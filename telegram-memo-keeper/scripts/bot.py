"""
Main MemoKeeper bot using aiogram.
Monitors Telegram groups and extracts important info.
"""
import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

from config import Config
from filters import MessageFilter
from extractor import ContentType
from redis_publisher import RedisPublisher
from cost_tracker import CostTracker

# Import extractor based on OpenAI availability
try:
    from ai_classifier import HybridExtractor
    EXTRACTOR_CLASS = HybridExtractor
except ImportError:
    from extractor import ContentExtractor
    EXTRACTOR_CLASS = ContentExtractor


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


class MemoKeeperBot:
    """Telegram bot for extracting memories from group chats."""
    
    def __init__(self, config: Config):
        self.config = config
        self.bot = Bot(token=config.bot_token)
        self.dp = Dispatcher()
        self.config = config
        
        self.filter_engine = MessageFilter(max_length=config.max_message_length)
        
        # Initialize cost tracker
        self.cost_tracker = CostTracker(redis_client=None)  # Will use Redis from publisher
        
        # Set budgets if provided
        if hasattr(config, 'daily_budget') and config.daily_budget:
            self.cost_tracker.set_budgets(
                daily=config.daily_budget,
                weekly=getattr(config, 'weekly_budget', None),
                monthly=getattr(config, 'monthly_budget', None)
            )
        
        # Use hybrid extractor if OpenAI is enabled
        if config.use_openai and config.openai_api_key:
            from ai_classifier import HybridExtractor
            self.extractor = HybridExtractor(
                use_openai=True,
                openai_threshold=config.confidence_threshold,
                cost_tracker=self.cost_tracker
            )
            logger.info("Using HybridExtractor with OpenAI and cost tracking")
        else:
            from extractor import ContentExtractor
            self.extractor = ContentExtractor()
            logger.info("Using rule-based ContentExtractor")
        
        self.publisher = RedisPublisher(
            host=config.redis_host,
            port=config.redis_port,
            stream=config.redis_stream
        )
        
        # Connect cost tracker to same Redis
        self.cost_tracker.redis = self.publisher.redis_client
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message handlers."""
        # Commands
        self.dp.message.register(self.cmd_mem_last, Command("mem_last"))
        self.dp.message.register(self.cmd_mem_off, Command("mem_off"))
        self.dp.message.register(self.cmd_mem_on, Command("mem_on"))
        self.dp.message.register(self.cmd_cost, Command("cost"))
        
        # Group messages
        self.dp.message.register(
            self.handle_group_message,
            F.chat.type.in_(["group", "supergroup"]),
        )
    
    async def cmd_mem_last(self, message: Message):
        """Show last N memories for this chat."""
        if not message.text:
            return
        
        # Parse count
        parts = message.text.split()
        count = 5
        if len(parts) > 1:
            try:
                count = min(int(parts[1]), 20)  # Max 20
            except ValueError:
                pass
        
        # Get recent memories (placeholder - connect to your memory service)
        await message.reply(f"📋 Последние {count} записей (заглушка - подключить memory service)")
    
    async def cmd_mem_off(self, message: Message):
        """Disable monitoring for this chat."""
        chat_id = message.chat.id
        self.publisher.set_chat_enabled(chat_id, False)
        await message.reply("🔕 MemoKeeper отключён для этого чата. Используй /mem_on чтобы включить.")
        logger.info(f"Monitoring disabled for chat {chat_id}")
    
    async def cmd_mem_on(self, message: Message):
        """Enable monitoring for this chat."""
        chat_id = message.chat.id
        self.publisher.set_chat_enabled(chat_id, True)
        await message.reply("🔔 MemoKeeper включён для этого чата.")
        logger.info(f"Monitoring enabled for chat {chat_id}")

    async def cmd_cost(self, message: Message):
        """Show OpenAI API cost statistics."""
        stats = self.cost_tracker.get_current_period_stats()
        report = self.cost_tracker.format_report(stats)
        await message.reply(report, parse_mode=None)
    
    async def handle_group_message(self, message: Message):
        """Process incoming group message."""
        chat_id = message.chat.id
        
        # Check if we monitor this group
        if self.config.group_ids and chat_id not in self.config.group_ids:
            return
        
        # Check if monitoring is enabled
        if not self.publisher.is_chat_enabled(chat_id):
            return
        
        # Get message text
        text = message.text or message.caption
        if not text:
            return
        
        # Filter noise
        should_process, reason = self.filter_engine.should_process(text)
        if not should_process:
            logger.debug(f"Message {message.message_id} filtered: {reason}")
            return
        
        # Clean text
        clean_text = self.filter_engine.clean(text)
        
        # Extract content
        items = self.extractor.extract(clean_text)
        if not items:
            logger.debug(f"No content extracted from message {message.message_id}")
            return
        
        # Get timestamp
        timestamp = message.date.timestamp()
        user_id = message.from_user.id if message.from_user else 0
        
        # Publish to Redis
        published_count = 0
        for item in items:
            # Skip if confidence too low
            if item.confidence < self.config.confidence_threshold:
                continue
            
            if item.content_type == ContentType.TASK:
                # Publish as task
                success = self.publisher.publish_task_created(
                    item=item,
                    chat_id=chat_id,
                    message_id=message.message_id,
                    user_id=user_id,
                    timestamp=timestamp
                )
                if success:
                    published_count += 1
                    logger.info(f"Task created: {item.content[:50]}...")
            
            # Publish as memory (all types)
            success = self.publisher.publish_memory_added(
                item=item,
                chat_id=chat_id,
                message_id=message.message_id,
                user_id=user_id,
                timestamp=timestamp
            )
            if success:
                published_count += 1
                logger.info(f"Memory added: {item.content[:50]}...")
        
        if published_count > 0:
            logger.info(f"Message {message.message_id}: published {published_count} items")
    
    async def start(self):
        """Start the bot (polling mode)."""
        logger.info("Starting MemoKeeper bot...")
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping MemoKeeper bot...")
        await self.bot.session.close()


def main():
    """Main entry point."""
    config = Config.from_env()
    config.validate()
    
    bot = MemoKeeperBot(config)
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise


if __name__ == "__main__":
    main()
