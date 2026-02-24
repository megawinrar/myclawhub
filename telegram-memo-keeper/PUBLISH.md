# Публикация на GitHub и ClawHub

## 1. GitHub Репозиторий

```bash
# Создаём репозиторий
cd telegram-memo-keeper
git init
git add .
git commit -m "Initial release: Telegram MemoKeeper v1.0.0"

# Добавляем remote (замени username)
git remote add origin https://github.com/YOUR_USERNAME/telegram-memo-keeper.git
git push -u origin main

# Создаём релиз с .skill файлом
git tag v1.0.0
git push origin v1.0.0
```

На GitHub:
1. Go to Releases → Create a new release
2. Tag: v1.0.0
3. Upload `telegram-memo-keeper.skill` файл
4. Publish release

## 2. ClawHub (OpenClaw Registry)

```bash
# Устанавливаем clawhub CLI (если ещё нет)
npm install -g clawhub

# Логинимся (если нужно)
clawhub login

# Публикуем skill
clawhub publish telegram-memo-keeper.skill

# Или с тегами
clawhub publish telegram-memo-keeper.skill --tags telegram,bot,redis,memory
```

## 3. Установка пользователями

После публикации установка одной командой:

```bash
# Из ClawHub
openclaw skills install telegram-memo-keeper

# Из GitHub release
openclaw skills install https://github.com/YOUR_USERNAME/telegram-memo-keeper/releases/download/v1.0.0/telegram-memo-keeper.skill

# Локально
openclaw skills install ./telegram-memo-keeper.skill
```

## 4. Структура для ClawHub

```
telegram-memo-keeper/
├── SKILL.md              # ✓ Required - описание и триггеры
├── telegram-memo-keeper.skill  # ✓ Required - упакованный архив
├── README.md             # ✓ Документация
├── icon.png              # Иконка (опционально, 128x128)
└── LICENSE               # Лицензия
```

## 5. Обновление версии

```bash
# Меняем версию в SKILL.md
# Делаем изменения
git add .
git commit -m "v1.1.0: добавлена новая фича"
git tag v1.1.0
git push origin v1.1.0

# Переупаковываем
python ~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py .

# Публикуем новый релиз на GitHub
# Обновляем в ClawHub
clawhub publish telegram-memo-keeper.skill
```

## 6. Быстрая проверка

```bash
# Проверим что skill валидный
openclaw skills validate telegram-memo-keeper.skill

# Установим локально для теста
openclaw skills install telegram-memo-keeper.skill --local
```

## Готово! 🎉

Теперь MemoKeeper доступен для установки всем пользователям OpenClaw.
