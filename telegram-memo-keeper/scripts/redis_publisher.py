"""
Redis Streams publisher for MemoKeeper.
Publishes memory.added and task.created events.
"""
import json
import redis
from typing import Optional
from dataclasses import asdict

from extractor import ExtractedItem, ContentType


class RedisPublisher:
    """Publishes events to Redis Streams."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, stream: str = "memory.events"):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.stream = stream
        self.dedup_set = "memo:processed"
    
    def is_processed(self, chat_id: int, message_id: int, content_type: str) -> bool:
        """Check if message was already processed (idempotency)."""
        key = f"mem:{chat_id}:{message_id}:{content_type}"
        return self.redis_client.sismember(self.dedup_set, key)
    
    def mark_processed(self, chat_id: int, message_id: int, content_type: str):
        """Mark message as processed."""
        key = f"mem:{chat_id}:{message_id}:{content_type}"
        self.redis_client.sadd(self.dedup_set, key)
        # Set TTL for cleanup (30 days)
        self.redis_client.expire(self.dedup_set, 30 * 24 * 3600)
    
    def publish_memory_added(
        self,
        item: ExtractedItem,
        chat_id: int,
        message_id: int,
        user_id: int,
        timestamp: float
    ) -> bool:
        """Publish memory.added event to Redis Stream."""
        # Check idempotency
        if self.is_processed(chat_id, message_id, item.content_type.value):
            return False
        
        event = {
            "event_type": "memory.added",
            "memory_id": f"mem_{chat_id}_{message_id}_{item.content_type.value}",
            "chat_id": chat_id,
            "user_id": user_id,
            "source_message_id": message_id,
            "content": item.content,
            "content_type": item.content_type.value,
            "confidence": item.confidence,
            "timestamp": timestamp,
            "tags": [item.content_type.value],
            "scope": "chat",
            "metadata": json.dumps(item.metadata),
        }
        
        # Add to stream
        self.redis_client.xadd(self.stream, event)
        
        # Mark as processed
        self.mark_processed(chat_id, message_id, item.content_type.value)
        
        return True
    
    def publish_task_created(
        self,
        item: ExtractedItem,
        chat_id: int,
        message_id: int,
        user_id: int,
        timestamp: float,
        assignee: Optional[int] = None
    ) -> bool:
        """Publish task.created event to Redis Stream."""
        task_id = f"task_{chat_id}_{message_id}"
        
        # Check idempotency
        if self.is_processed(chat_id, message_id, "task"):
            return False
        
        # Determine priority based on confidence and deadline
        priority = "medium"
        if item.confidence > 0.9:
            priority = "high"
        elif item.confidence < 0.6:
            priority = "low"
        
        event = {
            "event_type": "task.created",
            "task_id": task_id,
            "chat_id": chat_id,
            "user_id": user_id,
            "source_message_id": message_id,
            "title": item.content.replace("[Задача] ", "").replace("[Task] ", ""),
            "priority": priority,
            "due_at": item.metadata.get("deadline", ""),
            "assignee_user_id": assignee or "",
            "timestamp": timestamp,
            "confidence": item.confidence,
        }
        
        # Add to stream
        self.redis_client.xadd(self.stream, event)
        
        # Mark as processed
        self.mark_processed(chat_id, message_id, "task")
        
        return True
    
    def is_chat_enabled(self, chat_id: int) -> bool:
        """Check if monitoring is enabled for chat."""
        key = f"memo:chat:{chat_id}:enabled"
        enabled = self.redis_client.get(key)
        # Default: enabled if not set
        return enabled is None or enabled == "1"
    
    def set_chat_enabled(self, chat_id: int, enabled: bool):
        """Enable/disable monitoring for chat."""
        key = f"memo:chat:{chat_id}:enabled"
        self.redis_client.set(key, "1" if enabled else "0")
    
    def get_recent_memories(self, chat_id: int, count: int = 10) -> list:
        """Get recent memories for chat (for /mem_last command)."""
        # Read from stream
        pattern = f"mem_{chat_id}_*"
        # This is simplified - in production you'd query your memory service
        return []
