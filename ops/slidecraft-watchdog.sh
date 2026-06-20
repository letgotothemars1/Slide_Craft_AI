#!/usr/bin/env bash
set -euo pipefail

# Watchdog ресурсов сервера: проверяет Disk / RAM / CPU и шлёт алерт в Telegram
# при превышении порога. Защита от спама через state-флаги: один алерт на инцидент
# + сообщение о восстановлении. Запускается по cron каждые 5 минут.
# Деплой: /usr/local/bin/slidecraft-watchdog.sh

# --- настройки ---
ENV_FILE="/var/www/slidecraft/.env"
STATE_DIR="/var/lib/slidecraft-watchdog"
DISK_MAX=85   # порог занятости диска, %
RAM_MAX=85    # порог использования памяти, %
CPU_MAX=90    # порог нагрузки CPU (5-мин load / ядра), %

# --- читаем токен и chat_id (только их, не трогаем остальной .env) ---
ALERTS_BOT_TOKEN=$(grep -E '^ALERTS_BOT_TOKEN=' "$ENV_FILE" | cut -d= -f2- || true)
ALERTS_CHAT_ID=$(grep -E '^ALERTS_CHAT_ID=' "$ENV_FILE" | cut -d= -f2- || true)
if [ -z "$ALERTS_BOT_TOKEN" ] || [ -z "$ALERTS_CHAT_ID" ]; then
  echo "Missing ALERTS_BOT_TOKEN or ALERTS_CHAT_ID in $ENV_FILE" >&2
  exit 1
fi

# --- отправка сообщения в Telegram ---
send() {
  curl -fsS --max-time 15 \
    --data-urlencode "chat_id=${ALERTS_CHAT_ID}" \
    --data-urlencode "text=$1" \
    "https://api.telegram.org/bot${ALERTS_BOT_TOKEN}/sendMessage" >/dev/null || true
}

# --- считаем метрики ---
disk=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')
ram=$(free | awk '/^Mem:/ {printf "%d", ($2-$7)/$2*100}')
cores=$(nproc)
load5=$(awk '{print $2}' /proc/loadavg)
cpu=$(awk -v l="$load5" -v c="$cores" 'BEGIN{printf "%d", l/c*100}')

# --- ручной тест: ./slidecraft-watchdog.sh --test ---
if [ "${1:-}" = "--test" ]; then
  send "🔔 SlideCraft watchdog: тест. Диск ${disk}%, Память ${ram}%, CPU ${cpu}%"
  echo "test sent: disk=${disk}% ram=${ram}% cpu=${cpu}%"
  exit 0
fi

# --- проверка с защитой от спама (state-флаги) ---
mkdir -p "$STATE_DIR"
check() {
  local name="$1" value="$2" max="$3" label="$4"
  local flag="${STATE_DIR}/${name}.alerted"
  if [ "$value" -ge "$max" ]; then
    if [ ! -f "$flag" ]; then
      send "🚨 SlideCraft ($(hostname)): ${label} ${value}% — порог ${max}%"
      touch "$flag"
    fi
  else
    if [ -f "$flag" ]; then
      send "✅ SlideCraft ($(hostname)): ${label} в норме — ${value}%"
      rm -f "$flag"
    fi
  fi
}

check disk "$disk" "$DISK_MAX" "Диск"
check ram  "$ram"  "$RAM_MAX"  "Память"
check cpu  "$cpu"  "$CPU_MAX"  "CPU"
