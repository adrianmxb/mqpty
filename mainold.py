#!/usr/bin/python3
# -*- coding: utf-8 -*-

#dieser ansatz funktioniert nicht, weil keystrokes von script nicht aufgefangen werden!
#um ne gute user experience zu gewährleisten müssen wir nen terminal emulieren mit PTY

import paho.mqtt.client as mqtt
import argparse
import os
import random
import string

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Strg+F8 to toggle the breakpoint.


def generate_on_connect(identifier):
    def on_connect(client, userdata, flags, rc):
        client.subscribe(identifier)
    return on_connect

def on_message(client, userdata, msg):
    pass

def connect(identifier):
    client = mqtt.Client()
    client.on_connect = generate_on_connect(identifier)
    client.on_message = on_message
    client.connect("mqtt.eclipse.org", 1883, 60)
    return client

def loop(client, identifier):
    client.loop_start()
    tmpfile = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    os.mkfifo("/tmp/%s" % tmpfile)
    print("please use script -f /tmp/%s" % tmpfile)
    with open("/tmp/%s" % tmpfile, encoding="utf-8") as fifo:
        for line in fifo:
            #print(repr(line))
            print(line, end="")
            client.publish(identifier, line)
    client.loop_stop()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", help="enter your name or another unique identifier for your session")
    args = parser.parse_args()
    client = connect(args.identifier)
    print_hi('PyCharm')
    loop(client, args.identifier)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
