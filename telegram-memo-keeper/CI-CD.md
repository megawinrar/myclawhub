# CI/CD настройка для автопубликации

## Что делает

При каждом push тега `v*` (например `v1.0.0`):
1. Пакует skill
2. Публикует на ClawHub
3. Создаёт GitHub Release с .skill файлом

## Настройка

### 1. Создай репозиторий на GitHub

```bash
cd telegram-memo-keeper
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/telegram-memo-keeper.git
git push -u origin main
```

### 2. Получи ClawHub Token

```bash
# На сервере выполни
clawhub login
# Или если есть браузер:
clawhub login --no-browser
```

Скопируй токен из вывода.

### 3. Добавь Secrets в GitHub

Зайди в репозиторий → Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value |
|-------------|-------|
| `CLAWHUB_TOKEN` | Твой токен из шага 2 |
| `GITHUB_TOKEN` | Создаётся автоматически, добавлять не нужно |

### 4. Проверка

Создай тег и запушь:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions автоматически:
- Запустит workflow
- Опубликует на ClawHub
- Создаст Release

### 5. Проверь публикацию

```bash
clawhub search telegram-memo-keeper
```

Или на сайте: https://clawhub.com/skills/telegram-memo-keeper

## Ручной запуск

Если нужно опубликовать без создания тега:

1. Go to Actions tab в GitHub
2. Выбери "Publish to ClawHub"
3. Click "Run workflow"

## Обновление версии

```bash
# Внеси изменения
git add .
git commit -m "v1.1.0: новая фича"
git push

# Создай новый тег
git tag v1.1.0
git push origin v1.1.0
```

CI/CD автоматически опубликует новую версию!
