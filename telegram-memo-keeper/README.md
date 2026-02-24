# MemoKeeper

Telegram Group Watcher — автоматически фиксирует договорённости, задачи и решения из групповых чатов.

## 🚀 Публикация и установка

### Для пользователей

```bash
# Установить с ClawHub
openclaw skills install telegram-memo-keeper

# Или из файла
openclaw skills install telegram-memo-keeper.skill
```

### Для разработчиков (CI/CD)

Автоматическая публикация на ClawHub при создании тега:

```bash
./setup-cicd.sh  # Настройка

# Публикация новой версии
git tag v1.1.0
git push origin v1.1.0
# GitHub Actions сделает всё автоматически!
```

Подробнее: [CI-CD.md](CI-CD.md)

## Локальная установка

```bash
./install.sh

```bash
# Создаём окружение
python -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

### 2. Настройка

```bash
cp .env.example .env
# Редактируем .env
nano .env
```

### 3. Запуск

**Polling mode** (development):
```bash
python scripts/bot.py
```

**Webhook mode** (production):
```bash
# Set WEBHOOK_URL in .env
export WEBHOOK_URL=https://your-domain.com
python scripts/webhook_server.py
```

Webhooks provide better stability for production with many users.

## Deploy (systemd)

```bash
sudo cp assets/systemd/memo-keeper.service /etc/systemd/system/
sudo systemctl enable memo-keeper
sudo systemctl start memo-keeper
```

## Команды бота

- `/mem_last [N]` — последние N записей
- `/mem_off` — отключить наблюдение
- `/mem_on` — включить наблюдение
- `/cost` — статистика расходов OpenAI API ($)

## Архитектура

```
Telegram Group → aiogram → Filter → Extractor (Rule-based + OpenAI) → Redis Stream → Memory Service
```

### OpenAI Integration

Enable smarter classification with OpenAI:

```bash
# Add to .env
OPENAI_API_KEY=sk-...
USE_OPENAI=true
OPENAI_MODEL=gpt-4o-mini
```

**Benefits:**
- Understands context and implicit tasks
- Better confidence scoring
- Handles sarcasm vs genuine decisions
- Extracts deadlines even without trigger words

**Cost:** ~$0.001-0.002 per message (GPT-4o-mini)

### Cost Tracking

Track OpenAI API usage and costs:

```bash
# Set budgets for alerts
export DAILY_BUDGET=1.0    # $1 per day
export WEEKLY_BUDGET=5.0   # $5 per week
export MONTHLY_BUDGET=20.0 # $20 per month
```

Command `/cost` shows:
- Daily/weekly/monthly spending
- Number of API calls
- Budget usage percentage
- 🚨 Alerts when >80% of budget

## Redis Events

### memory.added
```json
{
  "event_type": "memory.added",
  "memory_id": "mem_-100123_456_decision",
  "chat_id": -1001234567890,
  "content": "[Решение] Переходим на PostgreSQL",
  "content_type": "decision",
  "confidence": 0.85,
  "timestamp": 1704067200
}
```

### task.created
```json
{
  "event_type": "task.created",
  "task_id": "task_-100123_456",
  "title": "Обновить документацию",
  "priority": "high",
  "due_at": "2024-12-25"
}
```
