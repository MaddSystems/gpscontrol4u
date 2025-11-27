# GPSControl4U - Guía de Instalación y Configuración

## Requisitos Previos

- Ubuntu/Debian Linux
- Python 3.10+
- MySQL/MariaDB
- Nginx
- Supervisor
- Certbot (para SSL)

## 1. Preparación del Entorno

### 1.1 Instalar Dependencias del Sistema

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y mysql-server mysql-client libmysqlclient-dev
sudo apt install -y nginx supervisor certbot python3-certbot-nginx
sudo apt install -y redis-server
```

### 1.2 Configurar MySQL

```bash
sudo mysql_secure_installation
```

Crear la base de datos:

```bash
sudo mysql -u root -p
```

```sql
CREATE DATABASE gpscontrol4u CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'gpscontrol'@'localhost' IDENTIFIED BY 'qazwsxedc';
GRANT ALL PRIVILEGES ON gpscontrol4u.* TO 'gpscontrol'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 2. Instalación de la Aplicación

### 2.1 Clonar/Copiar el Proyecto

```bash
cd /home/systemd
# Si ya tienes el código en gpscontrol4u, omite este paso
```

### 2.2 Crear Entorno Virtual

```bash
cd /home/systemd/gpscontrol4u
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Instalar Dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 Configurar Variables de Entorno

El archivo `.env` ya está configurado. Verifica que los valores sean correctos:

```bash
cat .env
```

### 2.5 Ejecutar Migraciones

```bash
python manage.py migrate
```

### 2.6 Crear Superusuario

```bash
python manage.py createsuperuser
```

### 2.7 Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 2.8 Crear Directorio de Logs

```bash
mkdir -p /home/systemd/gpscontrol4u/logs
```

## 3. Configuración de Supervisor

### 3.1 Copiar Configuración

```bash
sudo cp /home/systemd/gpscontrol4u/gpscontrol4u.conf /etc/supervisor/conf.d/
```

### 3.2 Crear Archivos de Log

```bash
sudo touch /var/log/gpscontrol4u.err.log
sudo touch /var/log/gpscontrol4u.out.log
sudo chown systemd:systemd /var/log/gpscontrol4u.*.log
```

### 3.3 Activar y Iniciar el Servicio

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gpscontrol4u
```

### 3.4 Verificar Estado

```bash
sudo supervisorctl status gpscontrol4u
```

Deberías ver algo como:
```
gpscontrol4u                     RUNNING   pid 12345, uptime 0:00:10
```

### 3.5 Comandos Útiles de Supervisor

```bash
# Ver logs en tiempo real
sudo tail -f /var/log/gpscontrol4u.out.log
sudo tail -f /var/log/gpscontrol4u.err.log

# Reiniciar el servicio
sudo supervisorctl restart gpscontrol4u

# Detener el servicio
sudo supervisorctl stop gpscontrol4u

# Ver todos los servicios
sudo supervisorctl status
```

## 4. Configuración de Nginx

### 4.1 Copiar Configuración

```bash
sudo cp /home/systemd/gpscontrol4u/store.gpscontrol4u.com /etc/nginx/sites-available/
```

### 4.2 Habilitar el Sitio

```bash
sudo ln -s /etc/nginx/sites-available/store.gpscontrol4u.com /etc/nginx/sites-enabled/
```

### 4.3 Verificar Configuración

```bash
sudo nginx -t
```

### 4.4 Reiniciar Nginx (Sin SSL por ahora)

Primero, comenta temporalmente la sección SSL en el archivo de configuración:

```bash
sudo nano /etc/nginx/sites-available/store.gpscontrol4u.com
```

Comenta o elimina la línea `return 301 https://$host$request_uri;` en el bloque HTTP (puerto 80) y todo el bloque HTTPS (puerto 443).

Luego:

```bash
sudo systemctl restart nginx
```

## 5. Configuración de SSL con Let's Encrypt

### 5.1 Asegúrate de que el Dominio Apunte al Servidor

Verifica que `store.gpscontrol4u.com` apunte a la IP de tu servidor:

```bash
nslookup store.gpscontrol4u.com
```

### 5.2 Detener Nginx Temporalmente

```bash
sudo systemctl stop nginx
```

### 5.3 Obtener Certificado SSL

```bash
sudo certbot certonly --standalone -d store.gpscontrol4u.com
```

Sigue las instrucciones:
1. Ingresa tu correo electrónico
2. Acepta los términos de servicio
3. Decide si quieres compartir tu email con EFF

### 5.4 Verificar Certificados

```bash
sudo ls -la /etc/letsencrypt/live/store.gpscontrol4u.com/
```

Deberías ver:
- `fullchain.pem`
- `privkey.pem`

### 5.5 Restaurar Configuración Nginx Completa

Descomenta las líneas del archivo de Nginx:

```bash
sudo nano /etc/nginx/sites-available/store.gpscontrol4u.com
```

Asegúrate de que contenga tanto el bloque HTTP (con redirect) como el HTTPS completo.

### 5.6 Verificar y Reiniciar Nginx

```bash
sudo nginx -t
sudo systemctl start nginx
```

### 5.7 Configurar Renovación Automática

Certbot ya configura un cron job automáticamente. Verifica:

```bash
sudo systemctl status certbot.timer
```

Prueba la renovación:

```bash
sudo certbot renew --dry-run
```

## 6. Configuración del Firewall (Opcional pero Recomendado)

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

## 7. Verificación Final

### 7.1 Verificar que la Aplicación Esté Corriendo

```bash
curl http://localhost:7008
```

### 7.2 Verificar Nginx

```bash
curl http://store.gpscontrol4u.com
curl https://store.gpscontrol4u.com
```

### 7.3 Acceder desde el Navegador

Abre tu navegador y visita:
- `https://store.gpscontrol4u.com`

## 8. Actualización del Dominio en ALLOWED_HOSTS

Si es necesario, actualiza el archivo `.env`:

```bash
nano .env
```

Asegúrate de que `ALLOWED_HOSTS` incluya tu dominio:

```
ALLOWED_HOSTS=localhost,127.0.0.1,store.gpscontrol4u.com
```

Luego reinicia la aplicación:

```bash
sudo supervisorctl restart gpscontrol4u
```

## 9. Troubleshooting

### Ver logs de la aplicación
```bash
sudo tail -f /var/log/gpscontrol4u.err.log
sudo tail -f /var/log/gpscontrol4u.out.log
```

### Ver logs de Nginx
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Ver logs de Supervisor
```bash
sudo tail -f /var/log/supervisor/supervisord.log
```

### Reiniciar todos los servicios
```bash
sudo supervisorctl restart gpscontrol4u
sudo systemctl restart nginx
```

### Verificar que el puerto 7008 esté escuchando
```bash
sudo netstat -tulpn | grep 7008
```

### Verificar permisos
```bash
ls -la /home/systemd/gpscontrol4u/
```

## 10. Mantenimiento

### Backup de la Base de Datos

```bash
mysqldump -u gpscontrol -p gpscontrol4u > backup_$(date +%Y%m%d).sql
```

### Actualizar la Aplicación

```bash
cd /home/systemd/gpscontrol4u
source .venv/bin/activate
git pull  # Si usas Git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart gpscontrol4u
```

### Renovar Certificado SSL Manualmente

```bash
sudo certbot renew
sudo systemctl reload nginx
```

## 11. Configuración de Correo Electrónico

La configuración de correo ya está en `.env`. Verifica que:
- `EMAIL_HOST_USER=gpscontrol4u@madd.com.mx`
- `EMAIL_HOST_PASSWORD=GPSc0ntr0l01`

Prueba el envío de correos:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message',
    'orders@store.gpscontrol4u.com',
    ['tu-email@example.com'],
    fail_silently=False,
)
```

## 12. Comandos de Gestión Django

```bash
# Activar entorno virtual
cd /home/systemd/gpscontrol4u
source .venv/bin/activate

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Limpiar usuarios no verificados
python manage.py cleanup_unverified_users

# Poblar datos de ejemplo
python manage.py populate_sample_data

# Shell de Django
python manage.py shell
```

## Contacto y Soporte

Para problemas o preguntas, contacta al equipo de desarrollo.

---

**Última actualización:** Noviembre 2025
