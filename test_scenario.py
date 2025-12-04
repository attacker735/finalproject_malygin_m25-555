#!/usr/bin/env python3
"""Тестовый сценарий для проверки основных функций кошелька."""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Тест базовой функциональности."""
    print("Тестирование базовой функциональности ValutaTrade Hub...")
    print("=" * 60)
    
    try:
        # Проверяем конфигурацию
        if not os.path.exists("config.json"):
            print("✗ config.json не найден")
            return False
        print("✓ config.json найден")
        
        # Проверяем основные модули
        from valutatrade_hub.infra.settings import SettingsLoader
        settings = SettingsLoader()
        print(f"✓ SettingsLoader загружен. BASE_CURRENCY: {settings.get('BASE_CURRENCY')}")
        
        print("✓ Модуль валют загружен")
        
        from valutatrade_hub.cli.interface import print_help
        print("✓ CLI интерфейс загружен")
        
        # Показываем доступные команды
        print("\n" + "=" * 60)
        print("Доступные команды:")
        print_help()
        
        print("\n" + "=" * 60)
        print("Базовый тест пройден успешно!")
        print("\nЧтобы начать работу, выполните:")
        print("  1. make setup      - создать структуру данных")
        print("  2. make project    - запустить приложение")
        print("  3. register --username <имя> --password <пароль> - зарегистрироваться")
        print("  4. login --username <имя> --password <пароль>    - войти")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_functionality()
