#!/usr/bin/env python3
"""Финальный тест проекта для проверки всех требований."""

import os
import sys
import subprocess

def run_command(cmd):
    """Запуск команды и возврат результата."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_makefile_commands():
    """Тестирование всех команд Makefile."""
    print("Тестирование команд Makefile...")
    print("=" * 60)
    
    commands = [
        ("make install", "Установка зависимостей"),
        ("make lint", "Проверка кода"),
        ("make build", "Сборка пакета"),
    ]
    
    all_passed = True
    for cmd, description in commands:
        print(f"\n{description}: {cmd}")
        success, stdout, stderr = run_command(cmd)
        if success:
            print("✓ Успешно")
            if stdout:
                print(f"Вывод: {stdout[:200]}...")
        else:
            print("✗ Ошибка")
            if stderr:
                print(f"Ошибка: {stderr[:200]}")
            all_passed = False
    
    return all_passed

def test_project_structure():
    """Проверка структуры проекта."""
    print("\n\nПроверка структуры проекта...")
    print("=" * 60)
    
    required_dirs = ["valutatrade_hub", "data", "logs"]
    required_files = [
        "pyproject.toml",
        "Makefile",
        "config.json",
        "parser_config.json",
        "users.json",
        "portfolios.json",
        "data/rates.json",
        "valutatrade_hub/__init__.py",
        "valutatrade_hub/cli/interface.py",
        "valutatrade_hub/core/currancies.py",
        "valutatrade_hub/core/usecase.py",
    ]
    
    all_passed = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Директория {dir_name}/ существует")
        else:
            print(f"✗ Директория {dir_name}/ не найдена")
            all_passed = False
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✓ Файл {file_name} существует")
        else:
            print(f"✗ Файл {file_name} не найден")
            all_passed = False
    
    return all_passed

def test_poetry_config():
    """Проверка конфигурации Poetry."""
    print("\n\nПроверка конфигурации Poetry...")
    print("=" * 60)
    
    # Проверяем pyproject.toml
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r") as f:
            content = f.read()
            checks = [
                ("name = \"finalproject-malygin-m25-555\"", "Имя проекта"),
                ("version = \"0.1.0\"", "Версия"),
                ("packages =", "Определение пакетов"),
                ("project = \"valutatrade_hub.cli.interface:cli\"", "Точка входа"),
            ]
            
            all_passed = True
            for check, description in checks:
                if check in content:
                    print(f"✓ {description} настроен правильно")
                else:
                    print(f"✗ {description} не найден")
                    all_passed = False
            return all_passed
    else:
        print("✗ pyproject.toml не найден")
        return False

def main():
    """Основная функция тестирования."""
    print("ФИНАЛЬНЫЙ ТЕСТ ПРОЕКТА: Валютный кошелек")
    print("=" * 60)
    
    tests = [
        ("Структура проекта", test_project_structure),
        ("Конфигурация Poetry", test_poetry_config),
        ("Команды Makefile", test_makefile_commands),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"ТЕСТ: {test_name}")
        print('='*60)
        result = test_func()
        results.append((test_name, result))
    
    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ ПРОЙДЕН" if result else "✗ НЕ ПРОЙДЕН"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Проект готов к сдаче.")
    else:
        print("НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ.")
        print("Пожалуйста, исправьте ошибки перед сдачей.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
