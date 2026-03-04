#!/usr/bin/env bash
set -euo pipefail

# Edita estos valores:
REMOTE_USER="ignacio"
REMOTE_HOST="192.168.0.101"
REMOTE_PORT="22"
REMOTE_DIR="/home/ignacio"
REMOTE_GUNICORN_SERVICE="gunicorn"
USE_SUDO_FOR_RESTART="1"

REPO_DIR="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_DIR")"

if [[ "$REMOTE_HOST" == "TU_IP" || "$REMOTE_USER" == "TU_USUARIO" || "$REMOTE_DIR" == "/ruta/remota/destino" ]]; then
  echo "[post-commit-scp] Configura REMOTE_USER, REMOTE_HOST y REMOTE_DIR en scripts/post-commit-scp.sh"
  exit 0
fi

# Crea carpeta remota y copia el repo completo con scp.
ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "mkdir -p '$REMOTE_DIR'"
scp -P "$REMOTE_PORT" -r "$REPO_DIR" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Reinicia gunicorn remoto tras copiar (sin prompt de password).
# Requiere NOPASSWD si USE_SUDO_FOR_RESTART="1".
if [[ "$USE_SUDO_FOR_RESTART" == "1" ]]; then
  ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" \
    "sudo -n systemctl restart '$REMOTE_GUNICORN_SERVICE'" || {
      echo "[post-commit-scp] ERROR: restart requiere password de sudo."
      echo "[post-commit-scp] Configura NOPASSWD para systemctl restart $REMOTE_GUNICORN_SERVICE o cambia USE_SUDO_FOR_RESTART=0."
      exit 1
    }
else
  ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" \
    "systemctl --user restart '$REMOTE_GUNICORN_SERVICE'" || {
      echo "[post-commit-scp] ERROR: no se pudo reiniciar con systemctl --user."
      exit 1
    }
fi

echo "[post-commit-scp] Repo copiado a $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/$REPO_NAME"
echo "[post-commit-scp] Gunicorn reiniciado: $REMOTE_GUNICORN_SERVICE"
