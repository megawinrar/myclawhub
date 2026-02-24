"""
Noise filtering for Telegram messages.
Removes garbage before extraction.
"""
import re
from typing import Optional


# Messages to ignore completely
NOISE_PATTERNS = [
    r"^\s*[+✓✅✔️]\s*$",  # Just "+" or checkmark
    r"^\s*[оo][кkк]\s*$",  # Just "ок" or "ok"
    r"^\s*лол\s*$",  # Just "лол"
    r"^\s*ха+\s*$",  # "ха", "хааа"
    r"^\s*спасибо?\s*$",  # Just "спасибо"
    r"^\s*пожалуйста\s*$",
    r"^\s*👍+\s*$",  # Just thumbs up
    r"^\s*😂+\s*$",  # Just laughs
]

# Bot commands to ignore (unless important)
BOT_COMMANDS_IGNORE = [
    r"/status",
    r"/api",
    r"/tasks",
    r"/help",
    r"/start",
]

# Minimum meaningful message length
MIN_LENGTH = 10


class MessageFilter:
    """Filters noise from messages."""
    
    def __init__(self, max_length: int = 2000):
        self.max_length = max_length
        self.noise_regex = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]
        self.command_regex = [re.compile(p, re.IGNORECASE) for p in BOT_COMMANDS_IGNORE]
    
    def is_noise(self, text: str) -> bool:
        """Check if message is pure noise."""
        if not text or len(text.strip()) < MIN_LENGTH:
            return True
        
        # Check against noise patterns
        cleaned = text.strip().lower()
        for pattern in self.noise_regex:
            if pattern.match(cleaned):
                return True
        
        # Check if it's only ignored command
        for pattern in self.command_regex:
            if pattern.match(cleaned):
                return True
        
        return False
    
    def is_too_long(self, text: str) -> bool:
        """Check if message is too long for processing."""
        return len(text) > self.max_length
    
    def should_process(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Determine if message should be processed.
        Returns: (should_process, reason_if_not)
        """
        if not text:
            return False, "empty"
        
        if self.is_noise(text):
            return False, "noise"
        
        if self.is_too_long(text):
            return False, "too_long"
        
        return True, None
    
    def clean(self, text: str) -> str:
        """Clean message text for processing."""
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        # Remove mentions of @botname
        cleaned = re.sub(r"@\w+_bot\b", "", cleaned)
        return cleaned.strip()
