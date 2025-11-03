#!/usr/bin/env python3
# tun_client.py - educativo, NON cifrato

import os, fcntl, struct, socket, select, sys, subprocess

TUN_NAME = "tun0"
SERVER_IP = "IP_DEL_SERVER"   # es: 192.168.1.10
SERVER_PORT = 55555

IFF_TUN = 0x0001
IFF_NO_PI = 0x1000
TUNSETIFF = 0x400454ca

def create_tun(name=TUN_NAME):
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack('16sH', name.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun

def setup_ip():
    subprocess.run(["ip", "addr", "add", "10.20.0.2/24", "dev", TUN_NAME], check=True)
    subprocess.run(["ip", "link", "set", "dev", TUN_NAME, "up"], check=True)
    # aggiungi rotta default via tun se vuoi full-tunnel:
    # subprocess.run(["ip", "route", "add", "default", "dev", TUN_NAME], check=True)

def main():
    tun = create_tun()
    setup_ip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = (SERVER_IP, SERVER_PORT)

    # invia un pacchetto vuoto per "register" - opzionale
    sock.sendto(b'hello', server)

    while True:
        r,w,x = select.select([tun, sock], [], [])
        if tun in r:
            pkt = os.read(tun, 2000)
            sock.sendto(pkt, server)
        if sock in r:
            data, addr = sock.recvfrom(65535)
            os.write(tun, data)

if __name__ == "__main__":
    main()
