#!/usr/bin/python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import os
import sys
import terminal
import select
import secrets
import subprocess

grows = -1
gcols = -1
history = []

def generate_on_connect(identifier):
    def on_connect(client, userdata, flags, rc, reason = None, properties = None):
        client.subscribe("%s/new" % identifier)
    return on_connect


def on_message(client, userdata, msg):
    if msg.topic == "%s/new" % identifier:
        global grows
        global gcols
        client.publish("%s/resize" % identifier, "%d|%d" % (gcols, grows))
        for data in history:
            client.publish("%s/data" % identifier, data)


def connect(identifier):
    client = mqtt.Client()
    client.on_connect = generate_on_connect(identifier)
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    return client


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    identifier = secrets.token_urlsafe(32)
    client = connect(identifier)
    print("~~~~~ SESSION LIVE. BE CAREFUL WHAT YOU TYPE IN HERE! ~~~~~")
    print("your mqpty identifier is %s, pass this code to the attendants of your meeting." % identifier)
    print("This server is serving on localhost:4242")
    print("~~~~~ SESSION LIVE. BE CAREFUL WHAT YOU TYPE IN HERE! ~~~~~")
    in_fd = sys.stdin.fileno()
    out_fd = sys.stdout.fileno()

    pid, child_fd = terminal.Spawn(sys.argv[1:])


    def OnStdin(ev):
        if ev & select.EPOLLIN:
            terminal.CopyData(in_fd, child_fd)


    def OnChild(ev):
        if ev & select.EPOLLIN:
            data = terminal.CopyData(child_fd, out_fd)
            client.publish("%s/data" % identifier, data)
            global history
            history.append(data)
        elif ev & select.EPOLLHUP:
            sys.exit(0)


    def OnResize(rows, cols):
        client.publish("%s/resize" % identifier, "%d|%d" % (cols, rows))
        global grows
        grows = rows
        global gcols
        gcols = cols


    if os.isatty(in_fd):
        terminal.SetRaw(in_fd)
        terminal.LinkWindowSizes(in_fd, child_fd, OnResize)

    subprocess.Popen(["python3", "-m", "http.server", "4242", "--directory", "public"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    client.loop_start()

    terminal.Wait({
        in_fd: OnStdin,
        child_fd: OnChild,
    })

    client.loop_stop()
    print("You successfully quit your mqpty session.")
