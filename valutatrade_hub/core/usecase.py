from datetime import datetime
from prettytable import PrettyTable

from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import logger
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage

from . import utils as u
from .currancies import get_currency
from .exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    RateNotFoundError,
)
from .models import Portfolio, User

_current_user: User | None = None
_current_portfolio: Portfolio | None = None


def format_success_message(message: str) -> str:
    return f"✅ {message}"


def format_error_message(message: str) -> str:
    return f"❌ {message}"


def format_info_message(message: str) -> str:
    return f"ℹ️  {message}"


@log_action("REGISTER")
def register(username: str, password: str) -> str:
    """Создание нового пользователя"""
    users_file = SettingsLoader().get("USERS_FILE")
    users_data = u.load_json(users_file)

    if any(u["username"] == username for u in users_data):
        raise ValueError(f"Пользователь '{username}' уже существует")

    if len(password) < 4:
        raise ValueError("Пароль должен содержать минимум 4 символа")

    user_id = u.next_id(users_data)
    user = User(user_id=user_id, username=username, password=password)
    users_data.append(user.get_user_info())
    u.save_json(users_file, users_data)

    portfolios_file = SettingsLoader().get("PORTFOLIOS_FILE")
    portfolios = u.load_json(portfolios_file)
    portfolios.append({
        "user_id": user_id,
        "wallets": {f"{SettingsLoader().get('BASE_CURRENCY')}": {"balance": 0.0}},
    })
    u.save_json(portfolios_file, portfolios)

    return f"Пользователь '{username}' успешно зарегистрирован (ID: {user_id}). " \
           f"Для входа используйте: login --username {username} --password ****"


@log_action("LOGIN")
def login(username: str, password: str) -> str:
    """Вход пользователя и загрузка его портфеля."""
    global _current_user, _current_portfolio

    users_data = u.load_json(SettingsLoader().get("USERS_FILE"))
    user_entry = next((u_ for u_ in users_data if u_["username"] == username), None)
    if not user_entry:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = User(
        user_id=user_entry["user_id"],
        username=user_entry["username"],
        password=password,
        salt=user_entry["salt"],
        registration_date=datetime.fromisoformat(user_entry["registration_date"]),
    )

    if not user.verify_password(password):
        if user.hashed_password != user_entry["hashed_password"]:
            raise ValueError("Неверный пароль")

    _current_user = user
    _current_portfolio = Portfolio.load_portfolio(user.user_id)

    return f"Добро пожаловать, {username}! Вы успешно вошли в систему."


def show_portfolio(base: str = "USD") -> str:
    """Все кошельки и общая стоимость в базовой валюте."""
    if _current_user is None or _current_portfolio is None:
        raise ValueError("Сначала выполните вход в систему")

    base = base.upper()
    rates = u.load_json(SettingsLoader().get("RATES_FILE"))
    base_found = any(base in key.split("_") for key in rates.keys() if "_" in key)
    if not base_found:
        raise RateNotFoundError(base)

    wallets = _current_portfolio.wallets
    if not wallets:
        return format_info_message(f"Портфель пользователя '{_current_user.username}' пуст.")

    # Создаем таблицу для отображения портфеля
    table = PrettyTable()
    table.field_names = ["Валюта", "Баланс", f"В {base}", "Изменение"]
    table.align["Валюта"] = "l"
    table.align["Баланс"] = "r"
    table.align[f"В {base}"] = "r"
    table.align["Изменение"] = "r"
    
    total_value = 0.0

    for code, wallet in wallets.items():
        try:
            rate, _ = u.get_exchange_rate(code, base)
        except RateNotFoundError:
            table.add_row([code, f"{wallet.balance:.4f}", "N/A", "—"])
            continue
        except ApiRequestError as e:
            table.add_row([code, f"{wallet.balance:.4f}", f"Ошибка: {e}", "—"])
            continue
            
        converted = wallet.balance * rate
        total_value += converted
        table.add_row([code, f"{wallet.balance:.4f}", f"{converted:.2f} {base}", "→"])

    result = [
        f"📊 ПОРТФЕЛЬ: {_current_user.username}",
        f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"💱 Базовая валюта: {base}",
        "",
        str(table),
        "",
        f"{'─' * 40}",
        f"💰 ОБЩАЯ СТОИМОСТЬ: {total_value:.2f} {base}",
        f"{'─' * 40}"
    ]
    
    return "\n".join(result)


@log_action("BUY", verbose=True)
def buy(currency: str, amount: float) -> str:
    """Покупка валюты и увеличение баланса кошелька."""
    if _current_portfolio is None or _current_user is None:
        raise ValueError("Сначала выполните вход в систему")
    
    if amount <= 0:
        raise ValueError("Сумма покупки должна быть положительной")

    base_currency = SettingsLoader().get("BASE_CURRENCY")
    currency = currency.upper()
    
    if currency == base_currency:
        raise ValueError(f"Нельзя покупать базовую валюту {base_currency}")

    get_currency(currency)
    
    try:
        rate, _ = u.get_exchange_rate(currency, base_currency)
    except (CurrencyNotFoundError, ApiRequestError) as e:
        raise ApiRequestError(f"Не удалось получить курс для {currency}/{base_currency}: {e}")

    cost_in_base = amount * rate
    
    try:
        base_wallet = _current_portfolio.get_wallet(base_currency)
    except CurrencyNotFoundError:
        raise InsufficientFundsError(0.0, cost_in_base, base_currency)

    if base_wallet.balance < cost_in_base:
        raise InsufficientFundsError(base_wallet.balance, cost_in_base, base_currency)
    
    old_base_balance = base_wallet.balance
    base_wallet.withdraw(cost_in_base)

    try:
        wallet = _current_portfolio.get_wallet(currency)
    except CurrencyNotFoundError:
        wallet = _current_portfolio.add_currency(currency)

    old_balance = wallet.balance
    wallet.deposit(amount)
    _current_portfolio.save_portfolio()

    return (
        f"🎯 ОПЕРАЦИЯ: ПОКУПКА\n"
        f"{'─' * 40}\n"
        f"• Куплено: {amount:.4f} {currency}\n"
        f"• Курс: 1 {currency} = {rate:.4f} {base_currency}\n"
        f"• Стоимость: {cost_in_base:.2f} {base_currency}\n"
        f"{'─' * 40}\n"
        f"📈 ИЗМЕНЕНИЯ В ПОРТФЕЛЕ:\n"
        f"  {currency}: {old_balance:.4f} → {wallet.balance:.4f} (+{amount:.4f})\n"
        f"  {base_currency}: {old_base_balance:.2f} → {base_wallet.balance:.2f} (-{cost_in_base:.2f})\n"
        f"{'─' * 40}\n"
        f"✅ Покупка успешно выполнена!"
    )

def show_rates(currency: str = None, top: int = None) -> str:
    try:
        if currency is not None:
            currency = currency.upper()
            get_currency(currency)
    except CurrencyNotFoundError as e:
        logger.error(e)
        return f"ERROR: {e}"
    if top is not None and top < 0:
        logger.error("Параметр 'top' должен быть положительным числом")
        return "ERROR: Параметр 'top' должен быть положительным числом"

    base = ParserConfig().get("BASE_CURRENCY", "USD")
    storage = RatesStorage()
    rates = storage.load_rates()
    if not rates or "last_refresh" not in rates:
        msg = "Локальный кеш курсов пуст. " \
        "Выполните 'update-rates', чтобы загрузить данные."
        logger.warning(msg)
        return f"WARNING: {msg}"

    last_refresh = rates.get("last_refresh")
    filtered = []

    for pair, info in rates.items():
        if pair in ("source", "last_refresh"):
            continue

        from_curr, to_curr = pair.split("_")
        if currency and from_curr != currency:
            continue

        rate = info["rate"]
        if base != to_curr:
            try:
                if (key := f"{to_curr}_{base}") in rates:
                    base_rate = rates[key]["rate"], \
                        datetime.fromisoformat(rates[key]["updated_at"])
                if (rev := f"{base}_{to_curr}") in rates:
                    base_rate = 1 / rates[rev]["rate"], \
                        datetime.fromisoformat(rates[rev]["updated_at"])
                rate /= base_rate
                to_curr = base
            except Exception:
                continue

        filtered.append((f"{from_curr}_{to_curr}", rate, info["updated_at"]))

    if not filtered:
        msg = f"Курс для '{currency}' не найден в кеше." \
            if currency else "Нет доступных курсов."
        logger.info(msg)
        return f"INFO: {msg}"

    if top:
        filtered.sort(key=lambda x: x[1], reverse=True)
        filtered = filtered[:int(top)]
    else:
        filtered.sort(key=lambda x: x[0])

    table = PrettyTable()
    table.field_names = ["Валютная пара", "Курс", "Обновлено"]
    table.align["Курс"] = "r"

    for pair, rate, updated_at in filtered:
        table.add_row([pair, f"{rate:.6f}", updated_at.replace('T', ' ').split('+')[0]])

    table_str = f"Курсы из кэша "\
        f"(обновлены {last_refresh.replace('T', ' ').split('+')[0]}):\n{table}"
    return table_str
@log_action("UPDATE_RATES")
def update_rates(source: str | None = None) -> str:
    """
    Обновляет курсы валют через RatesUpdater.
    source: 'coingecko', 'exchangerate' или None (все источники)
    """
    try:
        print("🔄 Начало обновления курсов...")
        logger.info("Старт обновления курсов...")

        u.update_rates(source)

        storage = RatesStorage()
        rates = storage.load_rates()
        last_refr = rates.get("last_refresh", "unknown").replace('T', ' ').split('+')[0]
        total_updated = len([k for k in rates if k not in ("source", "last_refresh")])

        logger.info(f"Обновление курсов успешно. Всего обновлено: {total_updated}. "
                   f"Время последнего обновления: {last_refr}")
        
        return (f"✅ Обновление курсов успешно завершено!\n"
                f"📊 Обновлено курсов: {total_updated}\n"
                f"🕐 Время обновления: {last_refr}")

    except ApiRequestError as e:
        logger.error(f"Ошибка при обновлении курсов: {e}")
        return f"❌ Ошибка обновления курсов: {e}"


def get_rate(frm: str, to: str) -> str:
    """Возвращает текущий курс валют и обратный курс."""
    frm, to = frm.upper(), to.upper()

    try:
        get_currency(frm)
        get_currency(to)
    except CurrencyNotFoundError:
        raise

    try:
        rate, updated = u.get_exchange_rate(frm, to)
        inv = 1 / rate
    except Exception as e:
        raise ApiRequestError(str(e))

    return (
        f"💱 КУРС ВАЛЮТ\n"
        f"{'─' * 40}\n"
        f"• {frm} → {to}: {rate:.6f}\n"
        f"• {to} → {frm}: {inv:.6f}\n"
        f"{'─' * 40}\n"
        f"🕐 Обновлено: {updated.strftime('%Y-%m-%d %H:%M:%S')}"
    )
