#!/usr/bin/env python
# coding: utf-8


import os, sys, termios, tty

c, l = os.get_terminal_size()

def print_pause(x):
    x += "\x1b[10;10H"
    sys.stdout.buffer.write(x.encode())
    sys.stdout.buffer.flush()
    input()

print_pause(f"\x1b[2J\x1b[{l};{c}H4")
print_pause(f"\x1b[1;{c}H3")
print_pause(f"\x1b[{l};1H2")
print_pause(f"\x1b[1;1H1")
print_pause(f"\x1b[1;2H5" + ('\x0a'*l))
