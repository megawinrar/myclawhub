# Redis Event Schemas

## memory.added

Published when MemoKeeper extracts a fact worth remembering.

```json
{
  "event_type": "memory.added",
  "memory_id": "string (unique)",
  "chat_id": "integer",
  "user_id": "integer",
  "source_message_id": "integer",
  "content": "string (1-2 lines)",
  "content_type": "decision|task|deadline|link|context|requirement",
  "confidence": "float (0.0-1.0)",
  "timestamp": "float (unix timestamp)",
  "tags": ["array of strings"],
  "scope": "chat|user|project",
  "metadata": "json string"
}
```

## task.created

Published when a task is explicitly identified.

```json
{
  "event_type": "task.created",
  "task_id": "string (unique)",
  "chat_id": "integer",
  "user_id": "integer",
  "source_message_id": "integer",
  "title": "string",
  "priority": "high|medium|low",
  "due_at": "string (optional)",
  "assignee_user_id": "integer (optional)",
  "timestamp": "float",
  "confidence": "float"
}
```

## Reading from Stream

```python
import redis

r = redis.Redis()

# Read new events
messages = r.xread({"memory.events": "$"}, block=0)

# Read from beginning
messages = r.xread({"memory.events": "0"})

# Create consumer group
r.xgroup_create("memory.events", "workers", id="0", mkstream=True)

# Read as consumer
messages = r.xreadgroup(
    "workers", 
    "worker-1", 
    {"memory.events": ">"}, 
    count=10, 
    block=5000
)
```

## Idempotency Set

Redis SET `memo:processed` stores processed message keys.

Key format: `mem:{chat_id}:{message_id}:{type}`

TTL: 30 days (auto-cleanup)
