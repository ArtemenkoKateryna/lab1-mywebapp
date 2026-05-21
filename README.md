# Лабораторна робота №1
## Розгортання Web-сервісу з автоматизацією

Цей репозиторій містить реалізацію web-сервісу `mywebapp` для лабораторної роботи №1.

## Варіант індивідуального завдання

Для цього проєкту прийнято `N = 2`.

Обчислення:

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

Кожен запис інвентарю містить:

- `id`
- `name`
- `quantity`
- `created_at`

## Архітектура системи

Усі компоненти розгортаються на одній Linux VM.

Схема роботи:

`client -> nginx -> mywebapp -> MariaDB`

Мережеві параметри:

- `nginx`: `0.0.0.0:80`
- `mywebapp`: `127.0.0.1:3000`
- `MariaDB`: `127.0.0.1:3306`

Назовні через `nginx` доступні тільки:

- `/`
- `/items`
- `/items/<id>`

Ендпоінти `/health/alive` і `/health/ready` використовуються для перевірки стану сервісу.

## Структура проєкту

```text
lab1-mywebapp/
├─ mywebapp/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ application.py
│  ├─ cli.py
│  ├─ config.py
│  ├─ database.py
│  └─ server.py
├─ scripts/
│  └─ migrate.py
├─ deploy/
│  ├─ install.sh
│  ├─ mywebapp.service
│  ├─ mywebapp.socket
│  ├─ nginx-mywebapp.conf
│  └─ operator-mywebapp.sudoers
├─ tests/
├─ requirements.txt
└─ README.md
