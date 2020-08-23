import os
import subprocess
import paho.mqtt.client as mqtt
import select
import terminal
import sys
import time
from functools import partial
import json

class MqptySession:
    def __init__(self, identifier, argv, host="broker.hivemq.com", port=1883):
        self.__rowSize = 0
        self.__colSize = 0
        self.__history = []
        self.__identifier = identifier
        self.__host = host
        self.__port = port
        self.__stdinFd = sys.stdin.fileno()
        self.__stdoutFd = sys.stdout.fileno()
        self.__setupMqtt()
        self.__setupChildProcess(argv)

    def __setupMqtt(self):
        def on_connect(client, userdata, flags, rc, reason=None, properties=None):
            client.subscribe("%s/new" % self.__identifier)

        def on_message(client, userdata, msg):
            if msg.topic == "%s/new" % self.__identifier:
                self.__mqtt.publish("%s/resize" % self.__identifier, json.dumps({"colSize": self.__colSize, "rowSize": self.__rowSize}))
                for (data, currentTime, timeDelta) in self.__history:
                    jsonData = json.dumps({
                        "data": data,
                        "currentTime": currentTime,
                        "timeDelta": timeDelta}
                    )
                    client.publish("%s/data" % self.__identifier, jsonData)

        self.__mqtt = mqtt.Client()
        self.__mqtt.on_connect = on_connect
        self.__mqtt.on_message = on_message
        self.__mqtt.connect(self.__host, self.__port, 60)

    def __setupChildProcess(self, argv):
        pid, self.__childFd = terminal.Spawn(argv)

    def __onResizeEvent(self, rowSize, colSize):
        self.__mqtt.publish("%s/resize" % self.__identifier, json.dumps({"colSize": colSize, "rowSize": rowSize}))
        self.__rowSize = rowSize
        self.__colSize = colSize

    def __onStdinEvent(self, ev):
        if ev & select.POLLIN:
            terminal.CopyData(self.__stdinFd, self.__childFd)
        return True

    def __onChildEvent(self, ev):
        if ev & select.POLLHUP:
            msg = self.__mqtt.publish("%s/close" % self.__identifier)
            msg.wait_for_publish()
            return False

        if ev & select.POLLIN:
            data = terminal.CopyData(self.__childFd, self.__stdoutFd)
            data = data.decode("utf-8")
            timeDelta = 0.0
            currentTime = time.time()
            if len(self.__history) > 0:
                prevTime = self.__history[-1][1]
                timeDelta = currentTime - prevTime

            jsonData = json.dumps({
                "data": data,
                "currentTime": currentTime,
                "timeDelta": timeDelta}
            )

            self.__mqtt.publish("%s/data" % self.__identifier, jsonData)
            self.__history.append((data, currentTime, timeDelta))

        return True

    def wait(self, webserver=True, port=4242):
        print("~~~~~ SESSION LIVE. BE CAREFUL WHAT YOU TYPE IN HERE! ~~~~~")
        print("your mqpty identifier is %s, pass this code to the attendants of your meeting." % self.__identifier)
        if webserver:
            subprocess.Popen(["python3", "-m", "http.server", str(port), "--directory", "public"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            print("This instance is serving on localhost:%d" % port)

        print("~~~~~ SESSION LIVE. BE CAREFUL WHAT YOU TYPE IN HERE! ~~~~~")
        if os.isatty(self.__stdinFd):
            terminal.SetRaw(self.__stdinFd)
            terminal.LinkWindowSizes(self.__stdinFd, self.__childFd, partial(self.__onResizeEvent))

        self.__mqtt.loop_start()

        terminal.Wait({
            self.__stdinFd: partial(self.__onStdinEvent),
            self.__childFd: partial(self.__onChildEvent),
        })

        self.__mqtt.loop_stop()
