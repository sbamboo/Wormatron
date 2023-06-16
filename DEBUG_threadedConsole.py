import threading
import time
import shutil
import sys
import queue
import inspect
import os

parentpath = os.path.dirname( inspect.getabsfile(inspect.currentframe()) )

threadedConsoleInp = queue.Queue()
threadedConsoleOut = queue.Queue()

import platform
if platform.system() == 'Windows':
    import msvcrt
    def custom_input(prompt=''):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        characters = []
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch().decode('utf-8')
                if ord(char) == 13:
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    threadedConsoleInp.put(''.join(characters))
                    break
                characters.append(char)
                sys.stdout.write("\r" + prompt + ''.join(characters) + " " * (shutil.get_terminal_size().columns - len(prompt + ''.join(characters)) - 1))
                sys.stdout.flush()
else:
    import tty
    import termios
    def custom_input(prompt=''):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        characters = []
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                rows, columns = shutil.get_terminal_size()
                last_line = rows - 1
                sys.stdout.write("\033[{};0H".format(last_line + 1))
                sys.stdout.flush()
                char = sys.stdin.read(1)
                if ord(char) == 13:
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    threadedConsoleInp.put(''.join(characters))
                    break
                elif ord(char) == 127:  # Check for backspace (ASCII value 127)
                    if characters:
                        characters.pop()
                else:
                    characters.append(char)
                sys.stdout.write("\r" + prompt + ''.join(characters) + " " * (shutil.get_terminal_size().columns - len(prompt + ''.join(characters)) - 1))
                sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def read_input():
    if os.path.exists(f"{parentpath}{os.sep}threadedconsole.content"): os.remove(f"{parentpath}{os.sep}threadedconsole.content")
    while True:
        custom_input("> ")
        if not threadedConsoleInp.empty():
            content = threadedConsoleInp.get()
            open(f"{parentpath}{os.sep}threadedconsole.content","w").write(content)

def print_wrapper(*args, **kwargs):
    # Add the modified output to the queue
    threadedConsoleOut.put((args, kwargs))

# Start the input reading thread
input_thread = threading.Thread(target=read_input)
input_thread.daemon = True
input_thread.start()

# Start the output processing thread
def process_output():
    while True:
        if not threadedConsoleOut.empty():
            args, kwargs = threadedConsoleOut.get()
            print(*args, **kwargs)

output_thread = threading.Thread(target=process_output)
output_thread.daemon = True
output_thread.start()

# Start the main console
import os
os.system("python3 wormatron.py --debug")
