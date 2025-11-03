#!/usr/bin/env python3
# tun_server.py - educativo, NON cifrato

import os, fcntl, struct, socket, select, sys, subprocess

TUN_NAME = "tun0"
SERVER_UDP_PORT = 55555

# constants
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000
TUNSETIFF = 0x400454ca

def create_tun(name=TUN_NAME):
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack('16sH', name.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun

def setup_ip():
    # assegna IP e porta down/up (modifica se vuoi)
    subprocess.run(["ip", "addr", "add", "10.20.0.1/24", "dev", TUN_NAME], check=True)
    subprocess.run(["ip", "link", "set", "dev", TUN_NAME, "up"], check=True)
    # abilita forwarding se vuoi routing ad internet:
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)

def main():
    print("[*] Avvio server TUN -> UDP")
    tun = create_tun()
    setup_ip()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", SERVER_UDP_PORT))
    print(f"[*] Ascolto UDP 0.0.0.0:{SERVER_UDP_PORT}")

    peers = set()
    while True:
        r,w,x = select.select([tun, sock], [], [])
        if tun in r:
            packet = os.read(tun, 2000)
            # invia a tutti i peer conosciuti
            for p in peers:
                sock.sendto(packet, p)
        if sock in r:
            data, addr = sock.recvfrom(65535)
            if addr not in peers:
                print("[*] Nuovo peer:", addr)
                peers.add(addr)
            os.write(tun, data)

if __name__ == "__main__":
    main()
