#!/usr/bin/env bash
# ============================================================
# Backup PRE-SPLIT - ElDojo (VPS Ubuntu)
# Fecha: 2026-08-29
# Objetivo: Copia de seguridad COMPLETA de la VPS antes del split
#           - Aplicacion backend + data + .env
#           - Sitios Nginx + certbot
#           - Units systemd
#           - Home del usuario con scripts
# Uso (como root en el VPS):
#   chmod +x backup-vps-pre-split.sh
#   ./backup-vps-pre-split.sh
# ============================================================

set -euo pipefail

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="/root/backups/pre-split-${TIMESTAMP}"
OUTPUT_TAR="/root/backups/eldojo-vps-pre-split-${TIMESTAMP}.tar.gz"

echo "==========================================="
echo "ElDojo VPS - Backup PRE-SPLIT"
echo "Timestamp: ${TIMESTAMP}"
echo "==========================================="
echo ""

# -- Usuario --
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse como root (sudo su -)." >&2
    exit 1
fi

# 1) Preparar rutas
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${OUTPUT_TAR}")"

# 2) Snapshot estado servicios (antes de parar nada)
echo ">> [1/8] Guardando estado de servicios..."
mkdir -p "${BACKUP_DIR}/system-state"
systemctl list-units --type=service --state=running > "${BACKUP_DIR}/system-state/services-running.txt" 2>&1 || true
ss -ltnp > "${BACKUP_DIR}/system-state/ss-ltnp.txt" 2>&1 || true
df -h > "${BACKUP_DIR}/system-state/df-h.txt" 2>&1 || true
free -m > "${BACKUP_DIR}/system-state/free-m.txt" 2>&1 || true
ps auxf --sort=-%mem | head -30 > "${BACKUP_DIR}/system-state/ps-top-mem.txt" 2>&1 || true
nginx -T > "${BACKUP_DIR}/system-state/nginx-T.txt" 2>&1 || true
echo "   OK"

# 3) Backup /eldojo (apps + data + .envs). Excluir carpetas runtime grandes
echo ">> [2/8] Backup /eldojo (apps + data + .env)..."
rsync -aR --delete \
    --exclude='/eldojo/*/node_modules' \
    --exclude='/eldojo/*/.venv' \
    --exclude='/eldojo/*/venv' \
    --exclude='/eldojo/*/dist' \
    --exclude='/eldojo/*/.next' \
    --exclude='/eldojo/*/.expo' \
    --exclude='/__pycache__' \
    /eldojo/./ "${BACKUP_DIR}/fs-root/eldojo/"
echo "   OK"

# 4) Backup nginx sitios + configs globales
echo ">> [3/8] Backup Nginx..."
mkdir -p "${BACKUP_DIR}/fs-root/etc/nginx"
if [ -d /etc/nginx ]; then
    cp -a /etc/nginx/sites-available "${BACKUP_DIR}/fs-root/etc/nginx/" 2>/dev/null || true
    cp -a /etc/nginx/sites-enabled   "${BACKUP_DIR}/fs-root/etc/nginx/" 2>/dev/null || true
    cp -a /etc/nginx/nginx.conf      "${BACKUP_DIR}/fs-root/etc/nginx/" 2>/dev/null || true
    cp -a /etc/nginx/conf.d          "${BACKUP_DIR}/fs-root/etc/nginx/" 2>/dev/null || true
fi
echo "   OK"

# 5) Backup Certbot / Letsencrypt
echo ">> [4/8] Backup Letsencrypt..."
mkdir -p "${BACKUP_DIR}/fs-root/etc"
if [ -d /etc/letsencrypt ]; then
    cp -a /etc/letsencrypt "${BACKUP_DIR}/fs-root/etc/"
fi
echo "   OK"

# 6) Backup units systemd (eldojo-api, pm2, etc.)
echo ">> [5/8] Backup systemd units..."
mkdir -p "${BACKUP_DIR}/fs-root/etc/systemd/system"
if [ -d /etc/systemd/system ]; then
    find /etc/systemd/system \
        \( -name 'eldojo*.service' -o -name 'pm2*.service' -o -name 'gunicorn*.service' \) \
        -exec cp -a {} "${BACKUP_DIR}/fs-root/etc/systemd/system/" \;
fi
echo "   OK"

# 7) Backup home (scripts deploy, ssh config, crontab)
echo ">> [6/8] Backup home root + usuario + crontabs..."
for H in /root /home/*; do
    [ -d "$H" ] || continue
    D="${BACKUP_DIR}/fs-root${H}"
    mkdir -p "$D"
    rsync -a --exclude='*/node_modules' --exclude='*/.venv' \
        "$H/.ssh/" "$D/.ssh/" 2>/dev/null || true
    cp -a "$H/."bashrc "$D/" 2>/dev/null || true
    cp -a "$H/."profile "$D/" 2>/dev/null || true
    cp -a "$H/scripts" "$D/" 2>/dev/null || true
    cp -a "$H/update-api.sh" "$D/" 2>/dev/null || true
done
# Crontabs
mkdir -p "${BACKUP_DIR}/fs-root/var/spool/cron/crontabs"
cp -a /var/spool/cron/crontabs/* "${BACKUP_DIR}/fs-root/var/spool/cron/crontabs/" 2>/dev/null || true
crontab -l -u root > "${BACKUP_DIR}/system-state/crontab-root.txt" 2>/dev/null || true
echo "   OK"

# 8) PostgreSQL dump de la base de datos (si existe)
echo ">> [7/8] Backup base de datos PostgreSQL (pg_dump si existe)..."
mkdir -p "${BACKUP_DIR}/db-dump"
# Si existe la variable DATABASE_URL en .env backend
if [ -f /eldojo/eldojo-api/.env ] && command -v pg_dump >/dev/null 2>&1; then
    set -a
    # shellcheck disable=SC1091
    source /eldojo/eldojo-api/.env 2>/dev/null || true
    set +a
    if [ -n "${DATABASE_URL:-}" ]; then
        echo "   DATABASE_URL detectada. Ejecutando pg_dump..."
        pg_dump "${DATABASE_URL}" -F c -f "${BACKUP_DIR}/db-dump/eldojo-${TIMESTAMP}.dump" || true
        echo "   Dump SQL: ${BACKUP_DIR}/db-dump/eldojo-${TIMESTAMP}.dump"
    else
        echo "   (No DATABASE_URL en .env de eldojo-api, skip)"
    fi
else
    echo "   (pg_dump no disponible o falta .env, skip)"
fi
echo "   OK"

# 9) Crear tar.gz comprimido
echo ">> [8/8] Creando tar.gz final..."
tar -czf "${OUTPUT_TAR}" -C "${BACKUP_DIR}" .
TAR_SIZE_MB="$(du -m "${OUTPUT_TAR}" | awk '{print $1}')"

echo ""
echo "==========================================="
echo "Backup VPS COMPLETADO."
echo "Ruta:        ${OUTPUT_TAR}"
echo "Taman~o:     ${TAR_SIZE_MB} MB"
echo "Recomendacion: descargar este tar.gz SCP a local."
echo "   scp root@eldojo.tech:${OUTPUT_TAR} ."
echo "==========================================="

# Check size minimo
if [ "${TAR_SIZE_MB}" -lt 100 ]; then
    echo ""
    echo "! ADVERTENCIA: El backup pesa < 100MB. Probablemente falte contenido." >&2
    echo "! Revisar ${BACKUP_DIR} antes de continuar." >&2
    exit 2
fi
