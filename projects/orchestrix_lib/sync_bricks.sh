#!/bin/bash
# Synchronisiert alle Bricks (components/orchestrix/) rekursiv ins lokale orchestrix/-Verzeichnis
# Vor dem Build ausführen!

set -e

BRICKS_DIR="$(dirname "$0")/../../components/orchestrix"
TARGET_DIR="$(dirname "$0")/orchestrix"

if [ ! -d "$BRICKS_DIR" ]; then
  echo "Bricks-Verzeichnis $BRICKS_DIR existiert nicht!"
  exit 1
fi

# Zielverzeichnis leeren (außer __init__.py und py.typed)
find "$TARGET_DIR" -type f \( ! -name '__init__.py' ! -name 'py.typed' \) -delete
find "$TARGET_DIR" -type d -mindepth 1 -empty -delete

# Bricks rekursiv kopieren (inkl. Unterordner)
rsync -a "$BRICKS_DIR"/ "$TARGET_DIR"/

echo "Alle Bricks aus $BRICKS_DIR nach $TARGET_DIR synchronisiert."
