# Autostart de Aplicaciones en Jetson usando Systemd

Para el proyecto BFMC en la NVIDIA Jetson, se han configurado dos servicios independientes de `systemd`. Esta arquitectura asegura que el Dashboard y las Notificaciones corran en paralelo y que un fallo en uno no afecte al otro.

#### Resumen de Servicios

---

#### 1. Servicio: Dashboard (`bfmc-dashboard.service`)

Este servicio ejecuta el servidor principal.

- **Ubicación:** `/etc/systemd/system/bfmc-dashboard.service`
- **Nota:** Incluye `PYTHONUNBUFFERED=1` para ver los logs en tiempo real sin retraso.

```bash
[Unit]
Description=BFMC Dashboard Server
After=network.target

[Service]
Type=simple
User=jetson

# Variable para forzar que los print() salgan al log inmediatamente (sin buffer)
Environment=PYTHONUNBUFFERED=1

# Ejecuta usando el Python del VENV
ExecStart=/home/jetson/app/brain/brain/venv/bin/python /home/jetson/app/brain/brain/dashboard/dashboard_server.py

# Directorio de trabajo establecido para evitar errores de importación relativa
WorkingDirectory=/home/jetson/app/brain/brain/dashboard

Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

#### 2. Servicio: Notificador Telegram (`bfmc-telegram.service`)

Este script envía la IP al iniciar.

- **Ubicación:** `/etc/systemd/system/bfmc-telegram.service`
- **Nota:** Espera a `network-online.target` para garantizar acceso a Internet.

```bash
[Unit]
Description=BFMC Telegram Connectivity Notifier
# Espera a que la red esté ONLINE (con IP e Internet), no solo activa
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=jetson
# Ejecuta usando el Python del sistema, apuntando explícitamente al binario
ExecStart=/usr/bin/python3 /home/jetson/app/autostart/startup_telegram_sendip.py
WorkingDirectory=/home/jetson/app/autostart

# 'on-failure' evita bucles infinitos si el mensaje se envía correctamente
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

#### Guía de Comandos y Mantenimiento

#### Instalación Inicial

Ejecutar una sola vez para registrar los servicios en el arranque.

Bash

`sudo systemctl daemon-reload
sudo systemctl enable bfmc-dashboard.service
sudo systemctl enable bfmc-telegram.service`

#### Monitoreo en Tiempo Real (Live Logs)

Para ver lo que está imprimiendo el script en vivo (como si miraras la terminal), sin detener el servicio.

Bash

`# Ver logs del Dashboard en vivo
sudo journalctl -u bfmc-dashboard.service -f`

*(Presiona **`Ctrl + C`** para salir de la visualización)*

#### Comandos Útiles de Control

- **Reiniciar servicio** (necesario tras modificar código Python):Bash
    `sudo systemctl restart bfmc-dashboard.service`

- **Verificar estado** (saber si murió o está corriendo):Bash
    `sudo systemctl status bfmc-dashboard.service`

- **Ver historial de errores** (si el servicio murió hace rato):Bash
    `sudo journalctl -u bfmc-dashboard.service -e`


## Detener el servicio (frena la ejecución)

Como al encender la jetson vamos a tener corriendo todo de forma automatica, la forma de detener eso es corriendo el comando:

`sudo systemctl stop dashboard.service`
