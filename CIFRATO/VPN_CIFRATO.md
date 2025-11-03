Perfetto — ecco un **recap pronto-stampa** in stile README che puoi incollare su GitHub. Include **comandi passo-passo** per Kali (server) e Ubuntu (client), più test e opzioni.

---

# VPN didattica TUN + UDP (Python, PyNaCl)

Tunnel IP punto-punto con interfacce **TUN**, trasporto **UDP** e **cifratura AEAD** (XSalsa20-Poly1305 via PyNaCl).

## Topologia di esempio

| Ruolo  | OS     | IP reale (LAN)          | IP tunnel      |
| ------ | ------ | ----------------------- | -------------- |
| Server | Kali   | `192.168.254.134`       | `10.20.0.1/24` |
| Client | Ubuntu | `192.168.254.130` (es.) | `10.20.0.2/24` |

---

## Requisiti

* Python 3 su entrambi
* Modulo TUN attivo: `/dev/net/tun`
* Pacchetto PyNaCl installato via APT (scelta consigliata)

```bash
# Kali e Ubuntu
sudo apt update
sudo apt install -y python3 python3-nacl
# (opzionale) abilita modulo TUN se serve
sudo modprobe tun
```

---

## File del progetto

Posiziona questi due file nella stessa cartella su **entrambi** i nodi:

* `tun_server_enc.py` (server, Kali)
* `tun_client_enc.py` (client, Ubuntu)

> Nota: la riga che inviava `b'hello'` **deve essere rimossa** dal client (già fatto qui sotto).

### `tun_server_enc.py`

```python
#!/usr/bin/env python3
# Server TUN cifrato (AEAD)

import os, fcntl, struct, socket, select, subprocess
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random

TUN_NAME = "tun0"
SERVER_UDP_PORT = 55555
SHARED_KEY_HEX = "INSERISCI_LA_TUA_CHIAVE_QUI"  # stessa su client e server

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
    subprocess.run(["ip", "addr", "add", "10.20.0.1/24", "dev", TUN_NAME], check=True)
    subprocess.run(["ip", "link", "set", "dev", TUN_NAME, "up"], check=True)
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)

def main():
    print("[*] Avvio server TUN cifrato -> UDP")
    tun = create_tun()
    setup_ip()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", SERVER_UDP_PORT))
    print(f"[*] Ascolto UDP 0.0.0.0:{SERVER_UDP_PORT}")

    peers = set()
    while True:
        r,_,_ = select.select([tun, sock], [], [])
        if tun in r:
            pkt = os.read(tun, 2000)
            nonce = nacl_random(24)
            cipher = box.encrypt(pkt, nonce)
            for p in peers:
                sock.sendto(cipher, p)
        if sock in r:
            data, addr = sock.recvfrom(65535)
            if addr not in peers:
                print("[*] Nuovo peer:", addr)
                peers.add(addr)
            if len(data) < 24:
                # Ignora pacchetti non cifrati/di controllo
                continue
            try:
                plain = box.decrypt(data)
                os.write(tun, plain)
            except Exception as e:
                print(f"[!] Errore decrittazione da {addr}: {e}")

if __name__ == "__main__":
    main()
```

### `tun_client_enc.py`

```python
#!/usr/bin/env python3
# Client TUN cifrato (AEAD)

import os, fcntl, struct, socket, select, subprocess
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random

TUN_NAME = "tun0"
SERVER_IP = "192.168.254.134"   # IP LAN del server (Kali)
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

    while True:
        r,_,_ = select.select([tun, sock], [], [])
        if tun in r:
            pkt = os.read(tun, 2000)
            nonce = nacl_random(24)
            cipher = box.encrypt(pkt, nonce)
            sock.sendto(cipher, server)
        if sock in r:
            data, addr = sock.recvfrom(65535)
            if len(data) < 24:
                continue
            try:
                plain = box.decrypt(data)
                os.write(tun, plain)
            except Exception as e:
                print(f"[!] Errore decrittazione da {addr}: {e}")

if __name__ == "__main__":
    main()
```

---

## 1) Genera la chiave condivisa (sul server)

```bash
python3 - <<'EOF'
from nacl.utils import random
key = random(32)
print(key.hex())
EOF
```

Copia l’output esadecimale e incollalo in **entrambi** i file nel campo `SHARED_KEY_HEX`.

---

## 2) Avvio

### Server (Kali)

```bash
cd /percorso/del/progetto
sudo python3 tun_server_enc.py
# Atteso: "Ascolto UDP 0.0.0.0:55555"
```

### Client (Ubuntu)

```bash
cd /percorso/del/progetto
# (assicurati che SERVER_IP nel file sia 192.168.254.134)
sudo python3 tun_client_enc.py
```

---

## 3) Verifica

```bash
# dal client verso il server
ping -c 3 10.20.0.1

# dal server verso il client
ping -c 3 10.20.0.2

# vedere l'interfaccia TUN
ip addr show tun0
```

---

## (Opzionale) Usare il server come gateway Internet

**Sul server (Kali)** — abilita forwarding + NAT (sostituisci `eth0` con la tua NIC esterna):

```bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

**Sul client (Ubuntu)** — manda tutto nel tunnel:

```bash
sudo ip route add default dev tun0
# verifica IP pubblico visto da client
curl ifconfig.me
```

---

## Stop & pulizia

Interrompi con `CTRL+C`. Se servisse rimuovere l’interfaccia:

```bash
sudo ip link delete tun0
```

---

## Troubleshooting rapido

```bash
# vedere se /dev/net/tun esiste
ls -l /dev/net/tun || sudo modprobe tun

# controllare porta UDP
sudo tcpdump -n -i any udp port 55555

# errori di decrittazione -> chiave non uguale o pacchetti non cifrati
# MTU: se ci fosse frammentazione
sudo ip link set dev tun0 mtu 1400
```

---

## Note di sicurezza

Questo progetto è **didattico**. Mancano handshake automatico, anti-replay e rotazione chiavi. Per uso reale, preferisci **WireGuard**.

---

Se vuoi, ti preparo anche un `README.md` già formattato + i due file Python impacchettati (testati) così puoi pushare tutto nel repo in un colpo solo.
