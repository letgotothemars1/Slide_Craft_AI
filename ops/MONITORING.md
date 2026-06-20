# Мониторинг production (slidecraft.org)

Три независимых уровня наблюдения. Алерты по ресурсам и бэкапам шлются в **отдельного
admin-бота** в Telegram (не в пользовательского `@Slide_craft_AI_Bot`).

| Уровень | Что ловит | Чем |
|---------|-----------|-----|
| Внешний uptime | сайт целиком недоступен, истёк SSL | UptimeRobot — HEAD `/health` каждые 5 мин |
| Ресурсы сервера | переполнение диска, утечка памяти, перегрузка CPU | `slidecraft-watchdog.sh` (cron `*/5`) |
| Бэкапы БД | ночной `pg_dump` перестал создаваться / битый | `slidecraft-backup-check.sh` (cron `0 9`) |

Внешний UptimeRobot нужен потому, что если сервер ляжет целиком — локальные cron-скрипты
тоже не отработают. Локальные скрипты ловят «тихую» деградацию, которую снаружи не видно.

## Переменные в `/var/www/slidecraft/.env`

- `ALERTS_BOT_TOKEN` — токен admin-бота для алертов
- `ALERTS_CHAT_ID` — chat_id получателя алертов

## Файлы и их место на сервере

| Файл в репо | Путь на сервере |
|-------------|-----------------|
| `ops/slidecraft-watchdog.sh` | `/usr/local/bin/slidecraft-watchdog.sh` |
| `ops/slidecraft-backup-check.sh` | `/usr/local/bin/slidecraft-backup-check.sh` |
| `ops/slidecraft-backup` | `/etc/cron.daily/slidecraft-backup` (без расширения — иначе `run-parts` его игнорирует) |

## Установка / обновление на сервере

```bash
cd /var/www/slidecraft
git pull origin feat/product-analytics-dashboard

install -m 755 ops/slidecraft-watchdog.sh     /usr/local/bin/slidecraft-watchdog.sh
install -m 755 ops/slidecraft-backup-check.sh  /usr/local/bin/slidecraft-backup-check.sh
install -m 755 ops/slidecraft-backup           /etc/cron.daily/slidecraft-backup

# cron (идемпотентно: удаляет старые строки и ставит заново)
( crontab -l 2>/dev/null | grep -v 'slidecraft-watchdog\|slidecraft-backup-check'
  echo "*/5 * * * * /usr/local/bin/slidecraft-watchdog.sh >/dev/null 2>&1"
  echo "0 9 * * * /usr/local/bin/slidecraft-backup-check.sh >/dev/null 2>&1"
) | crontab -
```

## Пороги (правятся в начале скриптов)

- `slidecraft-watchdog.sh` — `DISK_MAX`, `RAM_MAX`, `CPU_MAX`
- `slidecraft-backup-check.sh` — `MIN_SIZE` (минимальный нормальный размер дампа)

## Ручная проверка

```bash
/usr/local/bin/slidecraft-watchdog.sh --test     # тестовое сообщение в Telegram
/usr/local/bin/slidecraft-backup-check.sh         # проверка сегодняшнего бэкапа
```

## Бэкапы БД

- `pg_dump` (PostgreSQL client 17) дампит прод-БД (Supabase) в `/var/backups/slidecraft/db-YYYYMMDD.sql.gz`
- Ротация: дампы старше 7 дней удаляются
- Запуск: `/etc/cron.daily/` (система запускает в ~06:25)
