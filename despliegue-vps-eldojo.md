# Despliegue VPS - ElDojo

Esta guia deja funcionando los tres componentes del proyecto dentro de la misma VPS:

- Base de datos en `/opt/el-dojo-admin-db`
- Backend en `~/eldojo/eldojo-backend-api`
- Frontend en `~/eldojo/eldojo-mobile`

La recomendacion para tu caso actual, donde todavia no usas dominio personalizado, es publicar ambos bajo el mismo host de la VPS:

- Frontend en `/`
- Backend en `/api/`
- Swagger en `/docs`
- Uploads en `/uploads/`

Con esto evitas problemas innecesarios de CORS y no dependes de subdominios.

## 1. Suposiciones de trabajo

Esta guia asume lo siguiente:

- Ya tienes los repos clonados en la VPS
- MySQL ya esta levantado y el backend ya logro conectarse localmente
- `nginx` ya esta instalado y funcionando
- Quieres seguir usando:
  - `pm2` para el frontend
  - `gunicorn` para el backend

Rutas esperadas:

```bash
/opt/el-dojo-admin-db
/root/eldojo/eldojo-backend-api
/root/eldojo/eldojo-mobile
```

Si tus rutas reales cambian, sustituye las rutas en todos los comandos.

## 2. Instalar dependencias base del servidor

Si la VPS ya tiene algunas, puedes omitir lo que no haga falta:

```bash
apt update
apt install -y python3 python3-venv python3-pip nginx git curl
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g pm2
```

Verifica:

```bash
python3 --version
node -v
npm -v
pm2 -v
nginx -v
```

## 3. Preparar o validar la base de datos

Si la base ya esta migrada y el backend ya conectaba, usa este paso solo para validar.

```bash
cd /opt/el-dojo-admin-db
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
cp .env.example .env
nano .env
```

Contenido esperado de `.env`:

```env
DATABASE_URL=mysql+pymysql://TU_USUARIO:TU_PASSWORD@127.0.0.1:3306/eldojo_db
```

Aplica migraciones:

```bash
python -m alembic upgrade head
```

Si es una instalacion nueva y quieres sembrar datos base:

```bash
python -m scripts.seed
```

## 4. Preparar el backend

En este proyecto el backend es FastAPI y el entrypoint correcto es:

```bash
app.main:app
```

No uses `app:app` porque en este repo la aplicacion no vive en la raiz.

### 4.1 Crear entorno virtual e instalar dependencias

```bash
cd ~/eldojo/eldojo-backend-api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install gunicorn
cp .env.example .env
nano .env
```

### 4.2 Configurar `.env`

Usa algo de este estilo:

```env
APP_NAME=ElDojo Backend API
APP_ENV=production
APP_DEBUG=false
API_V1_PREFIX=/api/v1
DATABASE_URL=mysql+pymysql://TU_USUARIO:TU_PASSWORD@127.0.0.1:3306/eldojo_db
AUTH_SECRET_KEY=CAMBIA_ESTA_CLAVE_POR_UNA_MUY_LARGA_Y_PRIVADA
AUTH_ALGORITHM=HS256
AUTH_ISSUER=eldojo-backend-api
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=120
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=30
BACKEND_CORS_ORIGINS=http://TU_HOST_VPS,http://TU_IP_PUBLICA
UPLOADS_DIR=/root/eldojo/eldojo-backend-api/uploads
UPLOADS_URL_PREFIX=/uploads
```

Notas:

- Como MySQL vive en la misma VPS, `127.0.0.1` es la opcion correcta
- `BACKEND_CORS_ORIGINS` debe incluir el host real desde donde abriras el frontend
- Aunque frontend y backend queden bajo el mismo host, conviene dejar el host publico en la lista

### 4.3 Crear carpeta de uploads

```bash
mkdir -p ~/eldojo/eldojo-backend-api/uploads
```

### 4.4 Levantar backend manualmente

Tu forma actual con `nohup` es valida. Solo ajusta el comando al stack real de FastAPI:

```bash
cd ~/eldojo/eldojo-backend-api
source .venv/bin/activate
nohup ./.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:5000 app.main:app > api.log 2>&1 &
```

Importante:

- Escuchamos en `127.0.0.1:5000` para que solo `nginx` lo exponga
- `-k uvicorn.workers.UvicornWorker` es necesario para FastAPI/ASGI

### 4.5 Validar backend

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/api/v1/health
curl http://127.0.0.1:5000/api/v1/health/db
tail -f ~/eldojo/eldojo-backend-api/api.log
```

Si `health/db` responde bien, el backend ya esta viendo la base.

## 5. Preparar el frontend

Este proyecto no debe quedar corriendo con `expo start --web` en produccion. Lo correcto es exportar la version web y servirla con `pm2`.

### 5.1 Instalar dependencias y configurar `.env`

```bash
cd ~/eldojo/eldojo-mobile
npm install
cp .env.example .env
nano .env
```

Pon la URL publica del backend con el mismo host de la VPS:

```env
EXPO_PUBLIC_API_URL=http://TU_HOST_VPS/api/v1
```

Si haras pruebas solo por IP:

```env
EXPO_PUBLIC_API_URL=http://TU_IP_PUBLICA/api/v1
```

Importante:

- Esta variable debe terminar en `/api/v1`
- Si la cambias, debes volver a generar el build web

### 5.2 Generar el build web

```bash
cd ~/eldojo/eldojo-mobile
npx expo export --platform web
```

Esto genera la carpeta `dist/`.

### 5.3 Levantar el frontend con `pm2`

```bash
cd ~/eldojo/eldojo-mobile
pm2 serve dist 3000 --name eldojo-mobile --spa
pm2 save
pm2 list
pm2 logs eldojo-mobile
curl http://127.0.0.1:3000
```

Si en tu VPS ya usas `pm2 startup` con otros proyectos, normalmente no hace falta repetirlo.

## 6. Como encaja con tu `nginx.conf`

Tu `nginx.conf` actual ya incluye:

- `include /etc/nginx/conf.d/*.conf;`
- `include /etc/nginx/sites-enabled/*;`

Eso significa que no necesitas tocar toda la configuracion global para levantar ElDojo.

Puedes crear un nuevo archivo en `sites-available` y activarlo con symlink, igual que en tus otros proyectos.

Tu `nginx.conf` tambien tiene upstreams globales como:

```nginx
upstream api_backend {
    server 127.0.0.1:48173;
    keepalive 32;
}

upstream front_backend {
    server 127.0.0.1:4173;
    keepalive 16;
}
```

Para ElDojo no es obligatorio reutilizar esos upstreams. Puedes apuntar directo a:

- backend `127.0.0.1:5000`
- frontend `127.0.0.1:3000`

Eso evita tocar sitios ya existentes.

## 7. Crear el archivo de Nginx para ElDojo

### 7.1 Elegir el host

Como aun no tienes dominio personalizado, define primero cual sera el host de prueba:

- El hostname publico que te da la VPS
- o la IP publica del servidor

Ejemplos:

```text
srv1333724.tu-proveedor.com
123.45.67.89
```

### 7.2 Crear el archivo en `sites-available`

```bash
nano /etc/nginx/sites-available/eldojo
```

Pega esto y sustituye `TU_HOST_VPS` y `TU_IP_PUBLICA` por tus valores reales:

```nginx
server {
    listen 80;
    server_name TU_HOST_VPS TU_IP_PUBLICA;

    client_max_body_size 20M;

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.3 Activar el sitio

```bash
ln -s /etc/nginx/sites-available/eldojo /etc/nginx/sites-enabled/eldojo
nginx -t
systemctl reload nginx
```

Si ya existe un enlace previo o necesitas recrearlo:

```bash
rm -f /etc/nginx/sites-enabled/eldojo
ln -s /etc/nginx/sites-available/eldojo /etc/nginx/sites-enabled/eldojo
nginx -t
systemctl reload nginx
```

## 8. Validaciones finales

Prueba desde la VPS:

```bash
curl http://127.0.0.1:3000
curl http://127.0.0.1:5000/api/v1/health
curl http://TU_HOST_VPS/
curl http://TU_HOST_VPS/api/v1/health
curl http://TU_HOST_VPS/api/v1/health/db
```

Luego abre en navegador:

```text
http://TU_HOST_VPS/
http://TU_HOST_VPS/docs
```

Pruebas recomendadas:

- Abrir el frontend
- Hacer login
- Confirmar que el frontend llama a `/api/v1/...`
- Confirmar que `/api/v1/health/db` responde
- Validar que uploads cargan si usas imagenes

## 9. Si quieres HTTPS despues

Cuando ya tengas dominio propio o un hostname valido apuntando a la VPS:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d TU_DOMINIO
```

Si usas `www`, agregalo tambien:

```bash
certbot --nginx -d TU_DOMINIO -d www.TU_DOMINIO
```

Luego Certbot te reescribe el archivo con el patron parecido al que ya usas en `raislabs`.

## 10. Como actualizar en futuras versiones

### Backend

```bash
cd ~/eldojo/eldojo-backend-api
git pull
source .venv/bin/activate
pip install -e .
pkill -f "gunicorn.*app.main:app"
nohup ./.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:5000 app.main:app > api.log 2>&1 &
```

Si hubo cambios de base de datos:

```bash
cd /opt/el-dojo-admin-db
source .venv/bin/activate
python -m alembic upgrade head
```

### Frontend

```bash
cd ~/eldojo/eldojo-mobile
git pull
npm install
npx expo export --platform web
pm2 restart eldojo-mobile
```

## 11. Errores comunes

### El frontend abre pero no inicia sesion

Revisa:

- `EXPO_PUBLIC_API_URL`
- que termine en `/api/v1`
- que `nginx` tenga el bloque `location /api/`
- que el backend siga vivo en `127.0.0.1:5000`

### `502 Bad Gateway`

Significa que `nginx` no esta alcanzando el proceso interno:

```bash
curl http://127.0.0.1:5000/api/v1/health
curl http://127.0.0.1:3000
tail -f ~/eldojo/eldojo-backend-api/api.log
pm2 logs eldojo-mobile
```

### Error de CORS

Aunque con mismo host se minimiza mucho, revisa:

- `BACKEND_CORS_ORIGINS`
- que el host real del navegador este incluido

### `nginx -t` falla

Revisa sintaxis del archivo:

```bash
nginx -t
cat /etc/nginx/sites-available/eldojo
```

## 12. Nota sobre tu ejemplo `raislabs`

En el ejemplo que pegaste aparecen estas lineas:

```nginx
return 301 `https://$host$request_uri;`
```

Esos acentos invertidos no deben existir en la configuracion real de `nginx`.

La forma correcta es:

```nginx
return 301 https://$host$request_uri;
```

Si esos acentos aparecieron solo por el pegado del mensaje, no pasa nada. Si estan realmente en el archivo del servidor, corrige eso antes de recargar `nginx`.

## 13. Orden recomendado de ejecucion

Hazlo en este orden:

1. Validar o migrar DB
2. Levantar backend en `127.0.0.1:5000`
3. Probar backend con `curl`
4. Generar build del frontend
5. Levantar frontend con `pm2` en `127.0.0.1:3000`
6. Crear archivo `sites-available/eldojo`
7. Activar sitio y recargar `nginx`
8. Probar login desde navegador

## 14. Comandos de diagnostico rapido

```bash
curl http://127.0.0.1:5000/api/v1/health
curl http://127.0.0.1:5000/api/v1/health/db
curl http://127.0.0.1:3000
pm2 list
pm2 logs eldojo-mobile
tail -f ~/eldojo/eldojo-backend-api/api.log
nginx -t
systemctl status nginx
```
