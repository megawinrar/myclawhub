"""
Webhook server for MemoKeeper bot.
Production-ready aiohttp server.
"""
import asyncio
import logging
import sys
from contextlib import suppress

from aiohttp import web
from aiogram import Bot
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import Config
from bot import MemoKeeperBot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint for monitoring."""
    return web.json_response({
        "status": "ok",
        "service": "memo-keeper",
        "timestamp": asyncio.get_event_loop().time()
    })


async def stats(request: web.Request) -> web.Response:
    """Statistics endpoint."""
    bot: MemoKeeperBot = request.app["bot"]
    
    # Get stats from Redis
    processed_count = bot.publisher.redis_client.scard("memo:processed") or 0
    
    return web.json_response({
        "processed_messages": processed_count,
        "monitored_groups": len(bot.config.group_ids),
        "redis_connected": bot.publisher.redis_client.ping()
    })


async def on_startup(app: web.Application):
    """Setup on server start."""
    bot: MemoKeeperBot = app["bot"]
    config: Config = app["config"]
    
    # Set webhook
    webhook_url = f"{config.webhook_url}/webhook"
    await bot.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set: {webhook_url}")
    
    # Send startup notification (optional)
    if config.admin_chat_id:
        await bot.bot.send_message(
            config.admin_chat_id,
            "🚀 MemoKeeper webhook server started"
        )


async def on_shutdown(app: web.Application):
    """Cleanup on server stop."""
    bot: MemoKeeperBot = app["bot"]
    
    # Remove webhook
    await bot.bot.delete_webhook()
    logger.info("Webhook removed")
    
    # Close bot session
    await bot.stop()
    logger.info("Bot stopped")


def create_app(config: Config) -> web.Application:
    """Create aiohttp application."""
    # Create bot instance
    bot = MemoKeeperBot(config)
    
    # Create app
    app = web.Application()
    app["bot"] = bot
    app["config"] = config
    
    # Register routes
    app.router.add_get("/health", health_check)
    app.router.add_get("/stats", stats)
    
    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=bot.dp,
        bot=bot.bot
    )
    webhook_handler.register(app, path="/webhook")
    
    # Setup startup/shutdown
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app


def main():
    """Main entry point."""
    config = Config.from_env()
    config.validate()
    
    # Validate webhook URL
    if not config.webhook_url:
        logger.error("WEBHOOK_URL is required for webhook mode")
        sys.exit(1)
    
    app = create_app(config)
    
    # Run server
    logger.info(f"Starting webhook server on {config.host}:{config.port}")
    web.run_app(
        app,
        host=config.host,
        port=config.port,
        print=logger.info
    )


if __name__ == "__main__":
    main()
