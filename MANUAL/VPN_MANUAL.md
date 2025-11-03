# VPN TUN didattica (Kali ↔ Ubuntu)

## Topologia

* **Server (Kali)**: IP LAN `192.168.254.134`, IP TUN `10.20.0.1/24`
* **Client (Ubuntu)**: IP LAN `192.168.254.X`, IP TUN `10.20.0.2/24`
* **Trasporto**: UDP/55555 (non cifrato – solo per studio)

---

## 0) Prerequisiti (entrambi)

```bash
sudo apt update
sudo apt install -y python3 iproute2
# opzionale per cifratura in seguito
# pipx/pip3 install pynacl
```

Verifica/abilita TUN:

```bash
ls -l /dev/net/tun || sudo modprobe tun
```

Clona/entra nella cartella (esempio):

```bash
mkdir -p ~/Desktop/PROJ\ VPN/MANUALE
cd ~/Desktop/PROJ\ VPN/MANUALE
# copia qui i file tun_server.py e tun_client.py
chmod +x tun_server.py tun_client.py
```

---

## 1) Server (Kali)

Avvia server:

```bash
cd ~/Desktop/PROJ\ VPN/MANUALE
sudo ./tun_server.py
```

Output atteso:

```
[*] Avvio server TUN -> UDP
[*] Ascolto UDP 0.0.0.0:55555
```

---

## 2) Client (Ubuntu)

Imposta IP del server nello script:

```bash
cd ~/Desktop/PROJ\ VPN/MANUALE
sed -i 's/SERVER_IP = "IP_DEL_SERVER"/SERVER_IP = "192.168.254.134"/' tun_client.py
```

Avvia client:

```bash
sudo ./tun_client.py
```

Sul server vedrai:

```
[*] Nuovo peer: ('192.168.254.X', <porta_udp>)
```

---

## 3) Verifica tunnel

**Server (Kali):**

```bash
ip addr show tun0
ping -c 3 10.20.0.2
```

**Client (Ubuntu):**

```bash
ip addr show tun0
ping -c 3 10.20.0.1
```

---

## 4) (Opzionale) Far passare tutto il traffico del client nella VPN

**Sul server (Kali):**

```bash
# abilita forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# NAT verso l'interfaccia WAN (sostituisci eth0 con la tua, verifica con: ip -br a)
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

**Sul client (Ubuntu):** (full-tunnel temporaneo)

```bash
sudo ip route add default dev tun0
# per ripristinare in seguito: sudo ip route del default dev tun0
```

> Se usi UFW/iptables restrittivi, apri la porta:

```bash
# entrambi (se necessario)
sudo ufw allow 55555/udp
```

---

## 5) Stop & pulizia

Chiudi gli script con `CTRL+C`.
Se necessario rimuovi l’interfaccia (solo se ancora presente):

```bash
sudo ip link delete tun0
```

---

## 6) Troubleshooting rapido

```bash
# vedere se esiste tun0
ip link show | grep tun

# controllare MTU (se ping grandi non passano)
sudo ip link set dev tun0 mtu 1400

# osservare traffico UDP porta 55555
sudo tcpdump -n -i any udp port 55555

# vedere regole iptables NAT
sudo iptables -t nat -S POSTROUTING

# verificare che /dev/net/tun sia accessibile (esegui sempre con sudo)
ls -l /dev/net/tun
```

---

## Note importanti

* Questa implementazione **NON** cifra i pacchetti: è solo per studio del flusso TUN↔UDP.
* Per aggiungere cifratura (PyNaCl: SecretBox + handshake X25519) puoi creare una “fase 2” partendo da questi script.
* Per uso reale, preferisci **WireGuard** e usa questi file solo come base didattica.

