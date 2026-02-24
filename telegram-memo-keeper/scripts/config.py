"""
Config for MemoKeeper bot.
Loads from environment variables.
"""
import os
from dataclasses import dataclass
from typing import List, Set


@dataclass
class Config:
    bot_token: str
    redis_host: str
    redis_port: int
    redis_stream: str
    group_ids: Set[int]
    confidence_threshold: float = 0.7
    max_message_length: int = 2000
    # Webhook settings
    webhook_url: str = ""  # https://your-domain.com
    host: str = "0.0.0.0"
    port: int = 8080
    admin_chat_id: int = 0  # For notifications
    # OpenAI settings
    openai_api_key: str = ""
    use_openai: bool = False
    openai_model: str = "gpt-4o-mini"
    # Budget settings
    daily_budget: float = 0.0
    weekly_budget: float = 0.0
    monthly_budget: float = 0.0
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables."""
        group_ids_str = os.getenv("GROUP_IDS", "")
        group_ids = set()
        if group_ids_str:
            group_ids = {int(gid.strip()) for gid in group_ids_str.split(",")}
        
        admin_id = os.getenv("ADMIN_CHAT_ID", "")
        
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_stream=os.getenv("REDIS_STREAM", "memory.events"),
            group_ids=group_ids,
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
            max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "2000")),
            webhook_url=os.getenv("WEBHOOK_URL", ""),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
            admin_chat_id=int(admin_id) if admin_id else 0,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            use_openai=os.getenv("USE_OPENAI", "false").lower() == "true",
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            daily_budget=float(os.getenv("DAILY_BUDGET", "0")),
            weekly_budget=float(os.getenv("WEEKLY_BUDGET", "0")),
            monthly_budget=float(os.getenv("MONTHLY_BUDGET", "0")),
        )
    
    def validate(self) -> bool:
        """Validate required fields."""
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not self.group_ids:
            raise ValueError("GROUP_IDS is required (comma-separated list)")
        return True
