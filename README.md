# AI Task Capture System

**AI Task Capture System** — це MVP-система для фіксації, структуризації, голосового або текстового введення, ведення, контролю та аналізу робочих задач.

Проєкт створений як навчальний AI Engineering MVP з орієнтацією на реальний робочий сценарій: швидко записати або надиктувати задачу українською мовою, отримати структурований preview змін, підтвердити його і тільки після цього записати задачу в базу.

---

## 1. Короткий опис

Основна ідея системи:

```text
text input / voice transcript
→ AI parser
→ structured payload
→ preview
→ confirm
→ PostgreSQL
→ task_events
```

Ключовий принцип:

```text
AI не пише напряму в базу.
AI тільки готує structured output.
Backend формує preview.
Користувач підтверджує.
Тільки після цього дані записуються в PostgreSQL.
```

Це робить систему більш контрольованою, прозорою та безпечною для роботи з AI-виводом.

---

## 2. Матеріали для здачі в LMS

Основні файли для перевірки:

* `README.md` — основна інструкція по проєкту, запуску, API та перевірці працездатності.
* `docs/COURSE_SUBMISSION.md` — повний опис MVP, відповідність критеріям LMS, основний сценарій роботи, обмеження та розвиток.
* `docs/RESEARCH_AND_CONCEPT.md` — дослідження проблеми, концепція, обґрунтування стеку та voice-ready scope.

Основний сценарій роботи MVP:

```text
text input / voice transcript
→ AI parser
→ structured payload
→ preview
→ confirm
→ PostgreSQL
→ task_events
```

Ключові endpoints для перевірки:

```http
POST /tasks/ai-preview
POST /tasks/voice-preview
POST /tasks/confirm
GET /tasks/{task_id}
GET /tasks/{task_id}/events
```

Швидка перевірка перед здачею:

```powershell
docker compose up -d --build
Invoke-RestMethod http://localhost:8000/health
python -m pytest
```

Очікуваний результат тестів:

```text
19 passed
```

---

## 3. Яку проблему вирішує проєкт

У щоденній роботі задачі часто виникають у неструктурованому вигляді:

* у чатах;
* у листуванні;
* у голосових командах;
* у нотатках;
* в Excel;
* у коротких повідомленнях від замовників.

Через це складно:

* швидко фіксувати задачі;
* підтримувати єдину структуру;
* контролювати статуси;
* відстежувати історію змін;
* оцінювати складність і пріоритет;
* безпечно використовувати AI для створення або зміни записів.

AI Task Capture System вирішує цю проблему через контрольований workflow:

```text
неструктурований input
→ structured preview
→ confirmation
→ database write
```

---

## 4. Основні можливості MVP

Реалізовано:

* FastAPI backend;
* PostgreSQL database;
* Docker Compose запуск;
* Adminer для перегляду БД;
* Alembic migrations;
* SQLAlchemy models;
* seed довідників;
* API довідників;
* API читання задач;
* створення задачі через `preview → confirm`;
* створення задачі з українського тексту через `POST /tasks/ai-preview`;
* створення задачі з transcript голосової команди через `POST /tasks/voice-preview`;
* task lifecycle workflows:

  * start;
  * plan;
  * pause;
  * resume;
  * update;
  * close;
* автоматичний розрахунок статусу задачі;
* автоматична оцінка задачі;
* історія змін у `task_events`;
* mock AI parser;
* тести;
* українська документація для здачі.

---

## 5. Voice-ready MVP scope

Початкова ідея проєкту включає не тільки текстове введення, а й голосове управління задачами.

Production pipeline для голосового сценарію:

```text
voice command
→ Speech-to-Text
→ transcript
→ AI parser
→ structured payload
→ preview
→ confirm
→ PostgreSQL
```

У межах поточного MVP реалізована частина після Speech-to-Text:

```text
voice transcript
→ AI parser
→ structured payload
→ preview
→ confirm
→ PostgreSQL
```

Для цього додано endpoint:

```http
POST /tasks/voice-preview
```

Важливо: MVP не приймає audio-файл напряму і не реалізує власний speech-to-text engine. Натомість система приймає вже розпізнаний transcript голосової команди. У майбутньому перед цим endpoint-ом можна підключити Whisper, OpenAI Audio API, Google Speech-to-Text або інший STT-сервіс.

---

## 6. Архітектура MVP

Поточна архітектура:

```text
User / API client / Swagger UI
        ↓
FastAPI Router
        ↓
Pydantic Schemas
        ↓
Service Layer
        ↓
Business Rules
        ↓
Preview
        ↓
Confirm
        ↓
PostgreSQL
        ↓
task_events audit trail
```

AI workflow:

```text
raw text / voice transcript
        ↓
mock AI parser
        ↓
structured payload
        ↓
TaskCreatePreviewRequest
        ↓
TaskPreview
        ↓
Confirm
        ↓
Task
        ↓
TaskEvent
```

Docker Compose піднімає такі сервіси:

| Сервіс    | Призначення               |
| --------- | ------------------------- |
| `backend` | FastAPI application       |
| `db`      | PostgreSQL database       |
| `adminer` | Web UI для перегляду бази |

---

## 7. Технології

| Компонент   | Технологія             |
| ----------- | ---------------------- |
| Backend     | Python 3.12, FastAPI   |
| Database    | PostgreSQL             |
| ORM         | SQLAlchemy             |
| Migrations  | Alembic                |
| Validation  | Pydantic               |
| Tests       | Pytest                 |
| Containers  | Docker, Docker Compose |
| DB Admin UI | Adminer                |

Чому обрано саме цей стек:

| Технологія     | Причина                                                       |
| -------------- | ------------------------------------------------------------- |
| FastAPI        | Швидка розробка API, Swagger UI, зручна інтеграція з Pydantic |
| PostgreSQL     | Надійне structured data сховище                               |
| SQLAlchemy     | ORM для моделей і роботи з БД                                 |
| Alembic        | Контрольовані міграції                                        |
| Docker Compose | Відтворюваний локальний запуск                                |
| Pytest         | Перевірка критичної бізнес-логіки                             |
| Adminer        | Простий перегляд PostgreSQL                                   |

---

## 8. Структура проєкту

```text
AI Task Capture System/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dictionaries.py
│   │   ├── task.py
│   │   ├── task_event.py
│   │   └── task_preview.py
│   ├── routers/
│   │   ├── dicts.py
│   │   ├── health.py
│   │   └── tasks.py
│   ├── schemas/
│   │   ├── ai_parser.py
│   │   ├── dictionaries.py
│   │   ├── task.py
│   │   └── task_event.py
│   ├── services/
│   │   ├── ai_parser_service.py
│   │   ├── event_service.py
│   │   ├── preview_service.py
│   │   ├── score_service.py
│   │   └── status_service.py
│   └── utils/
├── docs/
│   ├── COURSE_SUBMISSION.md
│   └── RESEARCH_AND_CONCEPT.md
├── migrations/
├── scripts/
│   └── seed_dictionaries.py
├── tests/
│   ├── test_ai_parser_service.py
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

## 9. Запуск через Docker Compose

### 9.1. Запустити сервіси

```powershell
docker compose up -d --build
```

### 9.2. Перевірити статус контейнерів

```powershell
docker compose ps
```

Очікувані сервіси:

```text
ai-task-capture-system-backend
ai-task-capture-system-db
ai-task-capture-system-adminer
```

### 9.3. Health check

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікувано:

```text
status = ok
database = ok
```

### 9.4. Переглянути логи backend

```powershell
docker compose logs -f backend
```

### 9.5. Зупинити сервіси

```powershell
docker compose down
```

### 9.6. Зупинити сервіси і видалити дані PostgreSQL

```powershell
docker compose down -v
```

Увага: команда з `-v` видаляє Docker volume з даними PostgreSQL.

---

## 10. Корисні URL

| Що           | URL                          |
| ------------ | ---------------------------- |
| FastAPI root | http://localhost:8000        |
| Swagger UI   | http://localhost:8000/docs   |
| Health check | http://localhost:8000/health |
| Adminer      | http://localhost:8080        |

---

## 11. Підключення до Adminer

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

## 12. Міграції бази даних

Проєкт використовує Alembic.

### 12.1. Застосувати всі міграції

```powershell
python -m alembic upgrade head
```

### 12.2. Перевірити поточну міграцію

```powershell
python -m alembic current
```

### 12.3. Переглянути історію міграцій

```powershell
python -m alembic history
```

---

## 13. Seed довідників

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

## 14. Основні таблиці

### 14.1. `tasks`

Основна таблиця задач.

Ключові поля:

| Поле                       | Призначення                     |
| -------------------------- | ------------------------------- |
| `task_title`               | Назва задачі                    |
| `goal`                     | Ціль задачі                     |
| `task_type_id`             | Тип задачі                      |
| `business_area`            | Бізнес-напрям                   |
| `customer`                 | Замовник                        |
| `auto_status`              | Автоматично розрахований статус |
| `priority_id`              | Пріоритет                       |
| `complexity_id`            | Складність                      |
| `auto_task_score`          | Автоматична оцінка задачі       |
| `executor`                 | Виконавець                      |
| `planned_finish_date`      | Планова дата виконання          |
| `fact_start_date`          | Фактичний старт                 |
| `fact_finish_date`         | Фактичне завершення             |
| `fact_hours`               | Фактично витрачені години       |
| `short_status_description` | Короткий опис статусу           |
| `source_text`              | Початковий текст користувача    |
| `ai_confidence`            | Впевненість AI / parser         |

### 14.2. `task_events`

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

### 14.3. `task_previews`

Таблиця попередніх змін перед підтвердженням.

Саме вона забезпечує сценарій:

```text
preview → confirm → write
```

---

## 15. Довідники

### 15.1. Пріоритети

| Code       | Name     | Коефіцієнт |
| ---------- | -------- | ---------: |
| `critical` | Critical |       1.00 |
| `high`     | High     |       0.80 |
| `medium`   | Medium   |       0.60 |
| `low`      | Low      |       0.50 |

### 15.2. Складність

| Code           | Name         | Коефіцієнт |
| -------------- | ------------ | ---------: |
| `very_complex` | Very Complex |       3.00 |
| `complex`      | Complex      |       2.00 |
| `moderate`     | Moderate     |       1.50 |
| `easy`         | Easy         |       1.00 |

### 15.3. Типи задач

| Code           | Name       | Базовий час |
| -------------- | ---------- | ----------: |
| `db_reports`   | БД/Звіти   |           5 |
| `pbi_reports`  | Звіти PBI  |           8 |
| `requests`     | Запити     |           3 |
| `ssrs_reports` | Звіти SSRS |           5 |

---

## 16. Логіка автостатусу

Автостатус розраховується backend-ом, а не AI.

Правила:

| Умова                                      | Статус     |
| ------------------------------------------ | ---------- |
| Є `fact_finish_date`                       | `Виконано` |
| Немає пріоритету або складності            | `Оцінка`   |
| Є пріоритет і складність, але немає старту | `Нова`     |
| `fact_start_date <= today`                 | `В роботі` |
| `fact_start_date > today`                  | `План`     |
| Задача вручну поставлена на паузу          | `Пауза`    |

Ця логіка реалізована в:

```text
app/services/status_service.py
```

---

## 17. Логіка автооцінки задачі

Автоматична оцінка задачі розраховується backend-ом.

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

## 18. API endpoints

### 18.1. Health

```http
GET /health
```

### 18.2. Довідники

```http
GET /dicts/priorities
GET /dicts/complexities
GET /dicts/task-types
GET /dicts/task-score-matrix
```

### 18.3. Задачі

```http
GET /tasks
GET /tasks/{task_id}
GET /tasks/{task_id}/events
```

### 18.4. Preview / Confirm / AI

```http
POST /tasks/preview
POST /tasks/ai-preview
POST /tasks/voice-preview
POST /tasks/confirm
```

### 18.5. Lifecycle workflows

```http
POST /tasks/{task_id}/start
POST /tasks/{task_id}/plan
POST /tasks/{task_id}/pause
POST /tasks/{task_id}/resume
POST /tasks/{task_id}/update
POST /tasks/{task_id}/close
```

---

## 19. Приклади API-запитів

### 19.1. AI text preview

```powershell
$body = @{
    raw_text = "Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"
    created_by = "Кондес П."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/tasks/ai-preview `
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

### 19.2. Voice transcript preview

```powershell
$body = @{
    transcript = "Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"
    created_by = "Кондес П."
    language = "uk-UA"
    speech_confidence = 0.91
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/tasks/voice-preview `
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

### 19.3. Structured preview нової задачі

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

### 19.4. Підтвердити preview

Потрібно взяти `preview_id` з відповіді preview endpoint.

```powershell
$body = @{
    preview_id = 10
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://localhost:8000/tasks/confirm `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Очікувано:

```text
status = confirmed
task_id = new task id
```

---

### 19.5. Переглянути задачу

```powershell
Invoke-RestMethod http://localhost:8000/tasks/4 | ConvertTo-Json -Depth 5
```

---

### 19.6. Переглянути історію змін задачі

```powershell
Invoke-RestMethod http://localhost:8000/tasks/4/events | ConvertTo-Json -Depth 5
```

---

### 19.7. Закрити задачу через preview

```powershell
$body = @{
    fact_finish_date = "2026-06-11"
    fact_hours = 3
    short_status_description = "Перевірено фільтри та знайдено причину."
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

## 20. Тести

Запуск тестів:

```powershell
python -m pytest
```

Поточний очікуваний результат:

```text
19 passed
```

Тести покривають:

* імпорт FastAPI app;
* логіку автостатусу;
* логіку автооцінки;
* округлення оцінки до `0.5` години;
* mock AI parser;
* базові сценарії парсингу тексту.

---

## 21. Перевірка працездатності MVP

Цей сценарій потрібен для перевірки, що основний функціонал MVP працює локально після запуску проєкту.

### 21.1. Запустити проєкт

```powershell
docker compose up -d --build
```

### 21.2. Перевірити health check

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікуваний результат:

```text
status = ok
database = ok
```

### 21.3. Перевірити text input workflow

```http
POST /tasks/ai-preview
```

Цей endpoint приймає звичайний український текст задачі та формує preview.

Сценарій:

```text
raw text
→ mock AI parser
→ structured payload
→ preview
```

Очікуваний результат:

```text
action = create_task
can_confirm = True
```

### 21.4. Перевірити voice transcript workflow

```http
POST /tasks/voice-preview
```

Цей endpoint приймає transcript голосової команди та формує preview.

Сценарій:

```text
voice transcript
→ mock AI parser
→ structured payload
→ preview
```

Очікуваний результат:

```text
action = create_task
can_confirm = True
```

### 21.5. Підтвердити preview

```http
POST /tasks/confirm
```

Після підтвердження preview задача записується в PostgreSQL.

Очікуваний результат:

```text
status = confirmed
task_id = new task id
```

### 21.6. Перевірити створену задачу

```http
GET /tasks/{task_id}
```

Очікувано, що задача містить структуровані поля:

```text
task_title
goal
task_type
business_area
priority
complexity
planned_finish_date
auto_status
auto_task_score
```

### 21.7. Перевірити історію змін

```http
GET /tasks/{task_id}/events
```

Очікувано, що для створеної задачі є запис в `task_events`.

Це підтверджує, що працює audit trail.

---

## 22. Відповідність критеріям LMS

### 22.1. Дослідження та концепція

| Критерій             | Як закрито                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------ |
| Обґрунтування теми   | Проєкт вирішує проблему хаотичної фіксації задач із тексту, голосових команд і повідомлень |
| Аналіз проблеми      | Описано проблему неструктурованого input і ризики AI-помилок                               |
| Вибір стеку          | Обґрунтовано FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, Pytest                      |
| Очікуваний результат | Описано backend MVP з text / voice transcript input, preview, confirm і audit trail        |

### 22.2. Документація

| Критерій            | Як закрито                                                         |
| ------------------- | ------------------------------------------------------------------ |
| Чіткий опис проєкту | Є в README і `docs/COURSE_SUBMISSION.md`                           |
| Архітектурна логіка | Описано routers, schemas, services, models, DB, preview/confirm    |
| Інструкція запуску  | Є Docker Compose, health check, Swagger, Adminer                   |
| Залежності          | Описано технологічний стек                                         |
| Сценарій перевірки  | Описано text preview, voice preview, confirm, task details, events |

### 22.3. Працездатність MVP

| Критерій                  | Як закрито                                              |
| ------------------------- | ------------------------------------------------------- |
| Проєкт запускається       | Docker Compose піднімає backend, PostgreSQL, Adminer    |
| Health check працює       | `/health` повертає `status = ok`, `database = ok`       |
| Основні сценарії працюють | ai-preview, voice-preview, confirm, lifecycle workflows |
| Тести проходять           | `19 passed`                                             |

### 22.4. Якість коду та архітектура

| Критерій                     | Як закрито                                                                  |
| ---------------------------- | --------------------------------------------------------------------------- |
| Логічна структура директорій | `app/routers`, `app/schemas`, `app/services`, `app/models`, `tests`, `docs` |
| Clean Code                   | Бізнес-логіка винесена в services                                           |
| Немає прямого AI write в DB  | Використано `preview → confirm`                                             |
| Є audit trail                | Зміни пишуться в `task_events`                                              |
| Доречні інструменти          | FastAPI, PostgreSQL, Alembic, SQLAlchemy, Docker, Pytest                    |

---

## 23. Known limitations

Поточна версія є MVP.

Обмеження:

* використовується mock AI parser, а не реальний LLM;
* пряме завантаження audio-файлу не входить у MVP;
* власний speech-to-text engine не реалізований у цьому MVP;
* голосовий сценарій реалізовано через обробку transcript;
* немає frontend UI;
* немає авторизації;
* немає Telegram bot;
* немає production deployment;
* немає Excel import/export;
* немає semantic search;
* немає vector database;
* немає RAG;
* немає MCP server.

Ці обмеження свідомо залишені поза MVP, щоб сфокусуватися на core AI Engineering workflow.

---

## 24. Roadmap

Наступні можливі кроки:

1. Замінити mock parser на реальний LLM parser.
2. Додати JSON schema validation для AI-виводу.
3. Додати guardrails для неповних або небезпечних змін.
4. Додати пряме завантаження audio-файлу.
5. Підключити Speech-to-Text, наприклад Whisper або OpenAI Audio API.
6. Додати Telegram bot або простий frontend.
7. Додати Excel export/import.
8. Додати пошук задач.
9. Додати semantic search через embeddings.
10. Додати RAG для пошуку схожих задач або рекомендацій.
11. Додати monitoring якості AI parser.
12. Додати user authentication.
13. Додати dashboard по задачах.
14. Додати MCP server для інтеграції із зовнішніми AI agents.

---

## 25. Версія для здачі

Робоча гілка:

```text
dev
```

Фінальний тег для здачі:

```text
v0.1-course-mvp
```

Після фінальних змін тег має стояти на останньому коміті.

Перевірка:

```powershell
git log --oneline --decorate -5
```

Очікувано:

```text
HEAD -> dev, tag: v0.1-course-mvp
```

---

## 26. Поточний статус

Поточний статус:

```text
MVP реалізовано.
Backend запускається через Docker Compose.
PostgreSQL працює.
Health check працює.
AI text preview працює.
Voice transcript preview працює.
Preview/confirm workflow працює.
Task lifecycle workflows реалізовано.
Audit trail реалізовано через task_events.
Тести проходять.
Документація для LMS підготовлена.
```

Рівень готовності:

```text
Проєкт готовий до здачі як course MVP.
```

---

## 27. Ключова фраза

```text
У цьому MVP AI не приймає остаточне рішення і не пише напряму в базу.
AI тільки допомагає перетворити текст або transcript голосової команди у structured payload.
Backend формує preview, користувач підтверджує зміни, і тільки після цього задача записується в PostgreSQL.
```
