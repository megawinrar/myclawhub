#!/bin/bash
# Push Telegram MemoKeeper to your GitHub

echo "🚀 Подготовка к публикации на GitHub"
echo ""

# Проверяем git
if [ ! -d .git ]; then
    git init
    git add .
    git commit -m "Telegram MemoKeeper v1.0.0 - Group chat watcher with OpenAI"
    echo "✅ Git инициализирован"
else
    echo "✅ Git уже инициализирован"
fi

echo ""
echo "📋 Теперь выполни эти команды:"
echo ""
echo "1. Добавь remote (замени USERNAME на свой):"
echo "   git remote add origin https://github.com/YOUR_USERNAME/telegram-memo-keeper.git"
echo ""
echo "2. Проверь что всё ок:"
echo "   git remote -v"
echo ""
echo "3. Push на GitHub:"
echo "   git push -u origin main"
echo ""
echo "4. Создай тег и релиз:"
echo "   git tag v1.0.0"
echo "   git push origin v1.0.0"
echo ""
echo "5. Зайди на GitHub и создай Release с файлом telegram-memo-keeper.skill"
echo "   Файл находится здесь: $(pwd)/telegram-memo-keeper.skill"
echo ""
echo "💡 Или используй GitHub CLI:"
echo "   gh repo create telegram-memo-keeper --public --source=. --push"
echo "   gh release create v1.0.0 telegram-memo-keeper.skill --title 'v1.0.0' --notes 'Initial release'"
