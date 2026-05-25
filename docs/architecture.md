# Grid Stress Monitor - Architecture

## Overview

A continuous monitoring system for grid stress under renewable integration. Pulls real generation data from US RTOs (EIA, ERCOT), computes stress metrics in C++, stores results in Postgres, and exposes them via a Flask API.

## System Diagram

Internet
|
|
Nginx (port 80/443) <- reverse proxy, handles HTTP
|
|
Flask (port 5000) <- Python API, business logic
|
|
Postgres (port 5432) <- stores raw + derived data

## Components

### Nginx
Reverse proxy running on the VPS. Accepts public HTTP requests and forwards them to Flask. Handles SSL termination (future). Defined as a systemd service.

### Flask (app.py)
Python API server. Currently exposes /health and /db endpoints. Will grow to expose processed grid metrics. Reads credentials from .env via python-dotenv. Defined as a systemd service.

### Postgres
Primary data store. Database: griddb. Application user: flask (limited permissions). Will hold raw EIA/ERCOT data and derived analytics. Defined as a systemd service.

### C++ Analytics Layer
Will handle performance-sensitive computations: ramp rate, duck curve, curtailment, frequency deviation. Connects to Postgres via libpq. Produces derived metrics that Flask exposes via API.

## Machines

- VPS (arch-1): 178.105.208.98 - runs all services
- ThinkPad: development machine, WireGuard IP 10.10.0.1
- Mac: secondary machine, WireGuard IP 10.10.0.2

## Network

WireGuard tunnel connects all three machines on 10.10.0.0/24.
VPS firewall (iptables) allows only ports 22, 80, 443, 51820.
Flask and Postgres are not exposed publicly - only reachable via Nginx or WireGuard.
