# AI Task Capture System

**AI Task Capture System** — персональна система для фіксації, ведення, контролю та аналізу робочих задач.

Проєкт створюється не як курсова “для галочки”, а як реальний інструмент для щоденної роботи. Ідея системи: швидко записати або надиктувати задачу українською мовою, отримати структурований preview змін, підтвердити його і тільки після цього записати задачу в базу.

Поточний фокус MVP:

* стабільний backend;
* PostgreSQL як основне сховище;
* запуск через Docker Compose;
* безпечний сценарій `preview → confirm → write`;
* автоматичний розрахунок статусу задачі;
* автоматична оцінка задачі;
* історія змін задач;
* українська документація;
* можливість локальної перевірки без ручного налаштування PostgreSQL.

---

## 1. Основна ідея

Система має допомагати швидко фіксувати робочі задачі, які раніше велися в Excel.

Базовий сценарій:

```text
Користувач вводить або диктує задачу
→ система формує structured preview
→ користувач перевіряє зміни
→ користувач підтверджує
→ backend записує зміни в PostgreSQL
→ backend зберігає історію змін
```

Важливий принцип:

```text
Жодна важлива зміна не записується одразу.
Спочатку preview, потім confirmation, тільки потім write.
```

---

## 2. Архітектура MVP

Поточна архітектура:

```text
Користувач / Swagger UI
        ↓
FastAPI backend
        ↓
Business services
        ↓
PostgreSQL
        ↓
Adminer для перегляду даних
```

Docker Compose піднімає такі сервіси:

| Сервіс    | Призначення               |
| --------- | ------------------------- |
| `backend` | FastAPI application       |
| `db`      | PostgreSQL database       |
| `adminer` | Web UI для перегляду бази |

---

## 3. Технології

| Компонент   | Технологія             |
| ----------- | ---------------------- |
| Backend     | Python 3.12, FastAPI   |
| Database    | PostgreSQL 16          |
| ORM         | SQLAlchemy 2           |
| Migrations  | Alembic                |
| Validation  | Pydantic               |
| Tests       | Pytest                 |
| Containers  | Docker, Docker Compose |
| DB Admin UI | Adminer                |

---

## 4. Структура проєкту

```text
AI Task Capture System/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── dictionaries.py
│   │   ├── task.py
│   │   ├── task_event.py
│   │   └── task_preview.py
│   ├── routers/
│   │   ├── dicts.py
│   │   ├── health.py
│   │   └── tasks.py
│   ├── schemas/
│   │   ├── dictionaries.py
│   │   ├── task.py
│   │   └── task_event.py
│   ├── services/
│   │   ├── event_service.py
│   │   ├── preview_service.py
│   │   ├── score_service.py
│   │   └── status_service.py
│   └── utils/
├── migrations/
├── scripts/
│   └── seed_dictionaries.py
├── tests/
│   ├── test_app_import.py
│   ├── test_score_service.py
│   └── test_status_service.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 5. Запуск через Docker Compose

### 5.1. Запустити сервіси

```powershell
docker compose up -d --build
```

### 5.2. Перевірити статус контейнерів

```powershell
docker compose ps
```

Очікувані сервіси:

```text
ai-task-capture-system-backend
ai-task-capture-system-db
ai-task-capture-system-adminer
```

### 5.3. Переглянути логи backend

```powershell
docker compose logs -f backend
```

### 5.4. Зупинити сервіси

```powershell
docker compose down
```

### 5.5. Зупинити сервіси і видалити дані PostgreSQL

```powershell
docker compose down -v
```

Увага: команда з `-v` видаляє Docker volume з даними PostgreSQL.

---

## 6. Корисні URL

| Що           | URL                          |
| ------------ | ---------------------------- |
| FastAPI root | http://localhost:8000        |
| Swagger UI   | http://localhost:8000/docs   |
| Health check | http://localhost:8000/health |
| Adminer      | http://localhost:8080        |

---

## 7. Підключення до Adminer

Відкрити:

```text
http://localhost:8080
```

Параметри підключення:

| Поле     | Значення        |
| -------- | --------------- |
| System   | PostgreSQL      |
| Server   | db              |
| Username | task_user       |
| Password | task_password   |
| Database | task_capture_db |

---

## 8. Міграції бази даних

Проєкт використовує Alembic.

### 8.1. Застосувати всі міграції

```powershell
python -m alembic upgrade head
```

### 8.2. Перевірити поточну міграцію

```powershell
python -m alembic current
```

### 8.3. Переглянути історію міграцій

```powershell
python -m alembic history
```

---

## 9. Seed довідників

Після створення таблиць потрібно заповнити довідники:

```powershell
python -m scripts.seed_dictionaries
```

Скрипт заповнює:

| Таблиця             | Очікувана кількість записів |
| ------------------- | --------------------------: |
| `priority_dict`     |                           4 |
| `complexity_dict`   |                           4 |
| `task_type_dict`    |                           4 |
| `task_score_matrix` |                          16 |

Скрипт можна запускати повторно. Він оновлює існуючі записи, а не дублює їх.

---

## 10. Основні таблиці

### `tasks`

Основна таблиця задач.

Ключові поля:

| Поле                       | Призначення                                    |
| -------------------------- | ---------------------------------------------- |
| `task_title`               | Назва задачі                                   |
| `goal`                     | Ціль задачі                                    |
| `task_type_id`             | Тип задачі                                     |
| `business_area`            | Бізнес-напрям                                  |
| `customer`                 | Замовник                                       |
| `auto_status`              | Автоматично розрахований статус                |
| `priority_id`              | Пріоритет                                      |
| `complexity_id`            | Складність                                     |
| `auto_task_score`          | Автоматична оцінка задачі                      |
| `executor`                 | Виконавець                                     |
| `planned_finish_date`      | Планова дата виконання                         |
| `fact_start_date`          | Фактичний старт                                |
| `fact_finish_date`         | Фактичне завершення                            |
| `fact_hours`               | Фактично витрачені години                      |
| `short_status_description` | Короткий опис статусу                          |
| `source_text`              | Початковий текст користувача                   |
| `ai_confidence`            | Впевненість AI, буде використовуватись пізніше |

### `task_events`

Таблиця історії змін задач.

Використовується для audit trail:

```text
хто змінив
що змінив
старе значення
нове значення
коли змінив
з якого джерела
```

### `task_previews`

Таблиця попередніх змін перед підтвердженням.

Саме вона забезпечує сценарій:

```text
preview → confirm → write
```

---

## 11. Довідники

### Пріоритети

| Code       | Name     | Коефіцієнт |
| ---------- | -------- | ---------: |
| `critical` | Critical |       1.00 |
| `high`     | High     |       0.80 |
| `medium`   | Medium   |       0.60 |
| `low`      | Low      |       0.50 |

### Складність

| Code           | Name         | Коефіцієнт |
| -------------- | ------------ | ---------: |
| `very_complex` | Very Complex |       3.00 |
| `complex`      | Complex      |       2.00 |
| `moderate`     | Moderate     |       1.50 |
| `easy`         | Easy         |       1.00 |

### Типи задач

| Code           | Name       | Базовий час |
| -------------- | ---------- | ----------: |
| `db_reports`   | БД/Звіти   |           5 |
| `pbi_reports`  | Звіти PBI  |           8 |
| `requests`     | Запити     |           3 |
| `ssrs_reports` | Звіти SSRS |           5 |

---

## 12. Логіка автостатусу

Автостатус розраховується backend-ом, а не AI.

Правила:

| Умова                                      | Статус     |
| ------------------------------------------ | ---------- |
| Є `fact_finish_date`                       | `Виконано` |
| Немає пріоритету або складності            | `Оцінка`   |
| Є пріоритет і складність, але немає старту | `Нова`     |
| `fact_start_date <= today`                 | `В роботі` |
| `fact_start_date > today`                  | `План`     |

Ця логіка реалізована в:

```text
app/services/status_service.py
```

---

## 13. Логіка автооцінки задачі

Автооціночка задачі розраховується backend-ом.

Формула:

```text
auto_task_score = task_type.base_hours × priority.coefficient × complexity.coefficient
```

Результат округлюється до найближчих `0.5` години.

Приклад:

```text
Тип задачі: Звіти PBI → 8 год
Пріоритет: High → 0.80
Складність: Complex → 2.00

8 × 0.80 × 2.00 = 12.8 → 13.00
```

Ця логіка реалізована в:

```text
app/services/score_service.py
```

---

## 14. API endpoints

### Health

```http
GET /health
```

### Довідники

```http
GET /dicts/priorities
GET /dicts/complexities
GET /dicts/task-types
GET /dicts/task-score-matrix
```

### Задачі

```http
GET /tasks
GET /tasks/{task_id}
GET /tasks/{task_id}/events
```

### Preview / Confirm

```http
POST /tasks/preview
POST /tasks/confirm
POST /tasks/{task_id}/close
```

---

## 15. Приклади API-запитів

### 15.1. Створити preview нової задачі

```powershell
$body = @{
    task_title = "Перевірити фільтри у звіті Support"
    goal = "Зрозуміти, чому друга таблиця не реагує на частину фільтрів"
    task_type_id = 2
    business_area = "IT"
    customer = "Кяшко"
    priority_id = 2
    complexity_id = 2
    executor = "Кондес П."
    planned_finish_date = "2026-06-14"
    source_text = "додай задачу по звіту сапорт, треба перевірити фільтри"
    created_by = "Кондес П."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/tasks/preview `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Очікувано:

```text
action = create_task
can_confirm = True
```

---

### 15.2. Підтвердити preview

```powershell
$body = @{
    preview_id = 1
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/tasks/confirm `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### 15.3. Закрити задачу через preview

```powershell
$body = @{
    fact_finish_date = "2026-06-11"
    fact_hours = 3
    short_status_description = "Перевірено фільтри та знайдено причину, чому друга таблиця не реагує."
    source_text = "закрий задачу по звіту Support, факт сьогодні, витратив 3 години"
    created_by = "Кондес П."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/tasks/1/close `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

### 15.4. Переглянути задачі

```powershell
Invoke-RestMethod http://localhost:8000/tasks | ConvertTo-Json -Depth 5
```

---

### 15.5. Переглянути історію змін задачі

```powershell
Invoke-RestMethod http://localhost:8000/tasks/1/events | ConvertTo-Json -Depth 5
```

---

## 16. Тести

Запуск тестів:

```powershell
python -m pytest
```

Поточний очікуваний результат:

```text
15 passed
```

Тести покривають:

* імпорт FastAPI app;
* логіку автостатусу;
* логіку автооцінки;
* округлення оцінки до `0.5` години.

---

## 17. Що вже реалізовано в MVP-core

Реалізовано:

* Docker Compose запуск;
* FastAPI backend;
* PostgreSQL;
* Adminer;
* SQLAlchemy models;
* Alembic migrations;
* seed довідників;
* API довідників;
* API читання задач;
* API перегляду історії задач;
* створення задачі через `preview → confirm`;
* закриття задачі через `preview → confirm`;
* автоматичний статус задачі;
* автоматична оцінка задачі;
* історія змін у `task_events`;
* базові тести.

---

## 18. Known limitations

Поточні обмеження MVP:

* AI parser ще не реалізований;
* Telegram bot ще не реалізований;
* немає frontend UI;
* немає авторизації;
* немає update/start/plan workflows;
* немає Excel import/export;
* немає semantic search;
* немає vector database;
* немає MCP server;
* поки що всі приклади запускаються локально;
* preview реалізований для create і close workflows.

---

## 19. Roadmap

Наступні кроки:

1. Додати `start task` workflow.
2. Додати `plan task` workflow.
3. Додати `update task` workflow.
4. Додати mock AI parser.
5. Додати structured JSON schema для AI.
6. Додати реальний AI text-to-JSON parser.
7. Додати пошук задач за текстом.
8. Додати Excel export.
9. Додати Telegram bot.
10. Додати semantic search через embeddings.
11. Підготувати гілку або тег `course-mvp`.

---

## 20. Git strategy

Робочі гілки:

```text
main        — стабільна версія
dev         — активна розробка
course-mvp  — стабільний зріз для курсу
```

Коли MVP буде готовий для здачі:

```powershell
git checkout -b course-mvp
git push -u origin course-mvp
git tag v0.1-course-mvp
git push origin v0.1-course-mvp
```

---

## 21. Поточний статус

Поточний статус:

```text
MVP-core реалізовано.
Backend запускається через Docker Compose.
База створюється через Alembic.
Довідники заповнюються seed-скриптом.
Створення і закриття задач працює через preview/confirm.
Тести проходять.
```

Наступний робочий крок:

```text
start task / plan task / update task workflows
```
