# Hello World Example
# This is a simple example of the WS language

# Print a greeting
print "Hello, World!"

# Variable usage
set name "User"
print "Hello, $name!"

# Simple loop
set counter 1
while counter <= 5
    print "Counter: $counter"
    set counter counter + 1
end

# Basic function
function say_goodbye name
    print "Goodbye, $name!"
end

call say_goodbye "$name" 