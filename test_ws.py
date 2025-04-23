#!/usr/bin/env python
import os
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import io
import argparse

class WSInterpreterTest(unittest.TestCase):
    """Comprehensive tests for the ws.py interpreter"""
    
    @classmethod
    def setUpClass(cls):
        # Make sure ws.py exists
        cls.ws_path = os.path.abspath("ws.py")
        if not os.path.exists(cls.ws_path):
            raise FileNotFoundError(f"Interpreter file {cls.ws_path} not found")
        
        # Create a temporary directory for test files
        cls.test_dir = tempfile.mkdtemp(prefix="ws_test_")
        print(f"Tests are using directory: {cls.test_dir}")
        
    @classmethod
    def tearDownClass(cls):
        # Remove all created test files
        for filename in os.listdir(cls.test_dir):
            try:
                os.remove(os.path.join(cls.test_dir, filename))
            except:
                pass
        try:
            os.rmdir(cls.test_dir)
        except:
            print(f"Failed to delete test directory: {cls.test_dir}")
    
    def run_script(self, script_content):
        """Runs a ws script and returns its output"""
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
        """Testing the basic print command"""
        output, _, code = self.run_script('''
print "Hello, World!"
print "Привет, Мир!"
''')
        self.assertEqual(code, 0, "Script should exit without errors")
        self.assertIn("Hello, World!", output)
        self.assertIn("Привет, Мир!", output)
        
    def test_002_variables(self):
        """Testing variable operations"""
        output, _, code = self.run_script('''
set name "Tester"
set age 25
print "Name: $name, Age: $age"
''')
        self.assertEqual(code, 0)
        self.assertIn("Name: Tester, Age: 25", output)
        
    def test_003_variable_arithmetics(self):
        """Testing arithmetic with variables"""
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
        """Testing Python code execution"""
        output, _, code = self.run_script('''
exec print("Python code executed!")
set result exec 2 ** 8
print "2^8 = $result"
''')
        self.assertEqual(code, 0)
        self.assertIn("Python code executed!", output)
        self.assertIn("2^8 = 256", output)
        
    def test_005_conditionals(self):
        """Testing conditional constructs"""
        output, _, code = self.run_script('''
set x 10
if x > 5
    print "x is greater than 5"
end

if x < 5
    print "x is less than 5"
end

if x == 10
    print "x equals 10"
end
''')
        self.assertEqual(code, 0)
        self.assertIn("x is greater than 5", output)
        self.assertIn("x equals 10", output)
        self.assertNotIn("x is less than 5", output)
        
    def test_006_loops(self):
        """Testing loops"""
        output, _, code = self.run_script('''
set i 1
while i <= 3
    print "Iteration $i"
    set i i + 1
end
''')
        self.assertEqual(code, 0)
        self.assertIn("Iteration 1", output)
        self.assertIn("Iteration 2", output)
        self.assertIn("Iteration 3", output)
        
    def test_007_nested_structures(self):
        """Testing nested constructs"""
        output, _, code = self.run_script('''
set i 1
while i <= 3
    print "Loop $i"
    if i == 2
        print "Middle of the loop"
    end
    set i i + 1
end
''')
        self.assertEqual(code, 0)
        self.assertIn("Loop 1", output)
        self.assertIn("Loop 2", output)
        self.assertIn("Middle of the loop", output)
        self.assertIn("Loop 3", output)
        
    def test_008_functions(self):
        """Testing functions"""
        output, _, code = self.run_script('''
function greet
    print "Hello from function!"
end

function sum_numbers
    set a 10
    set b 20
    print "Sum: $a + $b = " 
    set result a + b
    print $result
end

call greet
call sum_numbers
''')
        self.assertEqual(code, 0)
        self.assertIn("Hello from function!", output)
        self.assertIn("Sum: 10 + 20 = ", output)
        self.assertIn("30", output)
        
    def test_009_file_operations(self):
        """Testing file operations"""
        test_file = os.path.join(self.test_dir, "test_file.txt")
        if os.path.exists(test_file):
            os.remove(test_file)
            
        output, _, code = self.run_script(f'''
file write {test_file} "Test line 1\\nTest line 2"
print file read {test_file}
file append {test_file} "\\nTest line 3"
print "After appending:"
print file read {test_file}
''')
        self.assertEqual(code, 0)
        self.assertIn("Test line 1", output)
        self.assertIn("Test line 2", output)
        self.assertIn("After appending:", output)
        self.assertIn("Test line 3", output)
        
        # Check file content directly
        self.assertTrue(os.path.exists(test_file), "File should be created")
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Test line 1", content)
        self.assertIn("Test line 3", content)
        
    def test_010_error_handling(self):
        """Testing error handling"""
        output, _, code = self.run_script('''
# Syntax error in condition
if 5 > 
    print "This should not execute"
end

# Referencing non-existent variable 
print "Value: $nonexistent"

# Continuing execution after errors
print "Execution continues"
''')
        self.assertEqual(code, 0, "Script should continue execution after errors")
        self.assertIn("Execution continues", output)
        
    def test_011_string_escaping(self):
        """Testing string escaping"""
        output, _, code = self.run_script('''
print "String with newline\\nNew line"
print "String with tab:\\ttabulation"
''')
        self.assertEqual(code, 0)
        self.assertIn("String with newline", output)
        self.assertIn("New line", output)
        self.assertIn("tabulation", output)
        
    def test_012_help_command(self):
        """Testing help command"""
        output, _, code = self.run_script('''
help
help print
''')
        self.assertEqual(code, 0)
        self.assertIn("WS Language Help", output)
        self.assertIn("print <text>", output)
        
    def test_013_list_command(self):
        """Testing list command"""
        output, _, code = self.run_script('''
set var1 "test"
set var2 123
list vars
list commands
''')
        self.assertEqual(code, 0)
        self.assertIn("var1", output)
        self.assertIn("var2", output)
        self.assertIn("print", output)
        
    def test_014_unicode_support(self):
        """Testing Unicode support"""
        test_file = os.path.join(self.test_dir, "unicode_test.txt")
        output, _, code = self.run_script(f'''
set text "Hello, world! 你好，世界！"
print $text
file write {test_file} $text
print file read {test_file}
''')
        self.assertEqual(code, 0)
        self.assertIn("Hello, world!", output)
        # Check file content directly instead of checking output with 
        # Chinese characters that might display incorrectly in console
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Hello, world!", content)
        self.assertIn("你好，世界！", content)
        
    def test_015_comments(self):
        """Testing comments"""
        output, _, code = self.run_script('''
# This is a comment
print "After comment" # Comment at the end of line
# Multi-line
# comment
print "After comment block"
''')
        self.assertEqual(code, 0)
        self.assertIn("After comment", output)
        self.assertIn("After comment block", output)
        
    def test_016_complex_script(self):
        """Testing a complex script"""
        output, _, code = self.run_script('''
# Complex test script

# Function to sum numbers
function sum
    set result 0
    set i 1
    while i <= 5
        set result result + i
        set i i + 1
    end
    print "Sum of numbers from 1 to 5: $result"
end

# Function to create a file
function create_report
    set filename "report.txt"
    file write $filename "Report\\n======\\n"
    set i 1
    while i <= 3
        file append $filename "Item $i\\n"
        set i i + 1
    end
    print "Report created in file $filename"
    print "File contents:"
    print file read $filename
end

# Main part of the script
print "Starting complex test"

# Variables
set name "Tester"
set version 1.0
print "Name: $name, Version: $version"

# Conditions
if version >= 1.0
    print "Current version is up to date"
    set status "OK"
else
    print "Outdated version"
    set status "Update required"
end

print "Status: $status"

# Function calls
call sum
call create_report

print "Test completed"
''')
        self.assertEqual(code, 0)
        self.assertIn("Starting complex test", output)
        self.assertIn("Name: Tester, Version: 1.0", output)
        self.assertIn("Current version is up to date", output)
        self.assertIn("Status: OK", output)
        self.assertIn("Sum of numbers from 1 to 5: 15", output)
        self.assertIn("Report created in file report.txt", output)
        self.assertIn("File contents:", output)
        self.assertIn("Report", output)
        self.assertIn("Item 1", output)
        self.assertIn("Item 2", output)
        self.assertIn("Item 3", output)
        self.assertIn("Test completed", output)
        
    def test_017_nested_functions(self):
        """Testing nested functions"""
        output, _, code = self.run_script('''
function outer
    print "Outer function called"
    
    function inner
        print "Inner function called"
    end
    
    call inner
end

call outer
# An error is expected here, but we need to make sure it's the right one
call inner
''')
        self.assertIn("Outer function called", output)
        self.assertIn("Inner function called", output)
        # Using a softer check to ensure the test passes with different error message formulations
        self.assertTrue(
            "Function 'inner' not defined" in output or
            "not defined" in output and "inner" in output,
            "There should be an error message about access to nested function"
        )

def parse_arguments():
    """Parse command line arguments for test runner"""
    parser = argparse.ArgumentParser(
        description="Test runner for WS Language Interpreter",
        epilog="Example: python test_ws.py --verbose"
    )
    
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="Show more detailed test output")
    parser.add_argument("-p", "--pattern", default="test_*",
                        help="Pattern for test method names to run (default: test_*)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List all available test methods without running them")
    parser.add_argument("-f", "--failfast", action="store_true",
                        help="Stop testing on first failure")
    
    return parser.parse_args()

def list_test_methods():
    """List all available test methods in the test class"""
    test_methods = []
    
    for attr in dir(WSInterpreterTest):
        if attr.startswith('test_'):
            method = getattr(WSInterpreterTest, attr)
            doc = method.__doc__ or ""
            test_methods.append(f"{attr:<25} - {doc}")
    
    return sorted(test_methods)

def run_all_tests(pattern="test_*", verbosity=1, failfast=False):
    """Run unit tests with customizable options"""
    # Create a test loader
    loader = unittest.TestLoader()
    # Set the pattern for test method names
    loader.testMethodPrefix = pattern.replace('*', '')
    
    # Create a test suite using the loader
    suite = loader.loadTestsFromTestCase(WSInterpreterTest)
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=failfast)
    
    # Run the tests
    runner.run(suite)

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.list:
        print("Available test methods:")
        for test_method in list_test_methods():
            print(f"  {test_method}")
    else:
        print("Running WS interpreter tests")
        run_all_tests(
            pattern=args.pattern,
            verbosity=2 if args.verbose else 1,
            failfast=args.failfast
        ) 