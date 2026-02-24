---
name: telegram-memo-keeper
description: "Telegram Group Watcher bot that extracts decisions, tasks, deadlines and facts from group chat messages and publishes to Redis Streams. Use when: (1) need to monitor Telegram groups for important information, (2) extract tasks/decisions from conversations, (3) build memory systems from chat data, (4) integrate Telegram with centralized memory/task services via Redis."
---

# Telegram MemoKeeper

Bot/Service that watches Telegram groups, extracts important facts (decisions, tasks, deadlines), and publishes to Redis Streams.

## Core Workflow

### 1. Setup

**Prerequisites:**
- Python 3.9+
- Redis instance
- Telegram Bot Token (from @BotFather)

**Install:**
```bash
pip install aiogram redis python-dotenv
```

**Environment (.env):**
```
BOT_TOKEN=your_telegram_bot_token
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_STREAM=memory.events
GROUP_IDS=-1001234567890,-1009876543210  # comma-separated
```

### 2. Run

**Development (polling):**
```bash
python scripts/bot.py
```

**Production (webhook):**
```bash
python scripts/webhook_server.py
```

### 3. Architecture

**Message Flow:**
1. Telegram → aiogram → `bot.py`
2. Filter (noise removal)
3. Extract (classify content type)
4. Normalize (short 1-2 line summary)
5. Deduplicate (idempotency check)
6. Publish → Redis Stream

**Redis Events:**
- `memory.added` — facts for memory
- `task.created` — explicit tasks

## Content Types

| Type | Trigger Words | Example |
|------|--------------|---------|
| Decision | "решили", "принято", "будем", "договорились" | "Решили использовать PostgreSQL" |
| Task | "сделай", "надо", "задача", "todo" | "Надо обновить документацию" |
| Deadline | "к", "до", "дедлайн", "срок" | "К пятнице сделать деплой" |
| Link | URL, repo, doc link | "Вот репо: github.com/..." |
| Context | описание проекта | "Строим систему учёта задач" |
| Requirement | "требование", "правило", "нужно" | "Нужно поддерживать RTL" |

## Idempotency

All records use key: `mem:{chat_id}:{message_id}:{type}`

Check Redis SET `memo:processed` before processing.

## Commands

- `/mem_last [N]` — show last N memories for this chat
- `/mem_off` — disable watching (store flag in Redis)
- `/mem_on` — enable watching

## Testing

Run tests:
```bash
python -m pytest tests/ -v
```

Key test cases:
1. Filter noise ("ок", "+", "лол")
2. Extract decision from message
3. Idempotency (same message_id twice)
4. Task creation with deadline

## File Structure

```
scripts/
  bot.py              # Main entry, aiogram handlers
  webhook_server.py   # Production webhook server
  filters.py          # Noise filtering logic
  extractor.py        # Rule-based content extraction
  ai_classifier.py    # OpenAI-powered classification
  redis_publisher.py  # Redis Streams publisher
  config.py           # Settings & env
references/
  redis-schema.md     # Event schemas
  telegram-api.md     # aiogram patterns
```

## OpenAI Integration

Enable intelligent classification:

```bash
export OPENAI_API_KEY="sk-..."
export USE_OPENAI=true
```

The hybrid extractor uses:
1. **Rule-based** (fast, free) - for obvious patterns
2. **OpenAI** (smart, paid) - for complex context

OpenAI kicks in when rule-based confidence is low (< 0.8).

### Cost Tracking

Track API spending with budgets and alerts:

```bash
export DAILY_BUDGET=1.0
export WEEKLY_BUDGET=5.0
export MONTHLY_BUDGET=20.0
```

Use `/cost` command to see real-time spending statistics.

Pricing (per 1K tokens):
- gpt-4o-mini: $0.00015 input / $0.00060 output
- gpt-4o: $0.0025 input / $0.010 output

## Deployment

See `assets/systemd/memo-keeper.service` for systemd unit file.

## Notes

- MVP: text only, no embeddings
- Confidence threshold: 0.7 for auto-save, 0.5-0.7 for manual review
- Ignore bot commands unless explicitly marked
