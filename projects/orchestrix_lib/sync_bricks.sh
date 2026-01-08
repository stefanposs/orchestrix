#!/bin/bash
# Synchronizes all Bricks (components/orchestrix/) recursively into the local orchestrix/ directory
# Run before build!

set -e

BRICKS_DIR="$(dirname "$0")/../../components/orchestrix"
TARGET_DIR="$(dirname "$0")/orchestrix"

# Ensure orchestrix directory exists
mkdir -p "$TARGET_DIR"

# Ensure py.typed exists in orchestrix
if [ ! -f "$TARGET_DIR/py.typed" ]; then
  touch "$TARGET_DIR/py.typed"
fi

if [ ! -d "$BRICKS_DIR" ]; then
  echo "Bricks directory $BRICKS_DIR does not exist!"
  exit 1
fi

# Clean target directory (except __init__.py and py.typed)
find "$TARGET_DIR" -type f \( ! -name '__init__.py' ! -name 'py.typed' \) -delete
find "$TARGET_DIR" -type d -mindepth 1 -empty -delete

# Copy Bricks recursively (including subfolders)
rsync -a "$BRICKS_DIR"/ "$TARGET_DIR"/

# Ensure orchestrix is not git-relevant
GITIGNORE_FILE="$(dirname "$0")/.gitignore"
if ! grep -q '^orchestrix/$' "$GITIGNORE_FILE" 2>/dev/null; then
  echo 'orchestrix/' >> "$GITIGNORE_FILE"
fi

echo "All Bricks from $BRICKS_DIR synchronized to $TARGET_DIR."
