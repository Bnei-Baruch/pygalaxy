#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import select
import socket
import sys
from time import sleep, time, localtime

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


class smart_server:
    def __init__(self):
        self.maxqueue = 50
        self.host = ''
        self.port = 9090
        self.main_socket = socket.socket()
        self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.main_socket.bind((self.host, self.port))
        self.main_socket.listen(self.maxqueue)
        self.recieved_str_dict = {}
        self.recieved_messages_dict = {}
        self.gstreamers = {}
        self.servers = {}
        self.gstreamers_messages_dict = {}
        self.symbol = "#"

    def recieve_one(self, sock):
        try:

            if self.recieved_str_dict[`sock`].count(self.symbol) < 1:
                self.recieved_str_dict[`sock`] = self.recieved_str_dict[`sock`] + sock.recv(1024)
            if self.recieved_str_dict[`sock`].count(self.symbol) < 1:
                print tt_log() + " Error: no separate symbol in recieved message"
                return ""
            s_pos = self.recieved_str_dict[`sock`].find(self.symbol)
            rcv_message = self.recieved_str_dict[`sock`][:s_pos]
            self.recieved_str_dict[`sock`] = self.recieved_str_dict[`sock`][s_pos + 1:]
            return rcv_message
        except:
            print tt_log() + " Error: function recieve_one"
            return ""

    def recieve_message(self, sock):
        message = self.recieve_one(sock)
        print tt_log() + " Recieved message ::: ", message
        return message

    def send_message(self, sock, message):
        try:
            sock.send(message + self.symbol)
            return 1
        except:
            print tt_log() + " Error: function send_message"
            return 0

    def start(self):
        print tt_log() + ' ===> SockServer started'

        rsocks = []
        wsocks = []
        connected = []
        rsocks.append(self.main_socket)
        select_all_ok = 1
        while select_all_ok:
            sleep(0.05)
            try:
                reads, writes, errs = select.select(rsocks, wsocks, [])
            except:
                select_all_ok = 0

            for sock in reads:
                if sock == self.main_socket:
                    client, name = sock.accept()
                    rsocks.append(client)
                    self.recieved_str_dict[`client`] = ""
                    print tt_log() + " Connected new client, append socket"
                else:
                    message = self.recieve_message(sock)
                    if message == "":
                        print tt_log() + " Error message recieved, delete socket"
                        if `sock` in connected:
                            connected.remove(`sock`)
                            # need to erase sock from server
                            rsocks.remove(sock)
                            wsocks.remove(sock)
                    else:
                        if not `sock` in connected:
                            connected.append(`sock`)
                            print tt_log() + " Connected ::: ", message
                            wsocks.append(sock)
                            self.recieved_str_dict[`sock`] = ""
                            self.recieved_messages_dict[`sock`] = []
                            if message == "server":
                                self.servers[`sock`] = `sock`
                            else:
                                # client connect operations
                                port_list = message.split(',')
                                self.gstreamers[`sock`] = port_list
                                for port in port_list:
                                    self.gstreamers_messages_dict[port] = ''

                        else:
                            if self.servers.has_key(`sock`):
                                port = message[:message.find(':')]
                                self.gstreamers_messages_dict[port] = message
                                print tt_log() + " Server send message ::: ", message
                                sock.send('OK')

            for sock in writes:
                if self.gstreamers.has_key(`sock`):
                    for port in self.gstreamers[`sock`]:
                        if self.gstreamers_messages_dict.has_key(port):
                            if self.gstreamers_messages_dict[port] != '':
                                msg = self.gstreamers_messages_dict[port]
                                if self.send_message(sock, msg):
                                    print tt_log() + " Send message to client ::: ", msg
                                    self.gstreamers_messages_dict[port] = ''

        print tt_log() + ' ===> LogServer stopped [signal %s]'
        os.unlink(self.sockfile)


ss = smart_server()
ss.start()
