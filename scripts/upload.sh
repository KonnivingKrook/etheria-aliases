#!/usr/bin/env bash
# upload.sh — Upload a gvar or alias to Avrae
#
# Usage:
#   ./scripts/upload.sh <file>           Upload as-is (production)
#   ./scripts/upload.sh <file> --test    Upload with cooldown=3 (test mode)
#
# File types:
#   *.gvar   — uploaded to /customizations/gvars/<uuid> (uuid extracted from filename)
#   *.alias  — uploaded to /customizations/aliases/<name> (name = filename without extension)

set -euo pipefail

FILE="${1:-}"
TEST_MODE=0

for arg in "$@"; do
  [[ "$arg" == "--test" ]] && TEST_MODE=1
done

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Usage: ./scripts/upload.sh <file> [--test]"
  exit 1
fi

TOKEN=$(jq -r '."avrae.token"' ~/Library/Application\ Support/Code/User/settings.json 2>/dev/null)
if [[ -z "$TOKEN" ]]; then
  echo "Error: Could not read avrae.token from VS Code settings."
  exit 1
fi

BASENAME=$(basename "$FILE")
EXT="${BASENAME##*.}"

# Write content to a temp file, applying test substitution if needed
TMPFILE=$(mktemp /tmp/avrae_upload.XXXXXX)
trap 'rm -f "$TMPFILE"' EXIT

if [[ "$TEST_MODE" == 1 ]]; then
  python3 - "$FILE" <<'PYEOF'
import sys, re
text = open(sys.argv[1]).read()
text = re.sub(r'^(cooldown = int\(cfg\.get\([^)]+\)\))', r'# \1', text, flags=re.MULTILINE)
text = re.sub(r'^# (cooldown = int\(3\))', r'\1', text, flags=re.MULTILINE)
sys.stdout.write(text)
PYEOF
  echo "[test mode] cooldown overridden to 3 seconds"
else
  cat "$FILE"
fi > "$TMPFILE"

if [[ "$EXT" == "gvar" ]]; then
  UUID=$(echo "$BASENAME" | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
  if [[ -z "$UUID" ]]; then
    echo "Error: Could not extract UUID from filename: $BASENAME"
    exit 1
  fi
  STATUS=$(python3 -c "
import json, sys
payload = json.dumps({'value': open('$TMPFILE').read()})
sys.stdout.write(payload)
" | curl -s -o /dev/null -w "%{http_code}" -X POST \
    "https://api.avrae.io/customizations/gvars/${UUID}" \
    -H "Authorization: $TOKEN" \
    -H "Content-Type: application/json" \
    -d @-)
  echo "$STATUS $BASENAME"

elif [[ "$EXT" == "alias" ]]; then
  ALIAS_NAME="${BASENAME%.*}"
  FULL_PAYLOAD=$(curl -s "https://api.avrae.io/customizations" \
    -H "Authorization: $TOKEN" \
    | python3 -c "
import json, sys
data = json.load(sys.stdin)
alias = next((a for a in data['aliases'] if a['name'] == '${ALIAS_NAME}'), None)
if not alias:
    import sys; print('NOT_FOUND', end=''); sys.exit(1)
alias['commands'] = open('${TMPFILE}').read()
print(json.dumps(alias), end='')
")
  if [[ "$FULL_PAYLOAD" == "NOT_FOUND" ]]; then
    echo "Error: alias '${ALIAS_NAME}' not found in your Avrae customizations."
    exit 1
  fi
  STATUS=$(echo "$FULL_PAYLOAD" | curl -s -o /dev/null -w "%{http_code}" -X POST \
    "https://api.avrae.io/customizations/aliases/${ALIAS_NAME}" \
    -H "Authorization: $TOKEN" \
    -H "Content-Type: application/json" \
    -d @-)
  echo "$STATUS $BASENAME"

else
  echo "Error: unsupported file type '.${EXT}'. Expected .gvar or .alias"
  exit 1
fi
