#!/usr/bin/env bash
set -euo pipefail

# Configuración de rutas
DEST_DIR="$HOME/WebStorm/pegaReact/copiaBackend"
REPO_DIR="$(git rev-parse --show-toplevel)"

echo "[post-commit-local] Sincronizando con $DEST_DIR..."

# Crear el directorio de destino si no existe
mkdir -p "$DEST_DIR"

# Sincronizar archivos excluyendo carpetas innecesarias
rsync -av --delete \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='.idea/' \
    --exclude='.pytest_cache/' \
    "$REPO_DIR/" "$DEST_DIR/"

echo "[post-commit-local] Sincronización completada con éxito."
