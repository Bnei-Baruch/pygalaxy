#!/usr/bin/env python
import os
import sys
from multiprocessing import Process, Queue
from socket import socket
from time import sleep, time, localtime

from bottle import run, route, request

script_name = os.path.basename(__file__)
script_name = script_name.split(".")[0]

log_path = 'logs'
if not os.path.exists(log_path):
    os.makedirs(log_path)


def first_zero(num, cnt=2):
    num = str(num)
    while len(num) < cnt:
        num = '0' + num
    return num


def tt_log():
    ttuple = localtime(time())
    return str(ttuple.tm_year) + first_zero(ttuple.tm_mon) + first_zero(ttuple.tm_mday) + "_" + first_zero(
        ttuple.tm_hour) + ":" + first_zero(ttuple.tm_min) + ":" + first_zero(ttuple.tm_sec)


sys.stdout = open(log_path + "/" + script_name + "_" + tt_log() + ".log", "w", 0)

global sock


def soccet_connect():
    global sock
    sock = socket()
    sock.connect(('localhost', 9090))
    sock.send('server#')


global q
q = Queue()


class myBottleClass:
    global q
    q = Queue()

    def __init__(self):
        print tt_log() + " myBottleClass created"

    @route('/title.php', method=['GET', 'OPTIONS'])
    def index():
        err = 0
        try:
            title = request.query.title
            port = request.query.port
        except:
            err = 1
            print "[myBottleClass][index] Unexpected exception in title and port getting:", sys.exc_info()[0]
            raise
        if err:
            return "Err"
        try:
            port = int(port)
        except:
            print tt_log() + " [myBottleClass] Broken port, must be integer"
            return "Err"
        print(tt_log() + " [myBottleClass] Recieve message for client " + str(port) + ": " + title)
        if title != "favicon.ico":
            print(tt_log() + " [myBottleClass] try put send title")
            q.put(str(port) + ':' + title)
            print(tt_log() + " [myBottleClass] message sended")
        return ("For client: " + str(port) + " sended title: " + title)

    def myBottleRun(self):
        run(host='0.0.0.0', port=8081)


global h
myBottlObject = myBottleClass()
h = Process(target=myBottlObject.myBottleRun)
h.start()

while 1:
    try:
        soccet_connect()
        print tt_log() + " Connected to soccet_gstreamer_server"
        break
    except:
        print tt_log() + " Can't connect to soccet_gstreamer_server, maybe it isn't run"
    sleep(3)

while 1:
    sleep(0.05)
    if not h.is_alive():
        print tt_log() + " [main_loop] Exception: Web Server Process is not alieve. Restart it."
        myBottlObject = myBottleClass()
        h = Process(target=myBottlObject.myBottleRun)
        h.start()

    try:
        txt = q.get(False)
        print tt_log() + " [main loop] get from Q: ", txt
        sock.send(txt + '#')
        print tt_log() + " [main loop] sended: " + txt + '#'
        replay = sock.recv(1024)
        if replay == '':
            print tt_log() + " [main loop] socket try to reconnect"
            while 1:
                try:
                    soccet_connect()
                    print tt_log() + " [main loop] socket reconnected"
                    sleep(3)
                    sock.send(txt + "#")
                    replay = sock.recv(1024)
                    print tt_log() + " [main loop] message sended: " + txt
                    break
                except:
                    print tt_log() + " [main loop] socket not reconnected"
                sleep(3)
        else:
            print tt_log() + " [main loop] message sended: " + txt
    except:
        pass
