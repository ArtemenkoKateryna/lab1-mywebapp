# Лабораторна робота №1
## Розгортання Web-сервісу з автоматизацією

Цей репозиторій містить реалізацію web-сервісу `mywebapp` для лабораторної роботи №1.

## Варіант індивідуального завдання 2

Для цього проєкту прийнято `N = 2`.

- `V2 = (2 % 2) + 1 = 1`
- `V3 = (2 % 3) + 1 = 3`
- `V5 = (2 % 5) + 1 = 3`

Отже:

- спосіб конфігурації: аргументи командного рядка
- тип застосунку: `Simple Inventory`
- база даних: `MariaDB`
- порт застосунку: `3000`

## Призначення застосунку

`mywebapp` це простий сервіс обліку обладнання.

Поля запису:

- `id`
- `name`
- `quantity`
- `created_at`

## Архітектура

`client -> nginx -> mywebapp -> MariaDB`

Мережеві параметри:

- `nginx`: `0.0.0.0:80`
- `mywebapp`: `127.0.0.1:3000`
- `MariaDB`: `127.0.0.1:3306`

Назовні через `nginx` доступні тільки:

- `/`
- `/items`
- `/items/<id>`

## Структура проєкту

```text
lab1-mywebapp/
├─ mywebapp/
├─ scripts/
├─ deploy/
├─ tests/
├─ requirements.txt
└─ README.md
##API
Кореневий ендпоінт
GET /
приймає тільки text/html
повертає HTML-сторінку зі списком бізнес-ендпоінтів
Health endpoints
GET /health/alive

завжди повертає 200 OK
тіло: OK
GET /health/ready

200 OK, якщо є підключення до БД
500, якщо БД недоступна
Бізнес-логіка
GET /items

Accept: application/json -> JSON-список
Accept: text/html -> HTML-таблиця
POST /items

створює новий запис
поля: name, quantity
GET /items/<id>

Accept: application/json -> деталі в JSON
Accept: text/html -> проста HTML-сторінка
Приклади запитів
curl -H 'Accept: text/html' http://127.0.0.1/
curl -H 'Accept: application/json' http://127.0.0.1/items
curl -X POST http://127.0.0.1/items \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Laptop","quantity":3}'
curl -H 'Accept: application/json' http://127.0.0.1/items/1
curl http://127.0.0.1:3000/health/alive
curl http://127.0.0.1:3000/health/ready
База даних і міграції
Використовується MariaDB.

Скрипт міграції:

scripts/migrate.py
Міграція:

створює schema_migrations
створює items
створює індекс idx_items_created_at
запускається повторно без втрати даних
Локальний запуск
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/migrate.py \
  --host 127.0.0.1 \
  --port 3000 \
  --db-host 127.0.0.1 \
  --db-port 3306 \
  --db-name mywebapp \
  --db-user mywebapp \
  --db-password mywebapp-secret

python -m mywebapp serve \
  --host 127.0.0.1 \
  --port 3000 \
  --db-host 127.0.0.1 \
  --db-port 3306 \
  --db-name mywebapp \
  --db-user mywebapp \
  --db-password mywebapp-secret
Розгортання на Linux VM
Рекомендований образ:

Ubuntu Server 24.04 LTS
Мінімальні ресурси:

1 vCPU
2 GB RAM
10 GB Disk
Спеціальні налаштування:

стандартна інсталяція Ubuntu Server
бажано встановити OpenSSH Server
Вхід на VM
Початковий вхід виконується під користувачем, створеним під час інсталяції Ubuntu.

Після автоматизації створюються:

student — sudo-доступ
teacher — sudo-доступ
operator — обмежений sudo-доступ
mywebapp — системний користувач для сервісу
Автоматизація
Єдина точка входу:

deploy/install.sh
Скрипт:

встановлює пакети
створює користувачів
створює базу даних
копіює код
встановлює конфіги
налаштовує systemd
запускає сервіс
налаштовує nginx
створює /home/student/gradebook
блокує дефолтного користувача
Запуск:

chmod +x deploy/install.sh
sudo ./deploy/install.sh
Systemd
Файли:

deploy/mywebapp.service
deploy/mywebapp.socket
Особливості:

сервіс працює від mywebapp
перед стартом виконується міграція
використовується systemd socket activation
Reverse Proxy
Файл:

deploy/nginx-mywebapp.conf
nginx:

слухає 80
проксіює /, /items, /items/<id>
не віддає /health/*
пише access log
Обмеження для operator
Файл:

deploy/operator-mywebapp.sudoers
Дозволені тільки:

systemctl start mywebapp.service
systemctl stop mywebapp.service
systemctl restart mywebapp.service
systemctl status mywebapp.service
systemctl reload nginx.service
Gradebook
Файл:

/home/student/gradebook
Вміст:

2
Тестування
Перевірка сервісів:

sudo systemctl status mywebapp.socket
sudo systemctl status mywebapp.service
sudo systemctl status nginx
sudo systemctl status mariadb
Перевірка локально:

curl http://127.0.0.1:3000/health/alive
curl http://127.0.0.1:3000/health/ready
Перевірка через nginx:

curl -H 'Accept: text/html' http://127.0.0.1/
curl -H 'Accept: application/json' http://127.0.0.1/items
curl -X POST http://127.0.0.1/items \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Monitor","quantity":4}'
curl -H 'Accept: application/json' http://127.0.0.1/items/1
Перевірка БД:

ss -ltnp | grep 3306
Перевірка operator:

su - operator
sudo systemctl status mywebapp.service
sudo systemctl restart mywebapp.service
sudo systemctl reload nginx.service
sudo systemctl stop mariadb.service
