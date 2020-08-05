#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pty
import sys
import os
import fcntl
import termios
import signal
import atexit
import tty
import select
import errno
import struct


def Spawn(argv):
    (pid, fd) = pty.fork()
    if pid == 0:
        try:
            os.execvp(argv[0], argv)
        except OSError as e:
            print(e)
            sys.exit(1)
    return pid, fd

def CopyData(frm, to):
    data = ''
    try:
        data = os.read(frm, 1024)
        os.write(to, data)
    except OSError:
        pass

    return data

def Wait(dispatchers):
    epoll = select.epoll()
    for fd in dispatchers.keys():
        epoll.register(fd, select.EPOLLIN)

    while True:
        try:
            for fd, ev in epoll.poll():
                dispatchers[fd](ev)
        except (IOError, select.error) as err:
            if err != errno.EINTR:
                raise

def SetRaw(fd):
    attr = termios.tcgetattr(fd)
    #restore state when the process dies so the terminal isnt messed up
    atexit.register(lambda: termios.tcsetattr(fd, termios.TCSAFLUSH, attr))
    tty.setraw(fd)


def LinkWindowSizes(master, slave, onResize):
    # TIOCGWINSZ -> IOC Get WINdow SiZe
    packedSize = fcntl.ioctl(master, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
    rows, cols, _, _ = struct.unpack("HHHH", packedSize)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, packedSize)
    signal.signal(signal.SIGWINCH, lambda s, f: LinkWindowSizes(master, slave, onResize))
    onResize(rows, cols)
