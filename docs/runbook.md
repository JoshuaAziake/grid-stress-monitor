# Grid Stress Monitor - Runbook

Operational guide for running and maintaining the system.
This document answers: how do I start it, check it, and fix it.

---

## Machines

- VPS (arch-1): 178.105.208.98
- ThinkPad: development machine (WireGuard: 10.10.0.1)
- Mac: secondary machine (WireGuard: 10.10.0.2)

SSH into VPS:
    ssh joshua@178.105.208.98

---

## Services

Three systemd services run on the VPS: nginx, flask, postgresql.

Check status of all three:
    sudo systemctl status nginx flask postgresql 

Check health status:
    curl -s http://localhost:5000/health
    curl -s http://178.105.208.98/health

List databases:
    sudo -u postgres psql -c "\l"

Row count:
    sudo -u postgres psql -d griddb -c "SELECT COUNT(*) FROM generation;"

Timer schedule:
    systemctl list-timers eia-ingest.timer

Ingest logs:
    journalctl -u eia-ingest.service -n 20

Restart a service:
    sudo systemctl restart X

Stop a service:
    sudo systemctl stop X

Start a service:
    sudo systemctl start X

All three services are enabled on boot. If the VPS reboots, they start automatically.

---

## Flask App

Location: /home/joshua/app
Entry point: app.py
Virtual environment: /home/joshua/app/venv/

Activate venv manually:
    cd /home/joshua/app
    source venv/bin/activate

Credentials are stored in /home/joshua/app/.env
Never commit .env to Git.

Test Flask is responding:
    curl http://127.0.0.1:5000/health
    curl http://127.0.0.1:5000/db

---

## Postgres

Database name: griddb
Application user: flask (limited permissions)
Superuser: postgres

Connect as superuser:
    sudo -u postgres psql

Connect to griddb directly:
    sudo -u postgres psql -d griddb

List all databases:
    sudo -u postgres psql -c "\l"

List tables in griddb:
    sudo -u postgres psql -d griddb -c "\dt"

---

## Nginx

Config location: /etc/nginx/nginx.conf
Nginx proxies all public HTTP traffic to Flask on port 5000.

Test nginx config is valid before restarting:
    sudo nginx -t

Reload nginx:
    sudo systemctl reload nginx

View access logs:
    sudo tail -f /var/log/nginx/access.log

View error logs:
    sudo tail -f /var/log/nginx/error.log

---

## Firewall

Managed by iptables. Allowed ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 51820 UDP (WireGuard).

View current rules:
    sudo iptables -L -v --line-numbers

---

## WireGuard

Tunnel connects ThinkPad, Mac, and VPS on 10.10.0.0/24.
Interface: wg0

Check tunnel status:
    sudo wg show

Restart WireGuard:
    sudo systemctl restart wg-quick@wg0
