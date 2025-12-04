import shlex
from functools import wraps
from json import JSONDecodeError
from typing import Dict, List, Optional

import prompt
from prettytable import PrettyTable

from valutatrade_hub.core.currancies import getRegistryCurrencys
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    RateNotFoundError,
)
from ..core import usecase


def print_help():
    """Выводит красивое меню помощи с использованием PrettyTable"""
    table = PrettyTable()
    table.field_names = ["Команда", "Описание", "Пример"]
    table.align["Команда"] = "l"
    table.align["Описание"] = "l"
    table.align["Пример"] = "l"
    
    commands = [
        ("register --username <имя> --password <пароль>", 
         "Регистрация нового пользователя", 
         "register --username alex --password 1234"),
        
        ("login --username <имя> --password <пароль>", 
         "Вход в систему", 
         "login --username alex --password 1234"),
        
        ("show-portfolio [--base USD]", 
         "Показать текущий портфель", 
         "show-portfolio --base USD"),
        
        ("buy --currency <код> --amount <число>", 
         "Купить валюту", 
         "buy --currency BTC --amount 0.1"),
        
        ("sell --currency <код> --amount <число>", 
         "Продать валюту", 
         "sell --currency BTC --amount 0.1"),
        
        ("get-rate --from <код> --to <код>", 
         "Получить курс валюты", 
         "get-rate --from USD --to EUR"),
        
        ("update-rates [--source coingecko|exchangerate]", 
         "Обновить кэш курсов валют", 
         "update-rates --source coingecko"),
        
        ("show-rates [--currency <код>] [--top <число <=3>]", 
         "Показать актуальные курсы", 
         "show-rates --top 3"),
        
        ("help", "Показать это меню", "help"),
        ("exit", "Выйти из программы", "exit"),
    ]
    
    for cmd, desc, example in commands:
        table.add_row([cmd, desc, example])
    
    print("\n" + "═" * 90)
    print("💰 ВАЛЮТНЫЙ КОШЕЛЕК - СПРАВОЧНАЯ ИНФОРМАЦИЯ")
    print("═" * 90)
    print(table)
    print("═" * 90)
    print("💡 Подсказка: Используйте TAB для автодополнения команд")
    print("   Для подробной информации о команде: <команда> --help (в разработке)")
    print("═" * 90)


def print_welcome():
    """Выводит приветственное сообщение"""
    welcome_text = """
╔══════════════════════════════════════════════════════════════╗
║                    💰 ВАЛЮТНЫЙ КОШЕЛЕК 💰                    ║
║                                                              ║
║  Управляйте своими финансами в одном месте!                 ║
║  Торгуйте криптовалютой и фиатными валютами                 ║
║  с актуальными курсами в реальном времени.                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(welcome_text)


def print_goodbye():
    """Выводит прощальное сообщение"""
    goodbye_text = """
╔══════════════════════════════════════════════════════════════╗
║                    🏦 До новых встреч! 🏦                     ║
║                                                              ║
║  Ваш портфель сохранен.                                      ║
║  Возвращайтесь для новых финансовых операций!                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(goodbye_text)


def format_currency_list() -> str:
    """Форматирует список доступных валют"""
    currencies = getRegistryCurrencys().strip().split('\n')
    table = PrettyTable()
    table.field_names = ["Тип", "Код", "Название", "Доп. информация"]
    table.align = "l"
    
    for currency in currencies:
        if not currency:
            continue
        if "[FIAT]" in currency:
            parts = currency.replace("[FIAT] ", "").split(" — ")
            code_name = parts[0].split(" ")
            if len(code_name) >= 2:
                code = code_name[0]
                name = code_name[1]
                info = parts[1] if len(parts) > 1 else ""
                table.add_row(["🏛️ ФИАТ", code, name, info])
        elif "[CRYPTO]" in currency:
            parts = currency.replace("[CRYPTO] ", "").split(" — ")
            code_name = parts[0].split(" ")
            if len(code_name) >= 2:
                code = code_name[0]
                name = code_name[1]
                info = parts[1] if len(parts) > 1 else ""
                table.add_row(["🔗 КРИПТО", code, name, info])
    
    return str(table)


def get_arg(params: List[str], name: str, default=None) -> Optional[str]:
    """Вспомогательная функция для парсинга аргументов с улучшенной обработкой ошибок"""
    if name not in params:
        return default
    
    index = params.index(name)
    if index + 1 >= len(params):
        raise ValueError(f"🚫 Для параметра {name} не указано значение")
    
    value = params[index + 1]
    if value.startswith("--"):
        raise ValueError(f"🚫 Для параметра {name} нужно указать значение, а не другой флаг")
    
    return value


def cli_command(required_args: Optional[List[str]] = None, 
                optional_args: Optional[Dict[str, any]] = None):
    """
    Декоратор для CLI-команд с улучшенной обработкой.
    """
    required_args = required_args or []
    optional_args = optional_args or {}

    def decorator(fn):
        @wraps(fn)
        def wrapper(params: List[str]):
            try:
                # Парсим обязательные аргументы
                parsed_args = {}
                for arg in required_args:
                    value = get_arg(params, arg)
                    if value is None:
                        raise ValueError(f"🚫 Отсутствует обязательный параметр: {arg}")
                    parsed_args[arg.lstrip('-')] = value

                # Парсим опциональные аргументы
                for arg, default in optional_args.items():
                    value = get_arg(params, arg, default)
                    if value is not None:
                        parsed_args[arg.lstrip('-')] = value

                # Выполняем команду
                result = fn(**parsed_args)
                
                # Форматируем вывод
                if isinstance(result, str) and result.startswith("Пользователь"):
                    print(f"✅ {result}")
                elif isinstance(result, str) and result.startswith("Вы вошли"):
                    print(f"🔐 {result}")
                elif isinstance(result, str) and "ошибка" in result.lower():
                    print(f"❌ {result}")
                elif result:
                    print(result)
                    
                return result

            except JSONDecodeError as e:
                print(f"🚫 Ошибка формата данных: {e.msg} (строка {e.lineno})")
            except ValueError as e:
                print(f"🚫 {str(e)}")
            except InsufficientFundsError as e:
                print("💰 Недостаточно средств!")
                print(f"   Доступно: {e.available:.2f} {e.code}")
                print(f"   Требуется: {e.required:.2f} {e.code}")
            except RateNotFoundError as e:
                print(f"📊 Курс {e.code} не найден.")
                print("   Используйте 'update-rates' для обновления курсов.")
                print("\n📋 Доступные валюты:")
                print(format_currency_list())
            except CurrencyNotFoundError as e:
                print(f"🌍 Валюта '{e.code}' не найдена!")
                print("\n📋 Доступные валюты:")
                print(format_currency_list())
            except ApiRequestError as e:
                print(f"🌐 Ошибка соединения: {e.reason}")
                print("   Проверьте подключение к интернету или попробуйте позже.")
            except FileNotFoundError as e:
                print(f"📁 Файл не найден: {e.filename}")
                print("   Проверьте структуру данных или выполните 'setup'.")
            except Exception as e:
                print(f"⚠️  Неожиданная ошибка: {type(e).__name__}")
                print(f"   Сообщение: {str(e)}")

        return wrapper
    return decorator


def cli():
    """Основная функция CLI с улучшенным интерфейсом"""
    print_welcome()
    print_help()
    
    print("\n📋 Доступные валюты:")
    print(format_currency_list())
    print("\n" + "═" * 90)
    print("💬 Готов к работе! Введите команду или 'help' для справки.")
    print("═" * 90)

    while True:
        try:
            # Используем prompt с историей команд
            user_input = prompt.string("\n💻 Команда > ").strip()
            if not user_input:
                continue

            try:
                args = shlex.split(user_input, posix=False)
                cmd, *params = args
            except ValueError as e:
                print(f"🚫 Ошибка разбора команды: {e}")
                continue

            cmd = cmd.lower()
            
            # Обработка специальных команд
            if cmd == "exit":
                print_goodbye()
                break
            elif cmd == "help":
                print_help()
            elif cmd == "currencies" or cmd == "валюты":
                print("\n📋 Доступные валюты:")
                print(format_currency_list())
            elif cmd == "register":
                @cli_command(required_args=["--username", "--password"])
                def cmd_register(username, password):
                    return usecase.register(username, password)
                cmd_register(params)
            elif cmd == "login":
                @cli_command(required_args=["--username", "--password"])
                def cmd_login(username, password):
                    return usecase.login(username, password)
                cmd_login(params)
            elif cmd == "show-portfolio":
                @cli_command(optional_args={"--base": "USD"})
                def cmd_show_portfolio(base):
                    return usecase.show_portfolio(base)
                cmd_show_portfolio(params)
            elif cmd == "buy":
                @cli_command(required_args=["--currency", "--amount"])
                def cmd_buy(currency, amount):
                    try:
                        amount = float(amount)
                    except ValueError:
                        return "🚫 Ошибка: параметр --amount должен быть числом."
                    return usecase.buy(currency, amount)
                cmd_buy(params)
            elif cmd == "sell":
                @cli_command(required_args=["--currency", "--amount"])
                def cmd_sell(currency, amount):
                    try:
                        amount = float(amount)
                    except ValueError:
                        return "🚫 Ошибка: параметр --amount должен быть числом."
                    return usecase.sell(currency, amount)
                cmd_sell(params)
            elif cmd == "get-rate":
                @cli_command(required_args=["--from", "--to"])
                def cmd_get_rate(**kwargs):
                    return usecase.get_rate(kwargs["from"], kwargs["to"])
                cmd_get_rate(params)
            elif cmd == "update-rates":
                @cli_command(optional_args={"--source": None})
                def cmd_update_rates(source=None):
                    return usecase.update_rates(source)
                cmd_update_rates(params)
            elif cmd == "show-rates":
                @cli_command(optional_args={"--currency": None, "--top": None})
                def cmd_show_rates(currency=None, top=None):
                    try:
                        top_value = int(top) if top is not None else None
                    except ValueError:
                        return "🚫 Ошибка: параметр --top должен быть числом."
                    return usecase.show_rates(currency, top_value)
                cmd_show_rates(params)
            else:
                print(f"🚫 Неизвестная команда: '{cmd}'")
                print("   Введите 'help' для списка доступных команд.")

        except KeyboardInterrupt:
            print("\n\n⚠️  Прерывание... Для выхода введите 'exit'")
        except EOFError:
            print("\n\n🏁 Конец ввода. Для выхода введите 'exit'")
        except Exception as e:
            print(f"\n⚠️  Критическая ошибка: {type(e).__name__}")
            print(f"   Сообщение: {str(e)}")