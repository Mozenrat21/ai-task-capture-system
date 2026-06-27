# AI Task Capture System — фінальний опис для здачі

## 1. Короткий опис проєкту

**AI Task Capture System** — це MVP-система для фіксації, структуризації, голосового або текстового введення, ведення та контролю робочих задач.

Основна ідея: користувач може описати задачу звичайною українською мовою або передати transcript голосової команди. Система перетворює цей неструктурований input у structured payload, формує preview змін, а запис у базу відбувається тільки після підтвердження користувачем.

Базовий workflow:

```text
text input / voice transcript
→ AI parser
→ structured payload
→ preview
→ confirm
→ PostgreSQL
→ task_events
```

Проєкт створений як AI Engineering MVP, а не просто CRUD-додаток. Основний акцент зроблено на безпечну роботу з AI-виводом: система не записує зміни напряму, а спочатку показує користувачу, що саме буде змінено.

---

## 2. Яку проблему вирішує проєкт

У реальній роботі задачі часто фіксуються хаотично:

* в Excel;
* у повідомленнях;
* у нотатках;
* у чатах;
* у голосових командах;
* у неструктурованому тексті;
* у коротких формулюваннях від замовників.

Через це важко:

* швидко створювати задачі;
* підтримувати єдину структуру;
* контролювати статуси;
* бачити історію змін;
* оцінювати складність і пріоритет;
* аналізувати виконану роботу;
* безпечно використовувати AI для створення або зміни записів.

Окрема проблема — голосове введення. У реальному процесі користувачу не завжди зручно вручну заповнювати форму. Часто простіше швидко сказати:

```text
Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01
```

Але така команда не є структурованою задачею. Її потрібно:

1. перетворити на текст, якщо вона була голосовою;
2. осмислити через AI parser;
3. виділити з тексту поля задачі;
4. показати користувачу preview;
5. записати в базу тільки після підтвердження.

---

## 3. Основна ідея рішення

Ідея проєкту — створити backend-систему, яка приймає задачу у вигляді тексту або transcript голосової команди, перетворює її у структуровані дані, показує preview і тільки після підтвердження записує результат у PostgreSQL.

Ключовий принцип:

```text
AI не пише напряму в базу.
AI тільки готує structured output.
Backend формує preview.
Користувач підтверджує.
Тільки після цього дані записуються в PostgreSQL.
```

Це зменшує ризик помилкових AI-рішень і робить систему більш контрольованою.

---

## 4. Основний AI Engineering сценарій

Головний сценарій системи:

```text
Користувач пише або диктує:
"Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"

↓ AI parser

Система формує structured payload:
- task_title
- goal
- task_type_id
- business_area
- customer
- priority_id
- complexity_id
- planned_finish_date
- source_text
- ai_confidence

↓ preview

Користувач бачить, які поля будуть записані.

↓ confirm

Тільки після підтвердження задача записується в PostgreSQL.

↓ task_events

Система фіксує історію створення або зміни задачі.
```

---

## 5. AI provider modes

У проєкті реалізовано provider-based підхід для AI parser.

Підтримуються два режими:

| Provider | Призначення                                                               |
| -------- | ------------------------------------------------------------------------- |
| `mock`   | Offline fallback для локального запуску, тестів і перевірки без API ключа |
| `openai` | Реальна LLM-обробка сирого тексту або transcript голосової команди        |

### Mock provider

`AI_PROVIDER=mock` використовується за замовчуванням.

Цей режим потрібен, щоб:

* проєкт можна було запустити без зовнішніх API ключів;
* тести були стабільними;
* перевірка в LMS не залежала від платного сервісу;
* система мала fallback, якщо LLM provider недоступний.

У цьому режимі використовується deterministic parser на Python.

### OpenAI provider

`AI_PROVIDER=openai` використовується для реальної AI-обробки сирого тексту або transcript голосової команди.

Workflow:

```text
raw text / voice transcript
→ OpenAI LLM
→ structured JSON
→ Pydantic validation
→ preview
→ confirm
→ PostgreSQL
→ task_events
```

Це закриває ключову AI Engineering частину проєкту: AI не просто шукає ключові слова, а може осмислювати сирий текст, формувати професійну назву задачі, goal та інші поля.

Для використання OpenAI provider потрібно локально створити `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Файл `.env` не потрібно комітити в Git.

---

## 6. Voice-ready сценарій

Окрім текстового введення, MVP підтримує voice-ready сценарій через обробку transcript голосової команди.

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

У межах MVP система не приймає audio-файл напряму і не реалізує власний speech-to-text engine. Натомість вона приймає вже розпізнаний transcript через endpoint:

```http
POST /tasks/voice-preview
```

Це дозволяє показати голосовий сценарій у межах MVP без інтеграції зовнішнього Speech-to-Text сервісу. У майбутньому перед цим endpoint-ом можна підключити Whisper, OpenAI Audio API, Google Speech-to-Text або інший STT-сервіс.

---

## 7. Чому використовується preview → confirm

AI може помилятися:

* неправильно визначити тип задачі;
* переплутати пріоритет;
* неправильно витягнути дату;
* некоректно зрозуміти замовника;
* неправильно інтерпретувати голосову команду;
* створити неповні або неточні дані.

Тому система не дозволяє AI напряму писати в базу.

Замість цього використовується патерн:

```text
AI output → backend validation → preview → user confirmation → database write
```

Переваги:

| Перевага        | Пояснення                                             |
| --------------- | ----------------------------------------------------- |
| Контроль        | Користувач бачить, що саме буде записано              |
| Безпека         | AI не має прямого запису в БД                         |
| Прозорість      | Усі зміни видно до підтвердження                      |
| Audit trail     | Після підтвердження зміни пишуться в task_events      |
| Масштабованість | Такий патерн можна використати для інших AI workflows |

---

## 8. Чому обрано саме цей стек

| Компонент   | Технологія                 | Чому обрано                                                           |
| ----------- | -------------------------- | --------------------------------------------------------------------- |
| Backend     | Python 3.12, FastAPI       | Швидка розробка API, Swagger UI, зручна інтеграція з Pydantic         |
| Database    | PostgreSQL                 | Надійне structured data сховище для задач, довідників та історії змін |
| ORM         | SQLAlchemy                 | Логічний опис моделей у Python і відокремлення бізнес-логіки від SQL  |
| Migrations  | Alembic                    | Контрольована еволюція структури БД                                   |
| Validation  | Pydantic                   | Перевірка вхідних даних і structured schemas                          |
| AI provider | OpenAI API / mock fallback | Реальна AI-обробка + стабільна перевірка без ключа                    |
| Tests       | Pytest                     | Перевірка бізнес-логіки та стабільності MVP                           |
| Containers  | Docker, Docker Compose     | Відтворюваний локальний запуск backend + database                     |
| DB Admin UI | Adminer                    | Простий перегляд PostgreSQL                                           |

---

## 9. Основні можливості MVP

Реалізовано:

* запуск через Docker Compose;
* FastAPI backend;
* PostgreSQL database;
* Adminer для перегляду БД;
* Alembic migrations;
* seed довідників;
* автоматичний розрахунок статусу;
* автоматична оцінка задачі;
* task lifecycle workflows;
* preview → confirm pattern;
* task_events audit trail;
* provider-based AI parser;
* optional OpenAI LLM provider;
* mock fallback provider;
* AI text preview endpoint;
* voice transcript preview endpoint;
* text input → structured payload → preview → confirm → DB;
* voice transcript → structured payload → preview → confirm → DB;
* тести.

---

## 10. Архітектурна логіка

Загальна схема:

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

Система розділена на логічні шари:

| Шар        | Призначення                         |
| ---------- | ----------------------------------- |
| routers    | API endpoints                       |
| schemas    | Валідація request / response        |
| services   | Бізнес-логіка та AI parser provider |
| models     | SQLAlchemy-моделі БД                |
| migrations | Alembic-міграції                    |
| tests      | Перевірка критичної логіки          |
| docs       | Документація для здачі та запуску   |

---

## 11. Реалізовані workflows задачі

| Workflow                 | Endpoint                       | Призначення                                          |
| ------------------------ | ------------------------------ | ---------------------------------------------------- |
| Create task preview      | `POST /tasks/preview`          | Створення preview нової задачі зі structured payload |
| AI text preview          | `POST /tasks/ai-preview`       | Створення preview із сирого українського тексту      |
| Voice transcript preview | `POST /tasks/voice-preview`    | Створення preview із transcript голосової команди    |
| Confirm preview          | `POST /tasks/confirm`          | Підтвердження preview і запис у БД                   |
| Start task               | `POST /tasks/{task_id}/start`  | Взяти задачу в роботу                                |
| Plan task                | `POST /tasks/{task_id}/plan`   | Запланувати задачу                                   |
| Pause task               | `POST /tasks/{task_id}/pause`  | Поставити задачу на паузу                            |
| Resume task              | `POST /tasks/{task_id}/resume` | Повернути задачу в роботу                            |
| Update task              | `POST /tasks/{task_id}/update` | Оновити поля задачі                                  |
| Close task               | `POST /tasks/{task_id}/close`  | Закрити задачу                                       |
| List tasks               | `GET /tasks`                   | Перегляд задач                                       |
| Task details             | `GET /tasks/{task_id}`         | Деталі задачі                                        |
| Task events              | `GET /tasks/{task_id}/events`  | Історія змін                                         |

---

## 12. Автостатус і автооцінка

Статус задачі розраховується backend-ом.

| Умова                                         | Статус     |
| --------------------------------------------- | ---------- |
| Є `fact_finish_date`                          | `Виконано` |
| Немає priority або complexity                 | `Оцінка`   |
| Є priority і complexity, але немає start date | `Нова`     |
| Start date у майбутньому                      | `План`     |
| Start date сьогодні або в минулому            | `В роботі` |
| Задача вручну поставлена на паузу             | `Пауза`    |

Оцінка задачі:

```text
auto_task_score = task_type.base_hours × priority.coefficient × complexity.coefficient
```

Результат округлюється до найближчих 0.5 години.

---

## 13. Audit trail

Кожна підтверджена зміна записується в `task_events`.

Це дозволяє бачити:

* хто змінив задачу;
* коли змінив;
* яке поле змінив;
* старе значення;
* нове значення;
* джерело зміни;
* тип події.

Приклади event types:

```text
created
started
planned
paused
resumed
updated
classification_changed
score_changed
deadline_changed
status_changed
closed
```

---

## 14. Локальний запуск

Потрібно мати встановлені:

* Docker;
* Docker Compose;
* Python 3.12;
* Git.

Запуск:

```powershell
docker compose up -d --build
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікувано:

```text
status = ok
database = ok
```

Swagger UI:

```text
http://localhost:8000/docs
```

Adminer:

```text
http://localhost:8080
```

Параметри Adminer:

```text
System: PostgreSQL
Server: db
Username: task_user
Password: task_password
Database: task_capture_db
```

---

## 15. Перевірка працездатності MVP

### 15.1. Text input workflow

```powershell
$body = @{
    raw_text = "Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"
    created_by = "Кондес П."
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/tasks/ai-preview -Method Post -ContentType "application/json" -Body $body
```

Очікувано:

```text
action = create_task
can_confirm = True
```

### 15.2. Voice transcript workflow

```powershell
$body = @{
    transcript = "Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"
    created_by = "Кондес П."
    language = "uk-UA"
    speech_confidence = 0.91
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/tasks/voice-preview -Method Post -ContentType "application/json" -Body $body
```

Очікувано:

```text
action = create_task
can_confirm = True
```

### 15.3. Confirm preview

```powershell
$body = @{
    preview_id = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/tasks/confirm -Method Post -ContentType "application/json" -Body $body
```

---

## 16. Тести

Запуск тестів:

```powershell
python -m pytest
```

Поточний результат:

```text
19 passed
```

Тести покривають:

* імпорт FastAPI app;
* автостатус;
* автооцінку;
* mock AI parser;
* базові сценарії парсингу тексту;
* стабільність fallback-режиму.

---

## 17. Відповідність критеріям LMS

### Дослідження та концепція

| Критерій             | Як закрито                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------------- |
| Обґрунтування теми   | Проєкт вирішує проблему хаотичної фіксації задач із тексту, голосових команд і повідомлень  |
| Аналіз проблеми      | Описано проблему неструктурованого input, ризики AI-помилок і потребу preview перед записом |
| Самостійність ідеї   | Реалізовано власний MVP під реальний робочий процес задач                                   |
| Вибір стеку          | Обґрунтовано FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, Pytest, OpenAI provider      |
| Очікуваний результат | Backend MVP з text / voice transcript input, AI provider, preview, confirm і audit trail    |

### Документація

| Критерій            | Як закрито                                                                       |
| ------------------- | -------------------------------------------------------------------------------- |
| Чіткий опис проєкту | Є в README і `docs/COURSE_SUBMISSION.md`                                         |
| Архітектурна логіка | Описано routing, schemas, services, AI provider, models, DB, preview/confirm     |
| Інструкція запуску  | Є Docker Compose, health check, Swagger, Adminer                                 |
| Залежності          | Описано технологічний стек і основні компоненти                                  |
| Сценарій перевірки  | Описано AI text preview, voice transcript preview, confirm, task details, events |

### Працездатність MVP

| Критерій                  | Як закрито                                                              |
| ------------------------- | ----------------------------------------------------------------------- |
| Проєкт запускається       | Docker Compose піднімає backend, PostgreSQL, Adminer                    |
| Health check працює       | `/health` повертає `status = ok`, `database = ok`                       |
| Основні сценарії працюють | create, ai-preview, voice-preview, confirm, update, lifecycle workflows |
| Немає критичних крашів    | Основні endpoints перевірені вручну                                     |
| Тести проходять           | `19 passed`                                                             |

### Якість коду та архітектура

| Критерій                     | Як закрито                                                           |
| ---------------------------- | -------------------------------------------------------------------- |
| Логічна структура директорій | app/routers, app/schemas, app/services, app/models, tests, docs      |
| Clean Code                   | Бізнес-логіка винесена в services                                    |
| AI provider layer            | Є mock fallback і optional OpenAI provider                           |
| Немає прямого AI write в DB  | Використано preview → confirm                                        |
| Є audit trail                | Зміни пишуться в task_events                                         |
| Доречні інструменти          | FastAPI, PostgreSQL, Alembic, SQLAlchemy, Docker, Pytest, OpenAI API |

---

## 18. Обмеження поточної версії

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
* немає Excel export/import;
* немає semantic search;
* немає vector database;
* немає RAG.

Ці обмеження свідомо залишені поза MVP, щоб сфокусуватися на core AI Engineering workflow.

---

## 19. Можливий розвиток

Наступні кроки розвитку:

1. Додати пряме завантаження audio-файлу.
2. Підключити Speech-to-Text, наприклад Whisper або OpenAI Audio API.
3. Посилити JSON schema validation для складніших сценаріїв.
4. Додати guardrails для небезпечних або неповних змін.
5. Додати Telegram bot або простий frontend.
6. Додати пошук задач.
7. Додати Excel export/import.
8. Додати semantic search через embeddings.
9. Додати monitoring для AI parser якості.
10. Додати user authentication.
11. Додати dashboard по задачах.
12. Додати RAG для пошуку схожих задач або рекомендацій.

---

## 20. Що треба вміти пояснити

1. Яку проблему вирішує проєкт.
2. Чому це не просто CRUD, а AI Engineering MVP.
3. Як працює text input → AI parser → preview → confirm.
4. Як працює voice transcript → AI parser → preview → confirm.
5. Чому audio upload і speech-to-text винесені за межі MVP.
6. Чому AI не пише напряму в базу.
7. Як працює provider-based AI parser.
8. Навіщо потрібні `AI_PROVIDER=mock` і `AI_PROVIDER=openai`.
9. Чому mock provider залишено для fallback і тестів.
10. Як backend розраховує статус задачі.
11. Як backend розраховує оцінку задачі.
12. Як працює task_events audit trail.
13. Як Docker Compose запускає систему.
14. Які є обмеження MVP.
15. Як можна розвивати систему далі.

---

## 21. Ключова фраза

```text
У цьому MVP AI не приймає остаточне рішення і не пише напряму в базу.
AI допомагає перетворити текст або transcript голосової команди у structured payload.
Backend формує preview, користувач підтверджує зміни, і тільки після цього задача записується в PostgreSQL.
Для стабільної перевірки використовується mock provider, а для реальної AI-обробки доступний optional OpenAI provider.
```

---

## 22. Висновок

AI Task Capture System демонструє базовий production-oriented AI Engineering підхід:

```text
AI допомагає структурувати дані.
Backend валідовує і формує preview.
Користувач підтверджує.
Тільки після цього дані записуються в БД.
Усі підтверджені зміни логуються.
```

У межах MVP реалізовано:

* текстове введення задачі;
* voice-ready сценарій через transcript;
* provider-based AI parser;
* optional OpenAI LLM provider;
* mock fallback provider;
* preview → confirm;
* PostgreSQL persistence;
* task_events audit trail;
* Docker-запуск;
* тести;
* документацію для перевірки та запуску.

Це робить систему контрольованою, прозорою і придатною для подальшого розвитку в реальний AI-powered інструмент для управління задачами.
