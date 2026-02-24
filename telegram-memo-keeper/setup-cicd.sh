#!/bin/bash
# Setup script for CI/CD deployment

set -e

echo "🔧 Setting up CI/CD for Telegram MemoKeeper"
echo ""

# Check if git repo
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Run: git init"
    exit 1
fi

# Check remote
if ! git remote -v > /dev/null 2>&1; then
    echo "⚠️  No remote configured."
    echo "Add remote: git remote add origin https://github.com/USERNAME/telegram-memo-keeper.git"
    exit 1
fi

echo "✓ Git repository configured"
echo ""

# Check for ClawHub token
if [ -z "$CLAWHUB_TOKEN" ]; then
    echo "⚠️  CLAWHUB_TOKEN not set"
    echo ""
    echo "To get token:"
    echo "  1. Run: clawhub login"
    echo "  2. Copy the token"
    echo "  3. Export: export CLAWHUB_TOKEN=your_token"
    echo ""
    echo "Or add to ~/.bashrc:"
    echo "  echo 'export CLAWHUB_TOKEN=your_token' >> ~/.bashrc"
else
    echo "✓ CLAWHUB_TOKEN is set"
fi

echo ""
echo "📋 Next steps:"
echo "1. Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Ready for CI/CD'"
echo "   git push -u origin main"
echo ""
echo "2. Add CLAWHUB_TOKEN to GitHub Secrets:"
echo "   https://github.com/YOUR_USERNAME/telegram-memo-keeper/settings/secrets/actions"
echo ""
echo "3. Create first release:"
echo "   git tag v1.0.0"
echo "   git push origin v1.0.0"
echo ""
echo "4. Watch the magic happen at:"
echo "   https://github.com/YOUR_USERNAME/telegram-memo-keeper/actions"
