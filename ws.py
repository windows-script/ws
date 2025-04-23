#!/usr/bin/env python
import os
import sys
import re
import subprocess
import time
import glob
import argparse
from typing import Dict, List, Any, Union, Optional, Tuple, Set

VERSION = "1.0.0"

try:
    import pyautogui
except ImportError:
    print("Warning: pyautogui module not found. GUI automation commands will not work.")
    class PyAutoGuiFallback:
        def click(self, *args, **kwargs): print("Error: pyautogui not installed")
        def write(self, *args, **kwargs): print("Error: pyautogui not installed")
        def getWindowsWithTitle(self, *args): return []
    pyautogui = PyAutoGuiFallback()

try:
    import psutil
except ImportError:
    print("Warning: psutil module not found. Process commands will have limited functionality.")
    psutil = None

try:
    import winreg
except ImportError:
    try:
        import _winreg as winreg
    except ImportError:
        print("Warning: winreg module not found. Registry commands will not work.")
        winreg = None

class WSInterpreter:
    def __init__(self, debug=False):
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, List[str]] = {}
        self.function_scopes: Dict[str, Set[str]] = {}  
        self.current_function_scope = None
        self.debug = debug
        self.last_result = None
        self.commands = {
            'run': self.run_command,
            'exec': self.exec_python,
            'print': self.print_output,
            'wait': self.wait_time,
            'click': self.mouse_click,
            'type': self.keyboard_type,
            'window': self.window_operations,
            'registry': self.registry_operations,
            'process': self.process_operations,
            'file': self.file_operations,
            'if': self.conditional,
            'else': self.else_block,
            'while': self.while_loop,
            'function': self.define_function,
            'call': self.call_function,
            'set': self.set_variable,
            'get': self.get_variable,
            'list': self.list_command,
            'help': self.help_command,
        }
        self._in_else_block = False
        self._last_condition_result = False
        self._capture_output = True 

    def parse(self, code: str) -> List[Union[List[str], List[List[str]]]]:
        """Parse WS code into executable commands."""
        if not code.strip():
            return []
            
        lines = code.strip().split('\n')
        parsed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or line.startswith('#'):
                i += 1
                continue
    
            if any(line.startswith(cmd) for cmd in ['if', 'while', 'function', 'else']):
                block_type = line.split()[0]  
                block = [line]
                i += 1
                
                if block_type == 'else':
                    parsed_lines.append([block_type, block])
                    continue
                
                depth = 1
                
                while i < len(lines) and depth > 0:
                    current_line = lines[i].strip()
                    
       
                    if not current_line or current_line.startswith('#'):
                        i += 1
                        continue
                    
                    if current_line.startswith('end'):
                        depth -= 1
                    elif any(current_line.startswith(cmd) for cmd in ['if', 'while', 'function']):
                        depth += 1
                    
                    block.append(current_line)
                    i += 1
                    if depth == 0:
                        break
                        
         
                parsed_lines.append([block_type, block])
            else:
          
                comment_pos = line.find('#')
                if comment_pos > 0:
                    line = line[:comment_pos].strip()
                
                try:
                
                    tokens = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")++', line)
                    tokens = [token.strip('"') if token.startswith('"') and token.endswith('"') else token for token in tokens]
                    if tokens: 
                        parsed_lines.append(tokens)
                except Exception as e:
                    print(f"Error parsing line: {line}")
                    print(f"Error details: {str(e)}")
                
                i += 1
                
        return parsed_lines

    def execute(self, parsed_code: List[Union[List[str], List[List[str]]]]) -> Any:
        """Execute parsed WS code."""
        result = None
        
        for command in parsed_code:
            if not command:
                continue
            
            try:
                if len(command) >= 2 and command[0] in ['if', 'while', 'function', 'else']:
                    block_type = command[0]
                    block_content = command[1]
                    
                    if block_type == 'if':
                        result = self.conditional(block_content)
                    elif block_type == 'else':
                        result = self.else_block(block_content)
                    elif block_type == 'while':
                        result = self.while_loop(block_content)
                    elif block_type == 'function':
                        result = self.define_function(block_content)
                elif isinstance(command[0], str) and command[0] in self.commands:
                    if command[0] == 'print' and len(command) > 2 and command[1] == 'file' and command[2] == 'read':
                        file_path = command[3]
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                                self.print_output([content])
                                result = content
                        except Exception as e:
                            error_msg = f"Error reading file: {str(e)}"
                            print(error_msg)
                            result = error_msg
                    else:
                        result = self.commands[command[0]](command[1:])
                    
                    if command[0] == 'set' and len(command) > 2 and command[2] == 'exec':
                        var_name = command[1]
                        exec_result = result
                        self.variables[var_name] = exec_result
                else:
                    print(f"Unknown command: {command[0]}")
            except Exception as e:
                print(f"Error executing command {command}: {str(e)}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
        
        self.last_result = result
        return result

    def run_command(self, args: List[str]) -> str:
        """Run a Windows command."""
        if not args:
            return "Error: No command specified"
            
        cmd = ' '.join(args)
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0 and result.stderr:
                return f"Command error: {result.stderr}"
            return result.stdout
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def exec_python(self, args: List[str]) -> Any:
        """Execute Python code."""
        if not args:
            return "Error: No Python code specified"
            
        code = ' '.join(args)
        try:
            exec_globals = globals().copy()
            exec_globals.update(self.variables)
            result = eval(code, exec_globals)
            return result
        except Exception as e:
            try:
                exec_globals = globals().copy()
                exec_globals.update(self.variables)
                loc = {}
                exec(code, exec_globals, loc)
                self.variables.update(loc)
                return None
            except Exception as e2:
                return f"Error in Python code: {str(e2)}"

    def print_output(self, args: List[str]) -> str:
        """Print text to the console."""
        if not args:
            print() 
            return ""
            
        output = ' '.join(args)
        
        output = self._process_escape_sequences(output)
        
        output = self._replace_variables(output)
            
        try:
            print(output)
            return output  
        except UnicodeEncodeError:
            try:
                encoded = output.encode('cp866', errors='replace').decode('cp866')
                print(encoded)
                return output  
            except:
                encoded = output.encode('ascii', errors='replace').decode('ascii')
                print(encoded)
                return output  

    def wait_time(self, args: List[str]) -> None:
        """Wait for a specified number of seconds."""
        if not args:
            return "Error: No wait time specified"
            
        try:
            seconds = float(args[0])
            time.sleep(seconds)
        except ValueError:
            return f"Error: Invalid wait time: {args[0]}"
        except Exception as e:
            return f"Error during wait: {str(e)}"

    def mouse_click(self, args: List[str]) -> None:
        """Perform a mouse click."""
        try:
            if len(args) == 2:
                try:
                    x, y = int(args[0]), int(args[1])
                    pyautogui.click(x, y)
                except ValueError:
                    return f"Error: Invalid coordinates: {args[0]}, {args[1]}"
            else:
                pyautogui.click()
        except Exception as e:
            return f"Error during mouse click: {str(e)}"

    def keyboard_type(self, args: List[str]) -> None:
        """Type text using the keyboard."""
        if not args:
            return "Error: No text specified"
            
        text = ' '.join(args)
        
        text = self._process_escape_sequences(text)
        
        text = self._replace_variables(text)
        
        try:
            pyautogui.write(text)
        except Exception as e:
            return f"Error typing text: {str(e)}"

    def window_operations(self, args: List[str]) -> None:
        """Perform window operations."""
        if not args:
            return "Error: No window operation specified"
            
        operation = args[0]
        if operation == "focus" and len(args) > 1:
            window_name = ' '.join(args[1:])
            try:
                windows = pyautogui.getWindowsWithTitle(window_name)
                if windows:
                    windows[0].activate()
                else:
                    return f"Window '{window_name}' not found"
            except Exception as e:
                return f"Error focusing window: {str(e)}"
        elif operation == "close" and len(args) > 1:
            window_name = ' '.join(args[1:])
            try:
                windows = pyautogui.getWindowsWithTitle(window_name)
                if windows:
                    windows[0].close()
                else:
                    return f"Window '{window_name}' not found"
            except Exception as e:
                return f"Error closing window: {str(e)}"
        else:
            return f"Unknown window operation: {operation}"

    def registry_operations(self, args: List[str]) -> Any:
        """Perform registry operations."""
        if not winreg:
            return "Error: Registry operations not available (winreg module not found)"
            
        if not args:
            return "Error: No registry operation specified"
            
        operation = args[0]
        
        if operation == "read" and len(args) >= 3:
            hkey_str, key_path = args[1], args[2]
            value_name = args[3] if len(args) > 3 else ""
            
            try:
                hkey = getattr(winreg, hkey_str, winreg.HKEY_CURRENT_USER)
                with winreg.OpenKey(hkey, key_path) as key:
                    value, _ = winreg.QueryValueEx(key, value_name)
                    return value
            except Exception as e:
                return f"Registry read error: {str(e)}"
        
        elif operation == "write" and len(args) >= 4:
            hkey_str, key_path, value_name, value = args[1], args[2], args[3], args[4]
            
            try:
                hkey = getattr(winreg, hkey_str, winreg.HKEY_CURRENT_USER)
                with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
                    return f"Successfully wrote to registry: {key_path}\\{value_name}"
            except Exception as e:
                return f"Registry write error: {str(e)}"
        
        else:
            return f"Unknown registry operation: {operation}"

    def process_operations(self, args: List[str]) -> Any:
        """Perform process operations."""
        if not psutil:
            return "Error: Process operations limited (psutil module not found)"
            
        if not args:
            return "Error: No process operation specified"
            
        operation = args[0]
        
        if operation == "list":
            try:
                if psutil:
                    processes = []
                    for proc in psutil.process_iter(['pid', 'name']):
                        processes.append(f"{proc.info['pid']}: {proc.info['name']}")
                    return processes
                else:
                    if os.name == 'nt':
                        result = subprocess.run("tasklist", shell=True, capture_output=True, text=True)
                        return result.stdout.split('\n')
                    else:
                        result = subprocess.run("ps aux", shell=True, capture_output=True, text=True)
                        return result.stdout.split('\n')
            except Exception as e:
                return f"Error listing processes: {str(e)}"
        
        elif operation == "kill" and len(args) > 1:
            try:
                pid = int(args[1])
                if psutil:
                    process = psutil.Process(pid)
                    process.terminate()
                    return f"Process {pid} terminated"
                else:
                    if os.name == 'nt':
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    else:
                        subprocess.run(f"kill -9 {pid}", shell=True)
                    return f"Process {pid} termination requested"
            except ValueError:
                return f"Error: Invalid process ID: {args[1]}"
            except Exception as e:
                return f"Process kill error: {str(e)}"
        
        elif operation == "start" and len(args) > 1:
            program = ' '.join(args[1:])
            try:
                subprocess.Popen(program, shell=True)
                return f"Started: {program}"
            except Exception as e:
                return f"Process start error: {str(e)}"
        
        else:
            return f"Unknown process operation: {operation}"

    def file_operations(self, args: List[str]) -> Any:
        """Perform file operations."""
        if not args:
            return "Error: No file operation specified"
            
        operation = args[0]
        
        if operation == "read" and len(args) > 1:
            file_path = args[1]
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    return content
            except FileNotFoundError:
                return f"Error: File not found: {file_path}"
            except Exception as e:
                return f"File read error: {str(e)}"
        
        elif operation == "write" and len(args) > 2:
            file_path = args[1]
            content = ' '.join(args[2:])
            
            content = self._process_escape_sequences(content)
            content = self._replace_variables(content)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote to {file_path}"
            except Exception as e:
                return f"File write error: {str(e)}"
        
        elif operation == "append" and len(args) > 2:
            file_path = args[1]
            content = ' '.join(args[2:])
            
            content = self._process_escape_sequences(content)
            content = self._replace_variables(content)
            
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully appended to {file_path}"
            except Exception as e:
                return f"File append error: {str(e)}"
        
        elif operation == "delete" and len(args) > 1:
            file_path = args[1]
            try:
                os.remove(file_path)
                return f"Successfully deleted {file_path}"
            except FileNotFoundError:
                return f"Error: File not found: {file_path}"
            except Exception as e:
                return f"File delete error: {str(e)}"
        
        elif operation == "exists" and len(args) > 1:
            file_path = args[1]
            return os.path.exists(file_path)
        
        else:
            return f"Unknown file operation: {operation}"

    def conditional(self, block: List[str]) -> None:
        """Execute a conditional block."""
        if not block:
            return None
            
        first_line = block[0]
        if not first_line.startswith('if '):
            return f"Invalid if statement: {first_line}"
            
        condition = first_line[3:]  
        
        body = []
        else_block = []
        i = 1
        in_else = False
        
        while i < len(block):
            if block[i] == 'end':
                break
            elif block[i].startswith('else'):
                in_else = True
                i += 1
                continue
                
            if not in_else:
                body.append(block[i])
            else:
                else_block.append(block[i])
            i += 1
        
        try:
            exec_globals = globals().copy()
            exec_globals.update(self.variables)
            condition_met = eval(condition, exec_globals, self.variables)
            self._last_condition_result = condition_met
            
            if condition_met:
                result = self._execute_block_body(body)
                self._in_else_block = False
                return result
            else:
                if else_block:
                    result = self._execute_block_body(else_block)
                    return result
                self._in_else_block = True
                return None
        except Exception as e:
            self._last_condition_result = False
            return f"Error in condition: {str(e)}"

    def else_block(self, block: List[str]) -> Any:
        """Execute an else block."""
        if not self._in_else_block:
            return None  
            
        if not self._last_condition_result:
            body = []
            i = 1  
            while i < len(block) and block[i] != 'end':
                body.append(block[i])
                i += 1
                
            return self._execute_block_body(body)
        
        return None
        
    def while_loop(self, block: List[str]) -> Any:
        """Execute a while loop."""
        if not block:
            return None
            
        first_line = block[0]
        if not first_line.startswith('while '):
            return f"Invalid while statement: {first_line}"
            
        condition = first_line[6:]  
        
        body = block[1:-1] if block[-1] == 'end' else block[1:]
        
        try:
            max_iterations = 1000  
            iteration = 0
            last_result = None
            
            exec_globals = globals().copy()
            exec_globals.update(self.variables)
            
            while eval(condition, exec_globals, self.variables) and iteration < max_iterations:
                last_result = self._execute_block_body(body)
                iteration += 1
                
                
                exec_globals.update(self.variables)
                
            if iteration >= max_iterations:
                print("Warning: Maximum loop iterations reached (possible infinite loop)")
                
            return last_result
        except Exception as e:
            return f"Error in while loop: {str(e)}"

    def _process_escape_sequences(self, text: str) -> str:
        """Process escape sequences in strings."""
        if not text:
            return text
            
        return text.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")

    def _replace_variables(self, text: str) -> str:
        """Replace variable references in strings."""
        if not text:
            return text
            
        result = text
        for var_name, var_value in self.variables.items():
            result = result.replace(f"${var_name}", str(var_value))
        return result

    def _execute_block_body(self, body_lines: List[str]) -> Any:
        """Helper method to execute the body of a block."""
        parsed_body = []
        i = 0
        while i < len(body_lines):
            line = body_lines[i].strip()
            
            if not line or line.startswith('#'):
                i += 1
                continue
                
            if any(line.startswith(cmd) for cmd in ['if', 'while', 'function', 'else']):
                block_type = line.split()[0]
                nested_block = [line]
                i += 1
                depth = 1
                
                while i < len(body_lines) and depth > 0:
                    current_line = body_lines[i].strip()
                    if current_line.startswith('end'):
                        depth -= 1
                    elif any(current_line.startswith(cmd) for cmd in ['if', 'while', 'function']):
                        depth += 1
                    
                    nested_block.append(current_line)
                    i += 1
                    if depth == 0:
                        break
                        
                parsed_body.append([block_type, nested_block])
            else:
                try:
                    comment_pos = line.find('#')
                    if comment_pos > 0:
                        line = line[:comment_pos].strip()
                    
                    tokens = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")++', line)
                    tokens = [token.strip('"') if token.startswith('"') and token.endswith('"') else token for token in tokens]
                    if tokens: 
                        parsed_body.append(tokens)
                except:
                    print(f"Error parsing line in block: {line}")
                i += 1
        
        return self.execute(parsed_body)

    def define_function(self, block: List[str]) -> str:
        """Define a function."""
        if not block:
            return "Error: Empty function block"
            
        first_line = block[0]
        if not first_line.startswith('function '):
            return f"Invalid function definition: {first_line}"
            
        parts = first_line.split(maxsplit=1)
        if len(parts) < 2:
            return "Error: Function name not specified"
            
        func_name = parts[1]
        
        if self.current_function_scope:
            if self.function_scopes.get(self.current_function_scope) is None:
                self.function_scopes[self.current_function_scope] = set()
            self.function_scopes[self.current_function_scope].add(func_name)
        
        body = block[1:-1] if block[-1] == 'end' else block[1:]
        self.functions[func_name] = body
        
        return f"Function '{func_name}' defined"
        
    def call_function(self, args: List[str]) -> Any:
        """Call a defined function."""
        if not args:
            return "Error: No function name specified"
            
        func_name = args[0]
        
        if func_name not in self.functions:
            error_msg = f"Function '{func_name}' not defined"
            print(error_msg)
            return error_msg
        
        for parent_scope, nested_funcs in self.function_scopes.items():
            if func_name in nested_funcs:
                if self.current_function_scope != parent_scope:
                    error_msg = f"Function '{func_name}' not defined"
                    print(error_msg)
                    return error_msg
        
        previous_scope = self.current_function_scope
        
        self.current_function_scope = func_name
        
        result = self._execute_block_body(self.functions[func_name])
        
        self.current_function_scope = previous_scope
        
        return result

    def set_variable(self, args: List[str]) -> Any:
        """Set a variable value."""
        if len(args) < 2:
            return "Error: set requires variable name and value"
            
        var_name = args[0]
        value = ' '.join(args[1:])
        
        if value.startswith('exec '):
            exec_code = value[5:]  
            try:
                exec_globals = globals().copy()
                exec_globals.update(self.variables)
                result = eval(exec_code, exec_globals, self.variables)
                self.variables[var_name] = result
                return result
            except:
                try:
                    exec_globals = globals().copy()
                    exec_globals.update(self.variables)
                    loc = {}
                    exec(exec_code, exec_globals, loc)
                    if loc:  
                        self.variables[var_name] = next(iter(loc.values()))
                    return self.variables.get(var_name)
                except Exception as e:
                    print(f"Error in exec: {str(e)}")
                    self.variables[var_name] = f"Error: {str(e)}"
                    return None
        else:
            try:
                exec_globals = globals().copy()
                exec_globals.update(self.variables)
                evaluated_value = eval(value, exec_globals, self.variables)
                self.variables[var_name] = evaluated_value
            except:
                for existing_var, existing_val in self.variables.items():
                    value = value.replace(f"${existing_var}", str(existing_val))
                self.variables[var_name] = value
            return self.variables[var_name]

    def get_variable(self, args: List[str]) -> Any:
        """Get a variable value."""
        if not args:
            return "Error: No variable name specified"
            
        var_name = args[0]
        if var_name in self.variables:
            return self.variables[var_name]
        else:
            return f"Error: Variable '{var_name}' not defined"

    def list_command(self, args: List[str]) -> str:
        """List files, directories, variables, or functions."""
        if not args:
            return "Error: No list type specified"
            
        list_type = args[0]
        output = []
        
        if list_type == "files":
            pattern = args[1] if len(args) > 1 else "*"
            try:
                files = glob.glob(pattern)
                for file in files:
                    print(file)
                    output.append(file)
                return "\n".join(output)
            except Exception as e:
                error_msg = f"Error listing files: {str(e)}"
                print(error_msg)
                return error_msg
        
        elif list_type == "vars" or list_type == "variables":
            var_list = [f"{name} = {value}" for name, value in self.variables.items()]
            for var in var_list:
                print(var)
            return "\n".join(var_list)
        
        elif list_type == "funcs" or list_type == "functions":
            func_list = list(self.functions.keys())
            for func in func_list:
                print(func)
            return "\n".join(func_list)
        
        elif list_type == "commands":
            cmd_list = list(self.commands.keys())
            for cmd in cmd_list:
                print(cmd)
            return "\n".join(cmd_list)
        
        else:
            error_msg = f"Unknown list type: {list_type}"
            print(error_msg)
            return error_msg

    def help_command(self, args: List[str]) -> str:
        """Show help information."""
        help_text = ""
        
        if not args:
            help_text = """WS Language Help:
Available command categories:
- Basic: print, set, get, wait, help, list
- Windows: run, click, type, window
- Files: file read/write/append/delete
- Advanced: exec, registry, process
- Control: if, while, function, call

Use 'help <command>' for more information on a specific command."""
            print(help_text)
            return help_text
            
        command = args[0]
        
        if command == "print":
            help_text = "print <text> - Print text to console. Variables can be referenced with $varname."
        elif command == "set":
            help_text = "set <var_name> <value> - Set a variable. Can use 'set var exec code' to execute Python."
        elif command == "get":
            help_text = "get <var_name> - Get a variable's value."
        elif command == "wait":
            help_text = "wait <seconds> - Wait for the specified number of seconds."
        elif command == "run":
            help_text = "run <command> - Run a Windows command."
        elif command == "exec":
            help_text = "exec <python_code> - Execute Python code."
        elif command == "click":
            help_text = "click [x y] - Perform a mouse click, optionally at specified coordinates."
        elif command == "type":
            help_text = "type <text> - Type text using the keyboard."
        elif command == "window":
            help_text = "window focus/close <window_name> - Perform operations on windows."
        elif command == "file":
            help_text = "file read/write/append/delete <path> [content] - Perform file operations."
        elif command == "registry":
            help_text = "registry read/write <hkey> <path> <name> [value] - Perform registry operations."
        elif command == "process":
            help_text = "process list/kill/start [pid/program] - Perform process operations."
        elif command == "if":
            help_text = "if <condition>\n    commands...\nend - Conditional execution block."
        elif command == "else":
            help_text = "else\n    commands...\nend - Execute if previous condition was false."
        elif command == "while":
            help_text = "while <condition>\n    commands...\nend - Loop execution while condition is true."
        elif command == "function":
            help_text = "function <name>\n    commands...\nend - Define a function."
        elif command == "call":
            help_text = "call <function_name> - Call a defined function."
        elif command == "list":
            help_text = "list files/vars/funcs/commands [pattern] - List various elements."
        else:
            help_text = f"No help available for '{command}'."
            
        print(help_text)
        return help_text

def run_ws_file(file_path: str, debug=False) -> None:
    """Run a WS script file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            code = f.read()
            
        interpreter = WSInterpreter(debug=debug)
        parsed_code = interpreter.parse(code)
        interpreter.execute(parsed_code)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Error running WS file: {str(e)}")
        if debug:
            import traceback
            traceback.print_exc()

def run_ws_repl(debug=False) -> None:
    """Run the WS interactive REPL."""
    interpreter = WSInterpreter(debug=debug)
    print("WS Language Interpreter (Windows Scripting)")
    print("Type 'exit' to quit, 'help' for help")
    
    while True:
        try:
            line = input("ws> ")
            if line.lower() == 'exit':
                break
                
            parsed_line = interpreter.parse(line)
            result = interpreter.execute(parsed_line)
            
            if result is not None and not (isinstance(result, str) and not result):
                print(f"=> {result}")
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {str(e)}")
            if debug:
                import traceback
                traceback.print_exc()

def parse_arguments():
    """Parse command line arguments using argparse."""
    parser = argparse.ArgumentParser(
        description="WS Language Interpreter - A simple programming language for Windows automation.",
        epilog="Example: python ws.py script.ws --debug"
    )
    
    parser.add_argument("script", nargs="?", help="Path to the WS script file to execute")
    parser.add_argument("-v", "--version", action="version", version=f"WS Language Interpreter v{VERSION}",
                        help="Show version information and exit")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.script:
        run_ws_file(args.script, debug=args.debug)
    else:
        run_ws_repl(debug=args.debug) 
