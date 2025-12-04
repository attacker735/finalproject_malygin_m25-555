# ValutaTrade Hub - Интеллектуальный Валютный Кошелек
Консольное приложение для управления мультивалютным портфелем с поддержкой криптовалют и фиатных валют

🚀 Установка и запуск
Предварительные требования
bash
# Python 3.12 или выше
python3 --version

# Poetry (рекомендуется)
curl -sSL https://install.python-poetry.org | python3 -

# Или pip
pip install poetry
Клонирование и настройка
bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd finalproject_malygin_m25-555

# 2. Установить зависимости
make install

# 3. Настроить окружение
make setup

# 4. Настроить API ключи (опционально)
echo 'export EXCHANGERATE_API_KEY="ваш_ключ"' >> ~/.bashrc
Конфигурационные файлы
config.json — Основной конфиг приложения:

json
{
  "USERS_FILE": "users.json",
  "PORTFOLIOS_FILE": "portfolios.json", 
  "RATES_FILE": "rates.json",
  "BASE_CURRENCY": "USD",
  "RATES_TTL_SECONDS": 3600,
  "LOG_DIR": "logs",
  "LOG_FILE": "actions.log",
  "LOG_LEVEL": "INFO",
  "LOG_MAX_BYTES": 1000000,
  "LOG_BACKUP_COUNT": 3
}
parser_config.json — Конфиг парсеров:

json
{
  "EXCHANGERATE_API_KEY": "",
  "COINGECKO_URL": "https://api.coingecko.com/api/v3/simple/price",
  "EXCHANGERATE_API_URL": "https://v6.exchangerate-api.com/v6",
  "BASE_CURRENCY": "USD",
  "FIAT_CURRENCIES": ["EUR", "GBP", "RUB"],
  "CRYPTO_CURRENCIES": ["BTC", "ETH", "SOL"],
  "REQUEST_TIMEOUT": 10
}

🛠 Вспомогательные команды
Команда	Описание	Пример
help	Вывод полного справочника команд	help
exit	Безопасный выход из приложения	exit

⚙️ Конфигурация
Основные настройки
json
{
  "BASE_CURRENCY": "USD",               # Базовая валюта для расчетов
  "RATES_TTL_SECONDS": 3600,            # Время жизни кеша курсов (1 час)
  "LOG_LEVEL": "INFO",                  # Уровень детализации логов
  "DEFAULT_USER_BALANCE": 10000         # Начальный баланс новых пользователей
}
Настройка API ключей
bash
# Linux/Mac
export EXCHANGERATE_API_KEY="ваш_ключ_здесь"

# Windows (PowerShell)
$env:EXCHANGERATE_API_KEY="ваш_ключ_здесь"

# Windows (CMD)
set EXCHANGERATE_API_KEY=ваш_ключ_здесь

asciinema

https://asciinema.org/a/6QfRf0WkgOX2EOmawyAqV8bSm