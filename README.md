# Лабораторна робота №1

## Розгортання Web-сервісу з автоматизацією

Цей репозиторій містить реалізацію web-сервісу `mywebapp` для лабораторної роботи №1.

## Варіант індивідуального завдання

Для цього проєкту прийнято `N = 2`.

Розрахунок варіанту:

- `V2 = (2 % 2) + 1 = 1`
- `V3 = (2 % 3) + 1 = 3`
- `V5 = (2 % 5) + 1 = 3`

Отже:

- спосіб конфігурації: аргументи командного рядка;
- тип застосунку: `Simple Inventory`;
- база даних: `MariaDB`;
- порт застосунку: `3000`.

## Призначення застосунку

`mywebapp` — це простий сервіс обліку обладнання.

Об’єкт інвентарю містить такі поля:

- `id`
- `name`
- `quantity`
- `created_at`

## Архітектура

Архітектура системи:

```text
client -> nginx -> mywebapp -> MariaDB
```

Мережеві параметри:

- `nginx`: `0.0.0.0:80`
- `mywebapp`: `127.0.0.1:3000`
- `MariaDB`: `127.0.0.1:3306`

Назовні через `nginx` доступні тільки:

- `/`
- `/items`
- `/items/<id>`

Health endpoints доступні тільки локально напряму через порт застосунку.

## Структура проєкту

```text
lab1-mywebapp/
├─ mywebapp/
├─ scripts/
├─ deploy/
├─ tests/
├─ requirements.txt
└─ README.md
```

## API

### Кореневий ендпоінт

```http
GET /
```

Кореневий ендпоінт приймає тільки `text/html` і повертає HTML-сторінку зі списком бізнес-ендпоінтів застосунку.

### Health endpoints

```http
GET /health/alive
```

Завжди повертає:

```text
OK
```

```http
GET /health/ready
```

Повертає `200 OK`, якщо застосунок успішно підключився до бази даних.

Якщо база даних недоступна, повертає `500` з коротким описом помилки.

## Бізнес-логіка

### Отримати список предметів

```http
GET /items
```

Якщо клієнт передає заголовок:

```http
Accept: application/json
```

сервіс повертає JSON-список.

Якщо клієнт передає:

```http
Accept: text/html
```

сервіс повертає просту HTML-таблицю.

### Створити новий запис

```http
POST /items
```

Поля запиту:

- `name`
- `quantity`

### Отримати детальну інформацію про предмет

```http
GET /items/<id>
```

Повертає:

- `id`
- `name`
- `quantity`
- `created_at`

Формат відповіді залежить від заголовку `Accept`.

## Приклади запитів

Перевірка головної сторінки:

```bash
curl -H 'Accept: text/html' http://127.0.0.1/
```

Перегляд списку предметів у JSON:

```bash
curl -H 'Accept: application/json' http://127.0.0.1/items
```

Створення нового запису:

```bash
curl -X POST http://127.0.0.1/items \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Laptop","quantity":3}'
```

Перегляд конкретного запису:

```bash
curl -H 'Accept: application/json' http://127.0.0.1/items/1
```

Перевірка health endpoints напряму через порт застосунку:

```bash
curl http://127.0.0.1:3000/health/alive
curl http://127.0.0.1:3000/health/ready
```

## База даних і міграції

У проєкті використовується `MariaDB`.

Скрипт міграції:

```text
scripts/migrate.py
```

Міграція виконує такі дії:

- створює таблицю `schema_migrations`;
- створює таблицю `items`;
- створює індекс `idx_items_created_at`;
- може запускатися повторно без втрати даних.

## Локальний запуск

Створення віртуального середовища:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Запуск міграції:

```bash
python scripts/migrate.py \
  --host 127.0.0.1 \
  --port 3000 \
  --db-host 127.0.0.1 \
  --db-port 3306 \
  --db-name mywebapp \
  --db-user mywebapp \
  --db-password mywebapp-secret
```

Запуск застосунку:

```bash
python -m mywebapp serve \
  --host 127.0.0.1 \
  --port 3000 \
  --db-host 127.0.0.1 \
  --db-port 3306 \
  --db-name mywebapp \
  --db-user mywebapp \
  --db-password mywebapp-secret
```

## Розгортання на Linux VM

Рекомендований базовий образ:

```text
Ubuntu Server 24.04 LTS
```

Мінімальні ресурси віртуальної машини:

- CPU: 1 vCPU
- RAM: 2 GB
- Disk: 10 GB
- Network: NAT або Bridged Adapter

Спеціальні налаштування при встановленні ОС не потрібні. Достатньо стандартної інсталяції Ubuntu Server. Бажано встановити OpenSSH Server для підключення через SSH.

## Вхід на VM

Початковий вхід виконується під користувачем, який був створений під час інсталяції Ubuntu.

Після автоматизації створюються користувачі:

- `student` — користувач для роботи з проєктом, має sudo-доступ;
- `teacher` — користувач для перевірки, має sudo-доступ;
- `operator` — користувач з обмеженим sudo-доступом;
- `mywebapp` — системний користувач, від якого запускається застосунок.

Пароль за замовчуванням для `student`, `teacher`, `operator`:

```text
12345678
```

Після першого входу пароль потрібно змінити.

## Автоматизація

Єдина точка входу для автоматичного розгортання:

```text
deploy/install.sh
```

Скрипт виконує:

1. встановлення необхідних пакетів;
2. створення користувачів;
3. створення бази даних;
4. копіювання коду застосунку;
5. створення конфігураційних файлів;
6. встановлення systemd service/socket;
7. запуск сервісу;
8. налаштування nginx;
9. створення файлу `/home/student/gradebook`;
10. блокування дефолтного користувача.

Запуск автоматизації:

```bash
chmod +x deploy/install.sh
sudo ./deploy/install.sh
```

## Systemd

Файли systemd:

```text
deploy/mywebapp.service
deploy/mywebapp.socket
```

Особливості:

- сервіс працює від користувача `mywebapp`;
- перед стартом сервісу виконується міграція бази даних;
- використовується `systemd socket activation`;
- unit-файл встановлюється за шляхом `/etc/systemd/system/mywebapp.service`.

Перевірка:

```bash
sudo systemctl status mywebapp.socket
sudo systemctl status mywebapp.service
```

## Reverse Proxy

Файл конфігурації nginx:

```text
deploy/nginx-mywebapp.conf
```

nginx:

- слухає порт `80`;
- проксіює запити на `127.0.0.1:3000`;
- віддає назовні тільки `/`, `/items`, `/items/<id>`;
- не віддає назовні `/health/*`;
- записує access log.

Перевірка nginx:

```bash
sudo nginx -t
sudo systemctl status nginx
```

## Обмеження для operator

Файл sudoers:

```text
deploy/operator-mywebapp.sudoers
```

Користувач `operator` має право виконувати тільки такі команди:

```bash
sudo systemctl start mywebapp.service
sudo systemctl stop mywebapp.service
sudo systemctl restart mywebapp.service
sudo systemctl status mywebapp.service
sudo systemctl reload nginx.service
```

Інші адміністративні команди для нього заборонені.

## Gradebook

Під час розгортання створюється файл:

```text
/home/student/gradebook
```

Вміст файлу:

```text
2
```

Це число використано для розрахунку варіанту.

## Тестування

### Перевірка сервісів

```bash
sudo systemctl status mywebapp.socket
sudo systemctl status mywebapp.service
sudo systemctl status nginx
sudo systemctl status mariadb
```

### Перевірка health endpoints

```bash
curl http://127.0.0.1:3000/health/alive
curl http://127.0.0.1:3000/health/ready
```

Очікуваний результат:

```text
OK
```

### Перевірка через nginx

Головна сторінка:

```bash
curl -H 'Accept: text/html' http://127.0.0.1/
```

Список предметів:

```bash
curl -H 'Accept: application/json' http://127.0.0.1/items
```

Створення предмета:

```bash
curl -X POST http://127.0.0.1/items \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Monitor","quantity":4}'
```

Перегляд створеного предмета:

```bash
curl -H 'Accept: application/json' http://127.0.0.1/items/1
```

### Перевірка бази даних

MariaDB повинна слухати тільки локальний інтерфейс:

```bash
ss -ltnp | grep 3306
```

Очікувано:

```text
127.0.0.1:3306
```

### Перевірка портів

```bash
ss -ltnp
```

Очікувано:

- `nginx` слухає `0.0.0.0:80`;
- `mywebapp` слухає `127.0.0.1:3000`;
- `MariaDB` слухає `127.0.0.1:3306`.

### Перевірка operator

Вхід під користувачем:

```bash
su - operator
```

Перевірка дозволених команд:

```bash
sudo systemctl status mywebapp.service
sudo systemctl restart mywebapp.service
sudo systemctl reload nginx.service
```

Перевірка забороненої команди:

```bash
sudo systemctl stop mariadb.service
```

Очікувано: команда має бути заборонена, оскільки `operator` не має права керувати MariaDB.
