# WS Language (Windows Scripting)

A simple yet powerful programming language for Windows automation and scripting, implemented in Python.

## Features

- Intuitive syntax for Windows automation tasks
- Variable management with string interpolation
- Control flow statements (if/else, while loops)
- Function definitions and calls
- File operations (read, write, append, delete)
- Process management (list, start, kill)
- Window operations (focus, close)
- Registry access (read, write)
- Mouse and keyboard control
- Direct Python code execution
- Interactive REPL mode

## Requirements

The basic interpreter requires Python 3.6+. For full functionality, install the following optional packages:
```
pip install pyautogui psutil
```

## Installation

Clone this repository or download the `ws.py` file to get started.

## Usage

Run a script:
```
python ws.py your_script.ws
```

Start the interactive REPL:
```
python ws.py
```

## Language Syntax

WS is a command-based language with straightforward syntax:

```
# This is a comment

# Variables
set name "John"
set age 30
print "Hello, $name! You are $age years old."

# Arithmetic operations
set x 5
set y 10
set z x + y
print "x + y = $z"

# Windows commands
run notepad.exe
wait 1
type "Hello from WS language!"
click 100 200

# Window operations
window focus "Notepad"
window close "Notepad"

# Registry operations
registry read HKEY_CURRENT_USER "Software\Microsoft\Windows\CurrentVersion\Run" "MyApp"
registry write HKEY_CURRENT_USER "Software\MyApp" "Version" "1.0.0"

# Process operations
process list
process kill 1234
process start notepad.exe

# File operations
file write test.txt "Hello, world!"
file read test.txt
file append test.txt "\nNew line"
file delete test.txt

# Control flow
set x 1
if x == 1
    print "x is 1"
else
    print "x is not 1"
end

set i 0
while i < 5
    print "i is $i"
    set i i + 1
end

# Functions
function greet name
    print "Hello, $name!"
end

call greet "World"

# Python execution
exec print("Hello from Python!")
```

## Command Reference

### Basic Commands
- `print <text>` - Print text to console (supports variable interpolation with $varname)
- `set <var_name> <value>` - Set a variable (supports arithmetic operations)
- `wait <seconds>` - Wait for the specified number of seconds
- `help` - Display available commands
- `list` - Display defined variables and functions

### Windows Control
- `run <command>` - Run a Windows command
- `exec <python_code>` - Execute Python code
- `click [x y]` - Perform a mouse click (at coordinates if provided)
- `type <text>` - Type text using the keyboard
- `sleep <seconds>` - Alias for wait

### Window Management
- `window focus <window_name>` - Focus a window
- `window close <window_name>` - Close a window

### Registry Operations
- `registry read <hkey> <key_path> <value_name>` - Read a registry value
- `registry write <hkey> <key_path> <value_name> <value>` - Write a registry value
- `registry delete <hkey> <key_path> <value_name>` - Delete a registry value

### Process Management
- `process list` - List running processes
- `process kill <pid>` - Kill a process by PID
- `process start <program>` - Start a program

### File Operations
- `file read <path>` - Read a file
- `file write <path> <content>` - Write to a file
- `file append <path> <content>` - Append to a file
- `file delete <path>` - Delete a file

### Control Flow
- `if <condition>` - Start conditional block
- `else` - Optional else block for conditionals
- `while <condition>` - Start a while loop
- `end` - End a control flow block or function definition

### Functions
- `function <name> [parameters...]` - Define a function
- `call <name> [arguments...]` - Call a defined function

## Testing

Run the test suite to verify interpreter functionality:
```
python test_ws.py
```

## Examples

See the `examples` directory for sample scripts that demonstrate WS language features.

## License

This project is released under the MIT License.

## Contributions

Contributions are welcome! Please feel free to submit a Pull Request. 
