# Windows Automation Example
# This example demonstrates various automation features of WS language

# Start Notepad
print "Starting Notepad..."
run notepad.exe
wait 1

# Focus on Notepad window
window focus "Notepad"
wait 0.5

# Type some text
print "Typing text..."
type "This text was typed by a WS language script!\n\n"
type "WS makes Windows automation easy.\n"
wait 1

# Save the file (Ctrl+S)
print "Saving file..."
exec import pyautogui; pyautogui.hotkey('ctrl', 's')
wait 1

# Type filename in save dialog
set filename "ws_automation_example.txt"
type "$filename"
wait 0.5
exec import pyautogui; pyautogui.press('enter')
wait 1

# Close Notepad
print "Closing Notepad..."
window close "Notepad"

# Read the saved file
print "Reading the saved file:"
file read "$filename"

# Delete the file
print "Cleaning up: deleting the file..."
file delete "$filename"

print "Automation demo completed!" 