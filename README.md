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
* `docs/RESEARCH_AND_CONCEPT.md` — дослідження проблеми, концепція, обґрунтування стеку та AI/voice-ready scope.

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
* provider-based AI parser;
* optional OpenAI LLM parser;
* mock fallback parser для запуску без ключа;
* тести;
* українська документація для здачі.

---

## 5. AI provider modes

Проєкт підтримує два режими AI parser:

```text
AI_PROVIDER=mock
AI_PROVIDER=openai
```

### Mock provider

`AI_PROVIDER=mock` використовується за замовчуванням.

Цей режим потрібен для:

* локального запуску без зовнішніх API ключів;
* стабільної перевірки в LMS;
* повторюваних тестів;
* fallback-сценарію, якщо LLM provider недоступний.

У цьому режимі використовується deterministic parser на Python.

### OpenAI provider

`AI_PROVIDER=openai` використовується для реальної AI-обробки сирого тексту або transcript голосової команди.

У цьому режимі workflow виглядає так:

```text
raw text / voice transcript
→ OpenAI LLM
→ structured JSON
→ Pydantic validation
→ preview
→ confirm
→ PostgreSQL
```

Цей режим дозволяє обробляти неакуратний, сирий або голосовий текст і формувати:

* коротку професійну назву задачі;
* ціль задачі;
* тип задачі;
* бізнес-напрям;
* замовника;
* пріоритет;
* складність;
* планову дату;
* confidence score.

Для використання OpenAI provider потрібно локально створити `.env` і додати:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Файл `.env` не потрібно комітити в Git.

Для перевірки без API ключа достатньо залишити режим за замовчуванням:

```env
AI_PROVIDER=mock
```

---

## 6. Voice-ready MVP scope

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

## 7. Архітектура MVP

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
AI Parser Provider
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
mock parser або OpenAI LLM parser
        ↓
structured payload
        ↓
Pydantic validation
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

## 8. Технології

| Компонент   | Технологія                 |
| ----------- | -------------------------- |
| Backend     | Python 3.12, FastAPI       |
| Database    | PostgreSQL                 |
| ORM         | SQLAlchemy                 |
| Migrations  | Alembic                    |
| Validation  | Pydantic                   |
| AI provider | OpenAI API / mock fallback |
| Tests       | Pytest                     |
| Containers  | Docker, Docker Compose     |
| DB Admin UI | Adminer                    |

Чому обрано саме цей стек:

| Технологія      | Причина                                                          |
| --------------- | ---------------------------------------------------------------- |
| FastAPI         | Швидка розробка API, Swagger UI, зручна інтеграція з Pydantic    |
| PostgreSQL      | Надійне structured data сховище                                  |
| SQLAlchemy      | ORM для моделей і роботи з БД                                    |
| Alembic         | Контрольовані міграції                                           |
| OpenAI provider | Реальна AI-обробка неструктурованого тексту в structured payload |
| Mock provider   | Стабільний fallback для тестів і запуску без API ключа           |
| Docker Compose  | Відтворюваний локальний запуск                                   |
| Pytest          | Перевірка критичної бізнес-логіки                                |
| Adminer         | Простий перегляд PostgreSQL                                      |

---

## 9. Структура проєкту

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

## 10. Запуск через Docker Compose

### 10.1. Запустити сервіси

```powershell
docker compose up -d --build
```

### 10.2. Перевірити статус контейнерів

```powershell
docker compose ps
```

Очікувані сервіси:

```text
ai-task-capture-system-backend
ai-task-capture-system-db
ai-task-capture-system-adminer
```

### 10.3. Health check

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікувано:

```text
status = ok
database = ok
```

### 10.4. Переглянути логи backend

```powershell
docker compose logs -f backend
```

### 10.5. Зупинити сервіси

```powershell
docker compose down
```

### 10.6. Зупинити сервіси і видалити дані PostgreSQL

```powershell
docker compose down -v
```

Увага: команда з `-v` видаляє Docker volume з даними PostgreSQL.

---

## 11. Корисні URL

| Що           | URL                          |
| ------------ | ---------------------------- |
| FastAPI root | http://localhost:8000        |
| Swagger UI   | http://localhost:8000/docs   |
| Health check | http://localhost:8000/health |
| Adminer      | http://localhost:8080        |

---

## 12. Підключення до Adminer

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

## 13. Міграції бази даних

Проєкт використовує Alembic.

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic history
```

---

## 14. Seed довідників

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

## 15. Основні таблиці

### `tasks`

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

## 16. Логіка автостатусу

Автостатус розраховується backend-ом, а не AI.

| Умова                                      | Статус     |
| ------------------------------------------ | ---------- |
| Є `fact_finish_date`                       | `Виконано` |
| Немає пріоритету або складності            | `Оцінка`   |
| Є пріоритет і складність, але немає старту | `Нова`     |
| `fact_start_date <= today`                 | `В роботі` |
| `fact_start_date > today`                  | `План`     |
| Задача вручну поставлена на паузу          | `Пауза`    |

Реалізація:

```text
app/services/status_service.py
```

---

## 17. Логіка автооцінки задачі

Автоматична оцінка задачі розраховується backend-ом.

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

Реалізація:

```text
app/services/score_service.py
```

---

## 18. API endpoints

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

### Preview / Confirm / AI

```http
POST /tasks/preview
POST /tasks/ai-preview
POST /tasks/voice-preview
POST /tasks/confirm
```

### Lifecycle workflows

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

### AI text preview

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

### Voice transcript preview

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

### Підтвердити preview

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
* mock AI parser;
* базові сценарії парсингу тексту;
* стабільну роботу parser fallback.

---

## 21. Перевірка працездатності MVP

Цей сценарій потрібен для перевірки, що основний функціонал MVP працює локально після запуску проєкту.

1. Запустити проєкт:

```powershell
docker compose up -d --build
```

2. Перевірити health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

3. Перевірити text input workflow:

```http
POST /tasks/ai-preview
```

4. Перевірити voice transcript workflow:

```http
POST /tasks/voice-preview
```

5. Підтвердити preview:

```http
POST /tasks/confirm
```

6. Перевірити створену задачу:

```http
GET /tasks/{task_id}
```

7. Перевірити історію змін:

```http
GET /tasks/{task_id}/events
```

---

## 22. Відповідність критеріям LMS

### Дослідження та концепція

| Критерій             | Як закрито                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| Обґрунтування теми   | Проєкт вирішує проблему хаотичної фіксації задач із тексту, голосових команд і повідомлень       |
| Аналіз проблеми      | Описано проблему неструктурованого input і ризики AI-помилок                                     |
| Вибір стеку          | Обґрунтовано FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, Pytest, OpenAI provider           |
| Очікуваний результат | Описано backend MVP з text / voice transcript input, AI provider, preview, confirm і audit trail |

### Документація

| Критерій            | Як закрито                                                                   |
| ------------------- | ---------------------------------------------------------------------------- |
| Чіткий опис проєкту | Є в README і `docs/COURSE_SUBMISSION.md`                                     |
| Архітектурна логіка | Описано routers, schemas, services, models, DB, AI provider, preview/confirm |
| Інструкція запуску  | Є Docker Compose, health check, Swagger, Adminer                             |
| Залежності          | Описано технологічний стек                                                   |
| Сценарій перевірки  | Описано text preview, voice preview, confirm, task details, events           |

### Працездатність MVP

| Критерій                  | Як закрито                                              |
| ------------------------- | ------------------------------------------------------- |
| Проєкт запускається       | Docker Compose піднімає backend, PostgreSQL, Adminer    |
| Health check працює       | `/health` повертає `status = ok`, `database = ok`       |
| Основні сценарії працюють | ai-preview, voice-preview, confirm, lifecycle workflows |
| Тести проходять           | `19 passed`                                             |

### Якість коду та архітектура

| Критерій                     | Як закрито                                                                  |
| ---------------------------- | --------------------------------------------------------------------------- |
| Логічна структура директорій | `app/routers`, `app/schemas`, `app/services`, `app/models`, `tests`, `docs` |
| Clean Code                   | Бізнес-логіка винесена в services                                           |
| AI provider layer            | Є mock fallback і optional OpenAI provider                                  |
| Немає прямого AI write в DB  | Використано `preview → confirm`                                             |
| Є audit trail                | Зміни пишуться в `task_events`                                              |
| Доречні інструменти          | FastAPI, PostgreSQL, Alembic, SQLAlchemy, Docker, Pytest, OpenAI API        |

---

## 23. Known limitations

Поточна версія є MVP.

Обмеження:

* реальний LLM parser реалізований як optional provider через `AI_PROVIDER=openai`, але для перевірки без API ключа за замовчуванням використовується `AI_PROVIDER=mock`;
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

1. Додати пряме завантаження audio-файлу.
2. Підключити Speech-to-Text, наприклад Whisper або OpenAI Audio API.
3. Додати JSON schema validation rules для більш складних сценаріїв.
4. Додати guardrails для неповних або небезпечних змін.
5. Додати Telegram bot або простий frontend.
6. Додати Excel export/import.
7. Додати пошук задач.
8. Додати semantic search через embeddings.
9. Додати RAG для пошуку схожих задач або рекомендацій.
10. Додати monitoring якості AI parser.
11. Додати user authentication.
12. Додати dashboard по задачах.
13. Додати MCP server для інтеграції із зовнішніми AI agents.

---

## 25. Версія проєкту

Поточна стабільна версія MVP позначена тегом:

```text
v0.1-course-mvp
```

Основна робоча гілка:

```text
dev
```

Цей тег фіксує версію, яка містить базовий AI Engineering workflow:

```text
text input / voice transcript
→ AI parser provider
→ structured payload
→ preview
→ confirm
→ PostgreSQL
→ task_events
```

---

## 26. Поточний стан реалізації

У поточній версії реалізовано:

```text
Backend запускається через Docker Compose.
PostgreSQL використовується як основне сховище.
Health check перевіряє доступність backend і database.
AI text preview працює через provider-based parser.
Voice transcript preview працює через той самий AI workflow.
OpenAI parser доступний як optional provider.
Mock parser доступний як fallback без API ключа.
Preview/confirm workflow відокремлює AI output від запису в БД.
Task lifecycle workflows реалізовано для start, plan, pause, resume, update і close.
Audit trail реалізовано через task_events.
Автоматичний статус і автоматична оцінка задачі розраховуються backend-ом.
Тести покривають критичну бізнес-логіку.
```

---

## 27. Ключовий архітектурний принцип

```text
AI не приймає остаточне рішення і не пише напряму в базу.

AI parser допомагає перетворити неструктурований текст або transcript голосової команди у structured payload.

Backend валідовує дані, формує preview, очікує підтвердження користувача і тільки після цього записує задачу в PostgreSQL.

Для стабільної локальної перевірки використовується mock provider.
Для реальної AI-обробки доступний optional OpenAI provider.
```
