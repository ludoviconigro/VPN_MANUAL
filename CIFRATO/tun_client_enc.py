#!/usr/bin/env python3
# tun_client_enc.py - versione cifrata del client

import os, fcntl, struct, socket, select, subprocess
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random

TUN_NAME = "tun0"
SERVER_IP = "IP_DEL_SERVER"   # IP reale del server
SERVER_PORT = 55555
SHARED_KEY_HEX = "INSERISCI_LA_TUA_CHIAVE_QUI"  # stessa del server

IFF_TUN = 0x0001
IFF_NO_PI = 0x1000
TUNSETIFF = 0x400454ca

box = SecretBox(bytes.fromhex(SHARED_KEY_HEX))

def create_tun(name=TUN_NAME):
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack('16sH', name.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun

def setup_ip():
    subprocess.run(["ip", "addr", "add", "10.20.0.2/24", "dev", TUN_NAME], check=True)
    subprocess.run(["ip", "link", "set", "dev", TUN_NAME, "up"], check=True)

def main():
    print("[*] Avvio client TUN cifrato -> UDP")
    tun = create_tun()
    setup_ip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = (SERVER_IP, SERVER_PORT)
    sock.sendto(b'hello', server)

    while True:
        r,w,x = select.select([tun, sock], [], [])
        if tun in r:
            pkt = os.read(tun, 2000)
            nonce = nacl_random(24)
            cipher = box.encrypt(pkt, nonce)
            sock.sendto(cipher, server)
        if sock in r:
            data, addr = sock.recvfrom(65535)
            try:
                plain = box.decrypt(data)
                os.write(tun, plain)
            except Exception as e:
                print(f"[!] Errore decrittazione da {addr}: {e}")

if __name__ == "__main__":
    main()
