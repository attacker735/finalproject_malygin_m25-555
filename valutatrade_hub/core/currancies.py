from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class CurrencyType(Enum):
    FIAT = "fiat"
    CRYPTO = "crypto"


@dataclass
class CurrencyInfo:
    name: str
    code: str
    currency_type: CurrencyType
    issuing_country: Optional[str] = None
    algorithm: Optional[str] = None
    market_cap: Optional[float] = None


class BaseCurrency(ABC):
    
    def __init__(self, info: CurrencyInfo):
        self._validate_info(info)
        self.info = info
    
    def _validate_info(self, info: CurrencyInfo) -> None:
        if not info.name or not info.name.strip():
            raise ValueError("Название валюты не может быть пустым")
        
        if not info.code or not info.code.isupper():
            raise ValueError("Код валюты должен быть в верхнем регистре")
        
        if not (2 <= len(info.code) <= 5):
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        
        if " " in info.code:
            raise ValueError("Код валюты не должен содержать пробелов")
    
    @abstractmethod
    def display(self) -> str:
        pass
    
    @property
    def name(self) -> str:
        return self.info.name
    
    @property
    def code(self) -> str:
        return self.info.code
    
    @property
    def type(self) -> CurrencyType:
        return self.info.currency_type


class Fiat(BaseCurrency):
    
    def __init__(self, name: str, code: str, issuing_country: str):
        info = CurrencyInfo(
            name=name,
            code=code,
            currency_type=CurrencyType.FIAT,
            issuing_country=issuing_country
        )
        super().__init__(info)
        
        if not issuing_country or not issuing_country.strip():
            raise ValueError("Страна-эмитент не может быть пустой")
    
    def display(self) -> str:
        return f"🏛️  {self.code} ({self.name}) | Страна: {self.info.issuing_country}"


class Crypto(BaseCurrency):
    
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        info = CurrencyInfo(
            name=name,
            code=code,
            currency_type=CurrencyType.CRYPTO,
            algorithm=algorithm,
            market_cap=market_cap
        )
        super().__init__(info)
        
        if not algorithm or not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым")
        
        if market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
    
    def display(self) -> str:
        mcap = f"{self.info.market_cap:,.2f}" if self.info.market_cap else "N/A"
        return f"🔗 {self.code} ({self.name}) | Алгоритм: {self.info.algorithm} | Кап.: ${mcap}"


class CurrencyRegistry:
    
    _instance = None
    _currencies: Dict[str, BaseCurrency] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_registry()
        return cls._instance
    
    def _initialize_registry(self):
        # Фиатные валюты
        self.register(Fiat("Доллар США", "USD", "Соединенные Штаты"))
        self.register(Fiat("Евро", "EUR", "Европейский союз"))
        self.register(Fiat("Российский рубль", "RUB", "Россия"))
        self.register(Fiat("Британский фунт", "GBP", "Великобритания"))
        
        # Криптовалюты
        self.register(Crypto("Биткойн", "BTC", "SHA-256", 1_120_000_000_000))
        self.register(Crypto("Эфириум", "ETH", "Ethash", 390_000_000_000))
        self.register(Crypto("Солана", "SOL", "Proof of History", 10_000_000_000))
    
    def register(self, currency: BaseCurrency):
        self._currencies[currency.code] = currency
    
    def get(self, code: str) -> BaseCurrency:
        normalized_code = code.upper().strip()
        
        if normalized_code not in self._currencies:
            from .exceptions import CurrencyNotFoundError
            raise CurrencyNotFoundError(normalized_code)
        
        return self._currencies[normalized_code]
    
    def get_all(self) -> List[BaseCurrency]:
        return list(self._currencies.values())
    
    def get_by_type(self, currency_type: CurrencyType) -> List[BaseCurrency]:
        return [c for c in self._currencies.values() if c.type == currency_type]
    
    def list_all(self, include_type: bool = True) -> str:
        if not self._currencies:
            return "Реестр валют пуст"
        
        result = []
        result.append("=" * 60)
        result.append("📊 РЕЕСТР ДОСТУПНЫХ ВАЛЮТ")
        result.append("=" * 60)
        
        # Фиатные валюты
        fiat_currencies = self.get_by_type(CurrencyType.FIAT)
        if fiat_currencies:
            result.append("\n🏛️  ФИАТНЫЕ ВАЛЮТЫ:")
            for currency in sorted(fiat_currencies, key=lambda x: x.code):
                result.append(f"  • {currency.display()}")
        
        # Криптовалюты
        crypto_currencies = self.get_by_type(CurrencyType.CRYPTO)
        if crypto_currencies:
            result.append("\n🔗 КРИПТОВАЛЮТЫ:")
            for currency in sorted(crypto_currencies, key=lambda x: x.code):
                result.append(f"  • {currency.display()}")
        
        result.append("=" * 60)
        result.append(f"Всего валют: {len(self._currencies)}")
        
        return "\n".join(result)


# Глобальный экземпляр реестра
_registry = CurrencyRegistry()


# Функции для обратной совместимости
def get_currency(code: str) -> BaseCurrency:
    return _registry.get(code)


def getRegistryCurrencys() -> str:
    return _registry.list_all()


def list_currencies() -> str:
    return _registry.list_all()