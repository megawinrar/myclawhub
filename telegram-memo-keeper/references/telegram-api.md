# aiogram Patterns

## Installation

```bash
pip install aiogram
```

## Basic Bot Structure

```python
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hello!")

# Run
async def main():
    await dp.start_polling(bot)
```

## Filtering Group Messages

```python
from aiogram.enums import ChatType

@dp.message(F.chat.type == ChatType.SUPERGROUP)
async def handle_supergroup(message: Message):
    pass

# Or multiple types
@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def handle_group(message: Message):
    pass
```

## Getting Message Info

```python
@dp.message()
async def handle(message: Message):
    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id
    text = message.text
    timestamp = message.date  # datetime object
    
    # For forwarded messages
    if message.forward_from:
        original_user = message.forward_from.id
```

## Commands with Arguments

```python
@dp.message(Command("mem_last"))
async def cmd_mem_last(message: Message):
    # /mem_last 10
    args = message.text.split()
    count = int(args[1]) if len(args) > 1 else 5
```

## Reply to Messages

```python
await message.reply("This is a reply")

# Or answer in same chat
await message.answer("This is not a reply")
```

## Error Handling

```python
@dp.errors()
async def error_handler(event):
    logger.error(f"Error: {event.exception}")
    return True  # Suppress error
```

## Graceful Shutdown

```python
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
```

## Webhook Mode

```python
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

async def on_startup(bot: Bot):
    await bot.set_webhook("https://your-domain.com/webhook")

app = web.Application()
webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
webhook_handler.register(app, path="/webhook")
setup_application(app, dp, bot=bot)

web.run_app(app, host="0.0.0.0", port=8080)
```

## Useful Filters

```python
from aiogram import F

# Text contains
@dp.message(F.text.contains("hello"))

# Text starts with
@dp.message(F.text.startswith("/"))

# Has caption (for media)
@dp.message(F.caption)

# From specific user
@dp.message(F.from_user.id == 123456)

# Chat ID
@dp.message(F.chat.id == -100123456)
```
