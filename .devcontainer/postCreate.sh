#!/usr/bin/env bash
# PodWave — post-creación del codespace (definido en devcontainer.json).
# Se ejecuta UNA sola vez al crear el contenedor y deja el proyecto listo:
# dependencias de sistema, venv, requirements, .env (local, nunca se sube),
# migraciones y datos de demostración. Después solo queda `runserver`.
set -euo pipefail

cd "$(dirname "$0")/.."   # raíz del proyecto (donde vive manage.py)

echo "== [1/5] Dependencias del sistema para compilar mysqlclient =="
sudo apt-get update -qq
sudo apt-get install -y -qq default-libmysqlclient-dev pkg-config build-essential

echo "== [2/5] Entorno virtual + requirements =="
if [ ! -d venv ]; then python3 -m venv venv; fi
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt --quiet

if [ ! -f .env ]; then
    echo "== [3/5] Creando .env local (nunca se sube al repositorio) =="
    # token_urlsafe produce SOLO [A-Za-z0-9_-]: una clave igual de segura
    # pero sin caracteres que rompan el parseo posterior de .env en bash.
    CLAVE=$(./venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > .env <<EOF
# Generado automáticamente por .devcontainer/postCreate.sh (solo desarrollo)
DJANGO_SECRET_KEY=${CLAVE}
DJANGO_DEBUG=True
DB_NAME=podwave
DB_USER=podwave_user
DB_PASSWORD=podwave_dev
DB_HOST=db
DB_PORT=3306
EOF
else
    echo "== [3/5] .env ya existe: se respeta tal cual =="
fi

echo "== [4/5] Esperando a MySQL (servicio db del compose) =="
# La prueba de conexión la hace el PROPIO settings.py del proyecto (que
# carga .env con su parser robusto): NO se hace "sourcing" de .env en
# bash, porque una clave con caracteres como ( ) & rompería el script.
export DJANGO_SETTINGS_MODULE=django_project.settings
i=0
until ./venv/bin/python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    i=$((i + 1))
    if [ "$i" -ge 30 ]; then
        echo "ERROR: MySQL no respondió tras 60 segundos; revisa el servicio db."
        exit 1
    fi
    sleep 2
done

echo "== [5/5] Migraciones + datos de demostración (seed_demo) =="
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_demo

echo
echo "CONTENEDOR LISTO. Siguiente paso:"
echo "    source venv/bin/activate   # activa el entorno virtual (importante)"
echo "    python manage.py runserver"
echo "Abre el puerto 8000 cuando VS Code lo notifique (o http://127.0.0.1:8000)."
echo "Usuario de prueba: demo / demo1234"
