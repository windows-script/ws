#!/usr/bin/env python
import os
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import io

class WSInterpreterTest(unittest.TestCase):
    """Всесторонние тесты для интерпретатора ws.py"""
    
    @classmethod
    def setUpClass(cls):
        # Убеждаемся, что ws.py существует
        cls.ws_path = os.path.abspath("ws.py")
        if not os.path.exists(cls.ws_path):
            raise FileNotFoundError(f"Файл интерпретатора {cls.ws_path} не найден")
        
        # Создаем временную директорию для тестовых файлов
        cls.test_dir = tempfile.mkdtemp(prefix="ws_test_")
        print(f"Тесты используют директорию: {cls.test_dir}")
        
    @classmethod
    def tearDownClass(cls):
        # Удаляем все созданные тестовые файлы
        for filename in os.listdir(cls.test_dir):
            try:
                os.remove(os.path.join(cls.test_dir, filename))
            except:
                pass
        try:
            os.rmdir(cls.test_dir)
        except:
            print(f"Не удалось удалить тестовую директорию: {cls.test_dir}")
    
    def run_script(self, script_content):
        """Запускает ws скрипт и возвращает его вывод"""
        script_path = os.path.join(self.test_dir, "test_script.ws")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        result = subprocess.run(
            [sys.executable, self.ws_path, script_path],
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    
    def test_001_basic_print(self):
        """Проверка базовой команды print"""
        output, _, code = self.run_script('''
print "Hello, World!"
print "Привет, Мир!"
''')
        self.assertEqual(code, 0, "Скрипт должен завершиться без ошибок")
        self.assertIn("Hello, World!", output)
        self.assertIn("Привет, Мир!", output)
        
    def test_002_variables(self):
        """Проверка работы с переменными"""
        output, _, code = self.run_script('''
set name "Tester"
set age 25
print "Имя: $name, Возраст: $age"
''')
        self.assertEqual(code, 0)
        self.assertIn("Имя: Tester, Возраст: 25", output)
        
    def test_003_variable_arithmetics(self):
        """Проверка арифметики с переменными"""
        output, _, code = self.run_script('''
set x 5
set y 10
set sum x + y
print "sum = $sum"
set product x * y
print "product = $product"
''')
        self.assertEqual(code, 0)
        self.assertIn("sum = 15", output)
        self.assertIn("product = 50", output)
        
    def test_004_python_exec(self):
        """Проверка выполнения Python кода"""
        output, _, code = self.run_script('''
exec print("Python code executed!")
set result exec 2 ** 8
print "2^8 = $result"
''')
        self.assertEqual(code, 0)
        self.assertIn("Python code executed!", output)
        self.assertIn("2^8 = 256", output)
        
    def test_005_conditionals(self):
        """Проверка условных конструкций"""
        output, _, code = self.run_script('''
set x 10
if x > 5
    print "x больше 5"
end

if x < 5
    print "x меньше 5"
end

if x == 10
    print "x равно 10"
end
''')
        self.assertEqual(code, 0)
        self.assertIn("x больше 5", output)
        self.assertIn("x равно 10", output)
        self.assertNotIn("x меньше 5", output)
        
    def test_006_loops(self):
        """Проверка циклов"""
        output, _, code = self.run_script('''
set i 1
while i <= 3
    print "Итерация $i"
    set i i + 1
end
''')
        self.assertEqual(code, 0)
        self.assertIn("Итерация 1", output)
        self.assertIn("Итерация 2", output)
        self.assertIn("Итерация 3", output)
        
    def test_007_nested_structures(self):
        """Проверка вложенных конструкций"""
        output, _, code = self.run_script('''
set i 1
while i <= 3
    print "Цикл $i"
    if i == 2
        print "Середина цикла"
    end
    set i i + 1
end
''')
        self.assertEqual(code, 0)
        self.assertIn("Цикл 1", output)
        self.assertIn("Цикл 2", output)
        self.assertIn("Середина цикла", output)
        self.assertIn("Цикл 3", output)
        
    def test_008_functions(self):
        """Проверка функций"""
        output, _, code = self.run_script('''
function greet
    print "Привет из функции!"
end

function sum_numbers
    set a 10
    set b 20
    print "Сумма: $a + $b = " 
    set result a + b
    print $result
end

call greet
call sum_numbers
''')
        self.assertEqual(code, 0)
        self.assertIn("Привет из функции!", output)
        self.assertIn("Сумма: 10 + 20 = ", output)
        self.assertIn("30", output)
        
    def test_009_file_operations(self):
        """Проверка операций с файлами"""
        test_file = os.path.join(self.test_dir, "test_file.txt")
        if os.path.exists(test_file):
            os.remove(test_file)
            
        output, _, code = self.run_script(f'''
file write {test_file} "Тестовая строка 1\\nТестовая строка 2"
print file read {test_file}
file append {test_file} "\\nТестовая строка 3"
print "После добавления:"
print file read {test_file}
''')
        self.assertEqual(code, 0)
        self.assertIn("Тестовая строка 1", output)
        self.assertIn("Тестовая строка 2", output)
        self.assertIn("После добавления:", output)
        self.assertIn("Тестовая строка 3", output)
        
        # Проверка содержимого файла напрямую
        self.assertTrue(os.path.exists(test_file), "Файл должен быть создан")
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Тестовая строка 1", content)
        self.assertIn("Тестовая строка 3", content)
        
    def test_010_error_handling(self):
        """Проверка обработки ошибок"""
        output, _, code = self.run_script('''
# Синтаксическая ошибка в условии
if 5 > 
    print "Это не должно выполниться"
end

# Обращение к несуществующей переменной 
print "Значение: $nonexistent"

# Продолжение выполнения после ошибок
print "Выполнение продолжается"
''')
        self.assertEqual(code, 0, "Скрипт должен продолжать выполнение после ошибок")
        self.assertIn("Выполнение продолжается", output)
        
    def test_011_string_escaping(self):
        """Проверка экранирования в строках"""
        output, _, code = self.run_script('''
print "Строка с переносом\\nНовая строка"
print "Строка с табуляцией:\\tтабуляция"
''')
        self.assertEqual(code, 0)
        self.assertIn("Строка с переносом", output)
        self.assertIn("Новая строка", output)
        self.assertIn("табуляция", output)
        
    def test_012_help_command(self):
        """Проверка команды help"""
        output, _, code = self.run_script('''
help
help print
''')
        self.assertEqual(code, 0)
        self.assertIn("WS Language Help", output)
        self.assertIn("print <text>", output)
        
    def test_013_list_command(self):
        """Проверка команды list"""
        output, _, code = self.run_script('''
set var1 "тест"
set var2 123
list vars
list commands
''')
        self.assertEqual(code, 0)
        self.assertIn("var1", output)
        self.assertIn("var2", output)
        self.assertIn("print", output)
        
    def test_014_unicode_support(self):
        """Проверка поддержки Unicode"""
        test_file = os.path.join(self.test_dir, "unicode_test.txt")
        output, _, code = self.run_script(f'''
set text "Привет, мир! 你好，世界！"
print $text
file write {test_file} $text
print file read {test_file}
''')
        self.assertEqual(code, 0)
        self.assertIn("Привет, мир!", output)
        # Проверка содержимого файла напрямую вместо проверки вывода с 
        # китайскими символами, которые могут неправильно отображаться в консоли
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Привет, мир!", content)
        self.assertIn("你好，世界！", content)
        
    def test_015_comments(self):
        """Проверка комментариев"""
        output, _, code = self.run_script('''
# Это комментарий
print "После комментария" # Комментарий в конце строки
# Многострочный
# комментарий
print "После блока комментариев"
''')
        self.assertEqual(code, 0)
        self.assertIn("После комментария", output)
        self.assertIn("После блока комментариев", output)
        
    def test_016_complex_script(self):
        """Проверка комплексного скрипта"""
        output, _, code = self.run_script('''
# Комплексный тестовый скрипт

# Функция для суммирования чисел
function sum
    set result 0
    set i 1
    while i <= 5
        set result result + i
        set i i + 1
    end
    print "Сумма чисел от 1 до 5: $result"
end

# Функция для создания файла
function create_report
    set filename "report.txt"
    file write $filename "Отчет\\n======\\n"
    set i 1
    while i <= 3
        file append $filename "Пункт $i\\n"
        set i i + 1
    end
    print "Отчет создан в файле $filename"
    print "Содержимое файла:"
    print file read $filename
end

# Главная часть скрипта
print "Запуск комплексного теста"

# Переменные
set name "Тестировщик"
set version 1.0
print "Имя: $name, Версия: $version"

# Условия
if version >= 1.0
    print "Актуальная версия"
    set status "OK"
else
    print "Устаревшая версия"
    set status "Обновите"
end

print "Статус: $status"

# Вызов функций
call sum
call create_report

print "Тест завершен"
''')
        self.assertEqual(code, 0)
        self.assertIn("Запуск комплексного теста", output)
        self.assertIn("Имя: Тестировщик, Версия: 1.0", output)
        self.assertIn("Актуальная версия", output)
        self.assertIn("Статус: OK", output)
        self.assertIn("Сумма чисел от 1 до 5: 15", output)
        self.assertIn("Отчет создан в файле report.txt", output)
        self.assertIn("Содержимое файла:", output)
        self.assertIn("Отчет", output)
        self.assertIn("Пункт 1", output)
        self.assertIn("Пункт 2", output)
        self.assertIn("Пункт 3", output)
        self.assertIn("Тест завершен", output)
        
    def test_017_nested_functions(self):
        """Проверка вложенных функций"""
        output, _, code = self.run_script('''
function outer
    print "Вызвана внешняя функция"
    
    function inner
        print "Вызвана внутренняя функция"
    end
    
    call inner
end

call outer
# Тут ожидается ошибка, но нам надо убедиться, что она правильная
call inner
''')
        self.assertIn("Вызвана внешняя функция", output)
        self.assertIn("Вызвана внутренняя функция", output)
        # Используем более мягкую проверку, чтобы тест проходил при разных формулировках
        # сообщения об ошибке
        self.assertTrue(
            "Function 'inner' not defined" in output or
            "not defined" in output and "inner" in output,
            "Должно быть сообщение об ошибке доступа к вложенной функции"
        )


def run_all_tests():
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    print("Запуск тестов интерпретатора WS")
    run_all_tests() 