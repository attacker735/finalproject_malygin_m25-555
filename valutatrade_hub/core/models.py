from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any
from copy import deepcopy

from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.infra.settings import SettingsLoader

from .utils import get_exchange_rate, load_json, save_json


@dataclass
class UserCredentials:
    """Данные для аутентификации пользователя."""
    user_id: int
    username: str
    hashed_password: str
    salt: str
    registration_date: str


class SecurityManager:
    """Менеджер безопасности для работы с паролями."""
    
    @staticmethod
    def generate_salt() -> str:
        """Генерирует соль для хеширования пароля."""
        timestamp = str(datetime.now().timestamp())
        return hashlib.sha256(timestamp.encode()).hexdigest()[:8]
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Хеширует пароль с солью."""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    @staticmethod
    def validate_password_strength(password: str) -> None:
        """Проверяет сложность пароля."""
        if len(password) < 4:
            raise ValueError("🔐 Пароль должен содержать минимум 4 символа")


class User:
    """Аккаунт пользователя системы."""
    
    def __init__(self, 
                 user_id: int, 
                 username: str, 
                 password: str,
                 salt: Optional[str] = None,
                 registration_date: Optional[datetime] = None):
        
        SecurityManager.validate_password_strength(password)
        
        self._user_id = user_id
        self._username = username.strip()
        self._salt = salt or SecurityManager.generate_salt()
        self._hashed_password = SecurityManager.hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.now()
        
        if not self._username:
            raise ValueError("👤 Имя пользователя не может быть пустым")
    
    @property
    def user_id(self) -> int:
        """Уникальный идентификатор пользователя."""
        return self._user_id
    
    @property
    def username(self) -> str:
        """Имя пользователя."""
        return self._username
    
    @username.setter
    def username(self, new_username: str):
        """Изменяет имя пользователя."""
        if not new_username.strip():
            raise ValueError("👤 Имя пользователя не может быть пустым")
        self._username = new_username.strip()
    
    @property
    def registration_date(self) -> datetime:
        """Дата регистрации."""
        return self._registration_date
    
    @property
    def hashed_password(self) -> str:
        """Хешированный пароль."""
        return self._hashed_password
    
    @property
    def salt(self) -> str:
        """Соль для хеширования пароля."""
        return self._salt
    
    @property
    def account_age_days(self) -> int:
        """Возраст аккаунта в днях."""
        return (datetime.now() - self._registration_date).days
    
    def verify_password(self, password: str) -> bool:
        """Проверяет правильность введённого пароля."""
        return self._hashed_password == SecurityManager.hash_password(password, self._salt)
    
    def change_password(self, new_password: str) -> None:
        """Изменяет пароль и пересчитывает хеш."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._salt = SecurityManager.generate_salt()
        self._hashed_password = SecurityManager.hash_password(new_password, self._salt)
    
    def get_user_info(self) -> Dict[str, Any]:
        """Возвращает информацию о пользователе."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }
    
    def __str__(self) -> str:
        return f"👤 Пользователь #{self.user_id}: {self.username}"


@dataclass
class WalletBalance:
    """Баланс кошелька."""
    currency: str
    amount: float = 0.0
    
    def __post_init__(self):
        self.currency = self.currency.upper()
        if self.amount < 0:
            raise ValueError("💰 Баланс не может быть отрицательным")
    
    def add(self, amount: float) -> None:
        """Пополнение баланса."""
        if amount <= 0:
            raise ValueError("💰 Сумма пополнения должна быть положительной")
        self.amount += amount
    
    def subtract(self, amount: float) -> None:
        """Снятие средств с баланса."""
        if amount <= 0:
            raise ValueError("💰 Сумма снятия должна быть положительной")
        if amount > self.amount:
            raise InsufficientFundsError(
                available=self.amount,
                required=amount,
                code=self.currency
            )
        self.amount -= amount


class Wallet:
    """Кошелек для хранения средств в определенной валюте."""
    
    def __init__(self, currency_code: str, balance: float = 0.0):
        if not isinstance(currency_code, str) or not currency_code:
            raise ValueError("💱 Код валюты должен быть непустой строкой")
        if not isinstance(balance, (int, float)) or balance < 0:
            raise ValueError("💰 Баланс должен быть числом не меньше 0")

        self.currency_code = currency_code.upper()
        self._balance = WalletBalance(currency=currency_code, amount=float(balance))
    
    @property
    def balance(self) -> float:
        """Текущий баланс."""
        return self._balance.amount
    
    @balance.setter
    def balance(self, value: float):
        """Установка баланса (с валидацией)."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("💰 Баланс не может быть отрицательным")
        self._balance.amount = float(value)
    
    def deposit(self, amount: float):
        """Пополняет баланс на указанную сумму."""
        if not isinstance(amount, (int, float)):
            raise TypeError("💰 Сумма пополнения должна быть числом")
        if amount <= 0:
            raise ValueError("💰 Сумма пополнения должна быть положительной")
        self._balance.add(amount)
    
    def withdraw(self, amount: float):
        """Снимает средства с баланса, если хватает средств."""
        if not isinstance(amount, (int, float)):
            raise TypeError("💰 Сумма снятия должна быть числом")
        if amount <= 0:
            raise ValueError("💰 Сумма снятия должна быть положительной")
        self._balance.subtract(amount)


class Portfolio:
    """Портфель пользователя, содержащий кошельки в разных валютах."""
    
    def __init__(self, user_id: int, wallets: Dict[str, Wallet]):
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("🆔 user_id должен быть положительным числом")

        self._user_id = user_id
        self._wallets = wallets or {}
    
    @property
    def user_id(self) -> int:
        """Идентификатор пользователя."""
        return self._user_id
    
    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return deepcopy(self._wallets)
    
    def add_currency(self, currency_code: str):
        """Добавляет новый кошелёк, если его ещё нет."""
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"💼 Кошелёк для валюты {code} уже существует")

        self._wallets[code] = Wallet(currency_code=code)
        return self._wallets[code]
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает объект Wallet по коду валюты."""
        code = currency_code.upper()
        wallet = self._wallets.get(code)
        if wallet is None:
            raise CurrencyNotFoundError(code)
        return wallet
    
    def get_total_value(self, base_currency: str = "USD") -> float:
        """Возвращает общую стоимость портфеля в выбранной базовой валюте."""
        base_currency = base_currency.upper()
        total_value_base = 0.0
        
        for code, wallet in self._wallets.items():
            if code == base_currency:
                total_value_base += wallet.balance
                continue
            
            try:
                rate, _ = get_exchange_rate(code, base_currency)
                total_value_base += wallet.balance * rate
            except (ValueError, CurrencyNotFoundError):
                # Если курс не найден, пропускаем эту валюту
                continue
        
        return round(total_value_base, 2)
    
    @staticmethod
    def load_portfolio(user_id: int) -> 'Portfolio':
        """Загружает портфель пользователя или создаёт новый."""
        portfolios = load_json(SettingsLoader().get("PORTFOLIOS_FILE"))
        
        data = next((d_ for d_ in portfolios if d_["user_id"] == user_id), None)
        
        if not data:
            return Portfolio(user_id, wallets={})
        
        wallets = {
            code: Wallet(currency_code=code, balance=float(info.get("balance", 0.0)))
            for code, info in data.get("wallets", {}).items()
        }
        return Portfolio(user_id, wallets=wallets)
    
    def save_portfolio(self):
        """Сохраняет портфель текущего пользователя."""
        portfolios = load_json(SettingsLoader().get("PORTFOLIOS_FILE"))
        
        for p in portfolios:
            if p["user_id"] == self.user_id:
                p["wallets"] = {
                    code: {"balance": w.balance}
                    for code, w in self._wallets.items()
                }
                break
        else:
            portfolios.append({
                "user_id": self.user_id,
                "wallets": {
                    code: {"balance": w.balance}
                    for code, w in self._wallets.items()
                }
            })
        
        save_json(SettingsLoader().get("PORTFOLIOS_FILE"), portfolios)
    
    def __str__(self) -> str:
        total_value = self.get_total_value()
        return (f"📊 Портфель #{self._user_id}: "
                f"{len(self._wallets)} валют, "
                f"Общая стоимость: {total_value:.2f} USD")

def create_initial_portfolio(user_id: int) -> Portfolio:
    """Создание начального портфеля для нового пользователя."""
    portfolio = Portfolio(user_id, wallets={})
    base_currency = SettingsLoader().get("BASE_CURRENCY", "USD")
    portfolio.add_currency(base_currency)
    return portfolio