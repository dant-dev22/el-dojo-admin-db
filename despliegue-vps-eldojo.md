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
cd /eldojo/eldojo-api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install gunicorn
cp .env.example .env
nano .env
```

### 4.2 Configurar `.env`

Usa algo de este estilo. En tu VPS actual el `.env` real ya tiene password y CORS correctos, pero el template debe incluir los DOS orígenes (público + app.*) y los paths reales:

```env
APP_NAME=ElDojo Backend API
APP_ENV=production
APP_DEBUG=false
API_V1_PREFIX=/api/v1
DATABASE_URL=mysql+pymysql://eldojo_app:N7_xK9mP2_vQ@127.0.0.1:3306/eldojo_db
AUTH_SECRET_KEY=eDuYpR88kbiAsA5j0AErCSG6gWncgQNCa1cKlVwMiATt9uF6exuRDjJOsb0=
AUTH_ALGORITHM=HS256
AUTH_ISSUER=eldojo-backend-api
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=120
AUTH_REFRESH_TOKEN_EXPIRE_DAYS=30
BACKEND_CORS_ORIGINS=https://eldojo.tech,https://www.eldojo.tech,https://app.eldojo.tech,http://eldojo.tech,http://www.eldojo.tech,http://app.eldojo.tech,http://localhost:8081,http://127.0.0.1:8081,http://localhost:8082,http://127.0.0.1:8082,http://localhost:19006,http://127.0.0.1:19006
UPLOADS_DIR=/eldojo/eldojo-api/uploads
UPLOADS_URL_PREFIX=/uploads
ACADEMY_VERIFICATION_URL_BASE=https://eldojo.tech/confirmar-cuenta
```

Notas:

- Como MySQL vive en la misma VPS, `127.0.0.1` es la opcion correcta
- `BACKEND_CORS_ORIGINS` **DEBE INCLUIR** `app.eldojo.tech` (además de `eldojo.tech`) porque el panel admin corre en subdominio separado (dual-origin). Si lo omites, login correcto pero los fetchs `/api/v1/*` desde `app.eldojo.tech` fallaran en CORS.
- `load_dotenv(override=True)`: a partir del commit `fix/dotenv-override-local-db-runner`, el valor de `DATABASE_URL` y las demás de este `.env` siempre ganan sobre variables heredadas del shell/systemd. Así que este archivo `.env` es la fuente única de verdad. Asegurate de que exista y tenga los valores correctos.

### 4.3 Crear carpeta de uploads

```bash
mkdir -p /eldojo/eldojo-api/uploads
chown -R root:root /eldojo/eldojo-api/uploads
```

### 4.4 Levantar backend con systemd (o nohup temporal)

La forma recomendada es un servicio `systemd` para restart automático. Ejemplo de `/etc/systemd/system/eldojo-api.service`:

```ini
[Unit]
Description=ElDojo Backend API (FastAPI + gunicorn)
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/eldojo/eldojo-api
Environment=PYTHONUNBUFFERED=1
# NO pongas Environment=DATABASE_URL=... a menos que sea intencional y distinto del .env.
# Con load_dotenv(override=True), los valores del .env ganan SIEMPRE a las variables de entorno aqui.
ExecStart=/eldojo/eldojo-api/.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:5000 --access-logfile /var/log/eldojo-api.access.log --error-logfile /var/log/eldojo-api.error.log app.main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Luego:

```bash
systemctl daemon-reload
systemctl enable eldojo-api
systemctl start  eldojo-api
systemctl status eldojo-api
```

Si prefieres no usar systemd y levantarlo temporal, el `nohup` sigue siendo válido, solo ajusta los paths reales:

```bash
cd /eldojo/eldojo-api
source .venv/bin/activate
nohup ./.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:5000 app.main:app > /var/log/eldojo-api.nohup.log 2>&1 &
```

Importante:

- Escuchamos en `127.0.0.1:5000` para que solo `nginx` lo exponga
- `-k uvicorn.workers.UvicornWorker` es necesario para FastAPI/ASGI
- Usa `systemctl restart eldojo-api` en futuros updates. Con `override=True` no hace falta exportar variables en la shell.

### 4.5 Validar backend

```bash
curl -sS http://127.0.0.1:5000/api/v1/health
curl -sS http://127.0.0.1:5000/api/v1/health/db | python3 -m json.tool | head -n 30
journalctl -u eldojo-api -n 60 --no-pager
# o si usas nohup:
tail -n 60 /var/log/eldojo-api.nohup.log
```

Si `health/db` responde bien con `connected=true` y 1+ organizations, el backend ya esta viendo la base y CORS tiene los origins correctos.

## 5. Preparar el frontend

Este proyecto no debe quedar corriendo con `expo start --web` en produccion. Lo correcto es exportar la version web y servirla con `pm2`.

IMPORTANTE (arquitectura productiva): El proyecto `eldojo-mobile` esta DISEÑADO para funcionar en **DUAL-ORIGIN** (origen publico + origen admin separados). NO intentes montar todo en un solo dominio/puerto con rutas `/admin` y `/home` compartiendo el mismo `origin`, porque el anti-loop de `AppNavigator.tsx` puede disparar `window.location.assign` en bucle cuando `getDomainConfig()` detecta ambos en la misma URL.

Origenes recomendados en tu VPS actual:

| Origen | Proposito | Detectado por `domains.ts` |
|---|---|---|
| `https://eldojo.tech` | Sitio publico (home / iniciar-sesion / crear-cuenta / eventos / tiendas / confirmar-cuenta) | `isPublicHostname = true` |
| `https://app.eldojo.tech` | Panel administrativo ( `/admin*`, listados, alumnos, pagos, trayectoria ) | `hostname.startsWith("app.")` => `isAppHostname = true` |

Necesitas ambos `server_name` declarados en `nginx`, ambos servidos por el mismo build web exportado (`dist/`). NO hace falta generar un build distinto por origen: el bundle en runtime usa `getDomainConfig()` para decidir que flow renderizar.

### 5.1 Instalar dependencias y configurar `.env`

```bash
cd /eldojo/eldojo-front
npm ci
cp .env.example .env
nano .env
```

Pon **TODAS** las variables que aparecen abajo (no solo `EXPO_PUBLIC_API_URL`). Son build-time: quedan hardcodeadas en el bundle. Si cambias alguna, tienes que re-generar `dist/` de cero.

```env
# URL publica del backend, terminando en /api/v1
EXPO_PUBLIC_API_URL=https://eldojo.tech/api/v1

# Origen publico (sitio publico + SignIn). Debe ser el mismo que el server_name publico de nginx.
EXPO_PUBLIC_PUBLIC_WEB_ORIGIN=https://eldojo.tech

# Origen admin (panel). Normalmente subdominio app.*.
EXPO_PUBLIC_APP_WEB_ORIGIN=https://app.eldojo.tech
```

Si haces pruebas solo por IP publica (sin dominio), usa estos valores y monta dos puertos distintos en nginx (ej. `:8081` publico y `:8082` admin) o dos server_name con IP/alias distintos en tu cliente:

```env
EXPO_PUBLIC_API_URL=http://TU_IP_PUBLICA/api/v1
EXPO_PUBLIC_PUBLIC_WEB_ORIGIN=http://TU_IP_PUBLICA:8081
EXPO_PUBLIC_APP_WEB_ORIGIN=http://TU_IP_PUBLICA:8082
```

Importante:

- `EXPO_PUBLIC_API_URL` debe terminar SIEMPRE en `/api/v1`
- `EXPO_PUBLIC_PUBLIC_WEB_ORIGIN` y `EXPO_PUBLIC_APP_WEB_ORIGIN` deben ser **distintos** (host o puerto, cualquiera de los dos) para que `AppNavigator.tsx` NO caiga en el caso patologico "single origin + /admin" que causa reload loop.
- Si modificas cualquiera de las 3, borras `dist/` y re-generas el build (el valor de estas variables NO cambia en caliente).

### 5.2 Generar el build web

```bash
cd /eldojo/eldojo-front
# 1) Borramos dist viejo (evita archivos residuales de builds antiguos con EXPO_PUBLIC_* hardcodeados a :5001/:8081/:8082)
rm -rf dist
# 2) Asegurar dependencias reproducidas
npm ci
# 3) Build. Se injectan las EXPO_PUBLIC_* del .env ACTUAL en este paso.
npx expo export --platform web
# 4) Verificacion rapida: index.html tiene que tener fecha de HOY
ls -la dist/index.html
```

Esto genera la carpeta `dist/`.

### 5.3 Levantar el frontend con `pm2`

`pm2 serve` debe apuntar a `dist/` y su `exec cwd` tiene que ser el directorio donde vive `dist/` (no la raiz del repo). En tu VPS actual el valor correcto es `/eldojo/eldojo-front/dist`.

Si ya tenias el proceso creado y quieres sobreescribirlo (recomendado):

```bash
cd /eldojo/eldojo-front
pm2 delete eldojo-mobile 2>/dev/null || true
# NOTA: el puerto 3000 es interno; nginx lo expone al mundo con proxy_pass a front_backend.
pm2 serve dist 3000 --name eldojo-mobile --spa
pm2 save
pm2 list
pm2 logs --lines 80 eldojo-mobile
curl -sSI http://127.0.0.1:3000 | head -n 5
```

Si en tu VPS ya usas `pm2 startup` con otros proyectos, normalmente no hace falta repetirlo.

Verifica en la salida de `pm2 show eldojo-mobile` que:
- `status = online`
- `exec cwd` = `/eldojo/eldojo-front/dist` (y no una ruta antigua como `/root/eldojo/eldojo-mobile/dist`)
- `restarts` no aumenta solo en 1 minuto (si lo hace, hay un build roto o permisos faltantes; mirar `pm2 logs eldojo-mobile --err`).

## 6. Como encaja con tu `nginx.conf`

Tu `nginx.conf` actual ya incluye:

- `include /etc/nginx/conf.d/*.conf;`
- `include /etc/nginx/sites-enabled/*;`

Eso significa que no necesitas tocar toda la configuracion global para levantar ElDojo.

Puedes crear un nuevo archivo en `sites-available` y activarlo con symlink, igual que en tus otros proyectos.

Tu `nginx.conf` tambien tiene upstreams globales como:

```nginx
upstream api_backend {
    server 127.0.0.1:5000;
    keepalive 32;
}

upstream front_backend {
    server 127.0.0.1:3000;
    keepalive 16;
}
```

NOTA: Ajusta los puertos a los reales de tu VPS. En tu entorno actual:
- `api_backend` debería apuntar a `127.0.0.1:5000` (workers gunicorn, confirmado por `ss -ltnp`)
- `front_backend` apunta al puerto donde `pm2 serve` publica el `dist/` (típicamente `3000`; usa `ss -ltnp | grep node` para confirmar)

Para ElDojo no es obligatorio reutilizar esos upstreams. Puedes apuntar directo a `127.0.0.1:5000` y `127.0.0.1:3000` en los `proxy_pass`. Eso evita tocar sitios ya existentes.

**REGLA INQUEBRANTABLE (evita loop infinito en login):** En `nginx` tienes que declarar **DOS bloques `server {}` separados** (uno por cada origin), aunque ambos hagan `proxy_pass` al mismo `front_backend`. NUNCA sirvas `eldojo.tech` y `app.eldojo.tech` desde el mismo bloque `server {}` con dos `server_name` y después intentes usar `location /admin` para distinguir panel vs público. Ese caso "single origin + /admin" es el bug pattern que dispara el loop en `AppNavigator.tsx` (location.assign al mismo URL).

## 7. Crear el archivo de Nginx para ElDojo

### 7.1 Hosts reales en tu VPS

En producción ya tienes:

- `eldojo.tech` + `www.eldojo.tech` (público)
- `app.eldojo.tech` (admin)

Si aún usas IP/hostname temporal sin DNS, monta 2 puertos lógicos en un solo server_name o usa entradas `/etc/hosts` locales en tu máquina cliente con 2 nombres distintos hacia la misma IP (ej: `eldojo.local` + `app.eldojo.local`).

### 7.2 Crear el archivo en `sites-available`

```bash
nano /etc/nginx/sites-available/eldojo
```

Pega esto. Incluye DOS bloques `server {}` separados (uno público, uno admin) + location `/api/` compartida en ambos, porque desde `app.eldojo.tech` el bundle hace llamadas a `https://eldojo.tech/api/v1/*` según `EXPO_PUBLIC_API_URL`. Si prefieres que el backend se pueda llamar también desde `https://app.eldojo.tech/api/*` por si cambias el `EXPO_PUBLIC_API_URL` en el futuro, se incluye en ambos server blocks.

```nginx
# ============================================================
# BLOQUE 1/2  -  Sitio PUBLICO (home / iniciar-sesion / crear-cuenta)
# ============================================================
server {
    listen 80;
    server_name eldojo.tech www.eldojo.tech;

    client_max_body_size 20M;

    # -- API (proxy al backend gunicorn :5000)
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

    # -- Frontend (SPA, cualquier path resuelve a index.html)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ============================================================
# BLOQUE 2/2  -  Panel ADMIN  ( /admin*, /admin/alumnos, etc )
# ============================================================
server {
    listen 80;
    server_name app.eldojo.tech;

    client_max_body_size 20M;

    # API (permite llamadas tambien desde app.* por si EXPO_PUBLIC_API_URL lo cambias)
    location /api/ {
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

    # Panel admin: MISMO build dist/ que el publico, distinto origin.
    # El bundle detecta "app." en el host y muestra AdminFlow.
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
rm -f /etc/nginx/sites-enabled/eldojo
ln -s /etc/nginx/sites-available/eldojo /etc/nginx/sites-enabled/eldojo
nginx -t
systemctl reload nginx
```

Si ya tienes otros bloques server en el puerto 80, `nginx -t` fallará por conflicto de `server_name`. En ese caso, revisa y fusiona en UN SOLO archivo por sitio.

## 8. Validaciones finales

Prueba desde la VPS:

```bash
curl -sS -o /dev/null -w "frontend publico %{http_code}\n" http://127.0.0.1:3000
curl -sS -o /dev/null -w "backend health %{http_code}\n"   http://127.0.0.1:5000/api/v1/health
curl -sSI http://eldojo.tech/          | head -n 5
curl -sSI http://app.eldojo.tech/      | head -n 5
curl -sSI http://eldojo.tech/api/v1/health | head -n 5
curl -sS  http://eldojo.tech/api/v1/health/db | python3 -m json.tool | head -n 20
```

Luego abre en navegador (usa incógnito para no arrastrar JWT viejo):

```text
https://eldojo.tech/
https://app.eldojo.tech/
https://eldojo.tech/docs
```

Checklist anti-loop productivo (hacerlo SIEMPRE después de deployar un nuevo build del frontend):

1. Abrir `https://eldojo.tech/` → debe cargar sitio público home, sin redirect a `app.`.
2. Click "Iniciar sesión" → `https://eldojo.tech/iniciar-sesion` (queda en origin público). Ingresar credenciales admin.
3. Después de submit "Entrar":
   - Debe hacer **1 solo** `window.location.assign` hacia `https://app.eldojo.tech/admin` (cambia el origin, NO recarga mismo URL)
   - Panel admin carga, menú visible, NO se recarga infinitamente, NO vuelve a `/iniciar-sesion`.
4. DevTools → Network:
   - `POST https://eldojo.tech/api/v1/auth/login` 200 (no 404/401/502)
   - Subsecuentes `GET /students`, `/classes`, `/organizations/1` todos 200.
5. DevTools → Console: 0 ERRORS. Puede haber warnings benignos de `shadow*` deprecado o Animated; ignorar.
6. Ir a `https://app.eldojo.tech/admin/alumnos` (deep link), F5 → carga misma página, no redirige a público.
7. Click "Cerrar sesión": debe terminar en `https://eldojo.tech/iniciar-sesion` o home público, sin errores.

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

**Orden OBLIGATORIO:** actualiza SIEMPRE backend PRIMERO, frontend DESPUES. No al revés. Porque si el nuevo front espera un endpoint/body nuevo y el back viejo no lo tiene, login y panel empiezan a fallar sin razón aparente.

### Backend (paths reales VPS)

```bash
cd /eldojo/eldojo-api
# 1) Verifica que working tree este limpio (sin cambios manuales sin commit)
git status --short
git fetch origin
git pull origin master   # o la rama default (main)

# 2) Asegurar dependencias nuevas
source .venv/bin/activate
pip install -e .
# si tienes requirements.txt en vez de pyproject.toml: pip install -r requirements.txt

# 3) Si hubo cambios de migraciones SQL/Alembic (opcional):
cd /opt/el-dojo-admin-db
source .venv/bin/activate
python -m alembic upgrade head
cd -

# 4) Reinicio controlado. Usa systemd SI lo tienes, si no pkill/nohup
if systemctl list-units --type=service | grep -qE 'eldojo-api|eldojo-backend'; then
  systemctl restart eldojo-api || systemctl restart eldojo-backend
  systemctl status  eldojo-api || systemctl status eldojo-backend --no-pager -l
else
  pkill -f "gunicorn.*app.main:app"
  cd /eldojo/eldojo-api
  source .venv/bin/activate
  nohup ./.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:5000 app.main:app > /var/log/eldojo-api.nohup.log 2>&1 &
fi

# 5) Smoke IMPRESCINDIBLE (si esto falla, NO toques el frontend aun)
sleep 2
curl -sS -o /dev/null -w "health %{http_code}\n"     http://127.0.0.1:5000/api/v1/health
curl -sS -o /dev/null -w "health/db %{http_code}\n"  http://127.0.0.1:5000/api/v1/health/db
```

### Frontend (paths reales VPS)

IMPORTANTE: Los valores `EXPO_PUBLIC_*` son **build-time**. Cualquier cambio en `.env` requiere `rm -rf dist` + rebuild. No hagas solo `pm2 restart eldojo-mobile` sin rebuild. Ese es el error #1 que causa "login apunta a :5001", "API_URL vieja" o loop en el navegador después de un deploy.

```bash
cd /eldojo/eldojo-front

# 1) Verificar .env antes de pull (por si hay diffs)
cat .env

# 2) Pull del repo
git fetch origin
git pull origin main     # o master

# 3) Re-validar .env DESPUES del pull (no queremos que git overwrote uno custom con uno de example,
#    aunque idealmente este en .gitignore).
echo "EXPO vars en el build que viene:"
grep -E '^EXPO_PUBLIC_' .env
# Deben verse los 3 (o al menos API_URL + los dos origins)
# EXPO_PUBLIC_API_URL=https://eldojo.tech/api/v1
# EXPO_PUBLIC_PUBLIC_WEB_ORIGIN=https://eldojo.tech
# EXPO_PUBLIC_APP_WEB_ORIGIN=https://app.eldojo.tech

# 4) BORRAR dist viejo y rebuild (obligatorio cada deploy front)
rm -rf dist
npm ci
npx expo export --platform web
# Confirmar fecha build:
ls -la dist/index.html

# 5) Reload pm2 (mejor que restart; no cambia PID y preserva logs)
pm2 reload eldojo-mobile
pm2 save

# 6) Smoke del server estático
pm2 list | grep eldojo-mobile
sleep 1
FRONT_PORT=$(ss -ltnp | awk '/pm2|node|Serve.js/{split($4,a,":"); print a[length(a)]}' | head -n1)
echo "Frontend sirviendo en puerto: $FRONT_PORT"
curl -sSI "http://127.0.0.1:${FRONT_PORT}/" | head -n 5
```

**Checklist rápido POST deploy front:**
- pm2 `restarts` en `pm2 list eldojo-mobile` no aumenta solo en 1 minuto.
- `pm2 logs eldojo-mobile --lines 60` no muestra ENOENT, permisos ni errores de `index.html`.
- Ir a navegador incógnito y ejecutar los 7 puntos anti-loop de la sección 8 ("Validaciones finales").

## 11. Errores comunes

### El frontend abre pero no inicia sesion

Revisa EN ESTE ORDEN:

1. `EXPO_PUBLIC_API_URL` en el `.env` con el que hiciste el build:
   - debe terminar en `/api/v1`
   - debe ser la URL PUBLICA (no 127.0.0.1:5000, el navegador del cliente no puede llegar ahi)
   - si cambiaste la variable: borra `dist/` y re-genera `npx expo export`. No basta pm2 restart.
2. Network DevTools: mira la URL del request `POST .../auth/login`.
   - Si sale `http://localhost:5001/api/v1/auth/login` o cualquier URL vieja: **tienes un build residual**. Solución: `rm -rf dist && npx expo export --platform web && pm2 reload eldojo-mobile`.
3. `nginx` tenga bloque `location /api/` en AMBOS server_names (eldojo.tech Y app.eldojo.tech), haciendo `proxy_pass http://127.0.0.1:5000;`.
4. Backend siga vivo en `127.0.0.1:5000`: `curl http://127.0.0.1:5000/api/v1/health`.

### Login exitoso pero la pagina se recarga SIN PARAR (loop infinito)

Este bug ocurre SÓLO cuando el panel admin `/admin*` se sirve DESDE EL MISMO ORIGEN que el sitio público (single origin), y `getDomainConfig().publicWebOrigin === getDomainConfig().appWebOrigin`. El código en `AppNavigator.tsx` hace `window.location.assign(buildAppUrl("admin"))` y, al ser el mismo URL, causa un full page reload.

Soluciones (elige una):

**a) Recomendada: dual-origin (ngingx con 2 server blocks, ya incluido en la sección 7)**
- Asegúrate en `.env` del front que `EXPO_PUBLIC_PUBLIC_WEB_ORIGIN !== EXPO_PUBLIC_APP_WEB_ORIGIN`.
- En nginx, 2 bloques `server {}` separados: `server_name eldojo.tech www.eldojo.tech` y `server_name app.eldojo.tech`.
- Reinicia nginx (`nginx -t && systemctl reload nginx`), rebuild front, reload pm2.
- Luego del login, te redirige una sola vez a `app.eldojo.tech/admin` y se detiene.

**b) Si tienes que usar single-origin a la fuerza (no recomendado, sólo casos sin DNS)**
- Asegúrate de que los dos origins coincidan y luego añade lógica defensiva en el cliente (`AppNavigator.tsx` bloque `singleOriginMode` salta `assign` si ya está en `/admin*`).
- Contacta dev si necesitas añadir ese fix específico.

### `502 Bad Gateway`

Significa que `nginx` no esta alcanzando el proceso interno:

```bash
curl http://127.0.0.1:5000/api/v1/health
FRONT_PORT=$(ss -ltnp | awk '/pm2|node|Serve.js/{split($4,a,":"); print a[length(a)]}' | head -n1)
curl "http://127.0.0.1:${FRONT_PORT}/"
journalctl -u eldojo-api -n 100 --no-pager
pm2 logs --lines 80 eldojo-mobile
ss -ltnp | grep -E ':5000|:3000|node'
```

### Error de CORS (bloqueado por política de origen)

Ahora que tenemos 2 orígenes, **cualquiera de los dos puede lanzar el error si no está incluido en el BACKEND_CORS_ORIGINS**:

```bash
cd /eldojo/eldojo-api
grep BACKEND_CORS_ORIGINS .env
```

Deben aparecer al menos:
```
https://eldojo.tech,https://www.eldojo.tech,https://app.eldojo.tech,http://eldojo.tech,http://www.eldojo.tech,http://app.eldojo.tech
```
Más los de desarrollo locales (`localhost:8081`, etc.) si los usas. Falta alguno? actualiza `.env` y restart `eldojo-api`.

### `nginx -t` falla

Revisa sintaxis del archivo y conflictos server_name:

```bash
nginx -t
cat -n /etc/nginx/sites-available/eldojo
grep -rnE 'server_name.*eldojo' /etc/nginx/sites-enabled /etc/nginx/conf.d
```

### Panel `/admin` devuelve 404 / vuelve a home

Si abres `app.eldojo.tech/admin` y muestra el sitio público o 404:
- El bloque `server { server_name app.eldojo.tech ... }` quizás no existe y nginx esta cayendo en otro server default. Solución: revisar `sites-enabled`, activar el archivo de la sección 7, `nginx -t && systemctl reload nginx`.
- `getDomainConfig()` en DevTools: `window.location.hostname` debería empezar por `"app."`. Si no, nginx esta sirviendo el contenido por el server equivocado.

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

## 13. Orden recomendado de ejecucion (primera instalacion)

Hazlo en este orden. No inviertas backend/frontend.

1. Validar o migrar DB
2. Levantar backend en `127.0.0.1:5000` (systemd o nohup)
3. Probar backend con `curl :5000/api/v1/health` y `health/db`
4. Poner `.env` del front con las 3 variables `EXPO_PUBLIC_*` correctas
5. `rm -rf dist && npm ci && npx expo export --platform web`
6. Levantar frontend con `pm2 serve dist 3000 --name eldojo-mobile --spa`
7. Crear archivo `sites-available/eldojo` CON 2 SERVER BLOCKS (public + app)
8. Activar sitio, `nginx -t && systemctl reload nginx`
9. Ejecutar checklist anti-loop navegador incógnito sección 8 puntos 1..7.

## 14. Comandos de diagnostico rapido

```bash
FRONT_PORT=$(ss -ltnp | awk '/pm2|node|Serve.js/{split($4,a,":"); print a[length(a)]}' | head -n1)
echo "FRONT port detectado: $FRONT_PORT"
curl -sS -o /dev/null -w "api health %{http_code}\n" http://127.0.0.1:5000/api/v1/health
curl -sS -o /dev/null -w "api db    %{http_code}\n" http://127.0.0.1:5000/api/v1/health/db
curl -sS -o /dev/null -w "front root %{http_code}\n" "http://127.0.0.1:${FRONT_PORT}/"
pm2 list
pm2 logs --lines 80 eldojo-mobile
journalctl -u eldojo-api -n 80 --no-pager 2>/dev/null || tail -n 80 /var/log/eldojo-api.nohup.log
nginx -t
systemctl status nginx --no-pager
# Dual origin check directo:
curl -sSI http://eldojo.tech/     | head -n 3
curl -sSI http://app.eldojo.tech/ | head -n 3
```
