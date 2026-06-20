#!/usr/bin/env bash
set -euo pipefail

# Dead man's switch для бэкапа БД: проверяет, что сегодняшний дамп создан и не битый.
# Нет файла / файл подозрительно мал -> алерт в Telegram. Иначе суточное "✅ ок".
# Запускается по cron в 09:00 (бэкап делается в ~06:25, даём запас).
# Деплой: /usr/local/bin/slidecraft-backup-check.sh

ENV_FILE="/var/www/slidecraft/.env"
BACKUP_DIR="/var/backups/slidecraft"
MIN_SIZE=10240   # минимальный нормальный размер дампа, байт (10 КБ)

ALERTS_BOT_TOKEN=$(grep -E '^ALERTS_BOT_TOKEN=' "$ENV_FILE" | cut -d= -f2- || true)
ALERTS_CHAT_ID=$(grep -E '^ALERTS_CHAT_ID=' "$ENV_FILE" | cut -d= -f2- || true)
if [ -z "$ALERTS_BOT_TOKEN" ] || [ -z "$ALERTS_CHAT_ID" ]; then
  echo "Missing ALERTS_BOT_TOKEN or ALERTS_CHAT_ID in $ENV_FILE" >&2
  exit 1
fi

send() {
  curl -fsS --max-time 15 \
    --data-urlencode "chat_id=${ALERTS_CHAT_ID}" \
    --data-urlencode "text=$1" \
    "https://api.telegram.org/bot${ALERTS_BOT_TOKEN}/sendMessage" >/dev/null || true
}

FILE="${BACKUP_DIR}/db-$(date +%Y%m%d).sql.gz"
size=$(stat -c%s "$FILE" 2>/dev/null || echo 0)

if [ "$size" -lt "$MIN_SIZE" ]; then
  if [ ! -f "$FILE" ]; then
    send "🚨 SlideCraft ($(hostname)): бэкап БД за сегодня НЕ создан — $(basename "$FILE") отсутствует"
  else
    send "🚨 SlideCraft ($(hostname)): бэкап БД подозрительно мал — ${size} байт ($(basename "$FILE"))"
  fi
  exit 1
fi

# суточное подтверждение «бэкап ок» (если не нужно — удали эту строку)
hr=$(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B")
send "✅ SlideCraft ($(hostname)): бэкап БД за сегодня ок — ${hr}"
