#!/bin/bash
# Quick install script for Telegram MemoKeeper

set -e

echo "🚀 Installing Telegram MemoKeeper..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r scripts/requirements.txt

# Check Redis
echo "🔍 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is running"
else
    echo "⚠️  Redis not detected. Please install and start Redis:"
    echo "   sudo apt install redis-server"
    echo "   sudo systemctl start redis"
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your BOT_TOKEN and GROUP_IDS"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your settings"
echo "2. Get bot token from @BotFather"
echo "3. Add bot to your Telegram group"
echo "4. Run: python scripts/bot.py"
echo ""
echo "Or use systemd:"
echo "  sudo cp assets/systemd/memo-keeper.service /etc/systemd/system/"
echo "  sudo systemctl enable memo-keeper"
echo "  sudo systemctl start memo-keeper"
