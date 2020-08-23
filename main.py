#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import secrets
from mqpty import MqptySession


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("please specify the terminal application you want to stream as parameter.")
        print("usage: python3 main.py [command]")
        print("example: python3 main.py bash")
        sys.exit(0)

    identifier = secrets.token_urlsafe(32)
    mqpty = MqptySession(identifier, sys.argv[1:])
    mqpty.wait()
