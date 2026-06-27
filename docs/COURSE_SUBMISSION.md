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
2. виділити з тексту поля задачі;
3. показати користувачу preview;
4. записати в базу тільки після підтвердження.

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

У поточній версії використовується deterministic mock AI parser. Його можна замінити на реальний LLM parser без зміни загальної архітектури.

---

## 5. Voice-ready сценарій

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

Приклад запиту:

```powershell
$body = @{
    transcript = "Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"
    created_by = "Кондес П."
    language = "uk-UA"
    speech_confidence = 0.91
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/tasks/voice-preview -Method Post -ContentType "application/json" -Body $body
```

Очікуваний результат:

```text
action = create_task
can_confirm = True
```

Після цього preview підтверджується через:

```http
POST /tasks/confirm
```

Це дозволяє показати голосовий сценарій у межах MVP без інтеграції зовнішнього Speech-to-Text сервісу. У майбутньому перед цим endpoint-ом можна підключити Whisper, OpenAI Audio API, Google Speech-to-Text або інший STT-сервіс.

---

## 6. Чому використовується preview → confirm

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

Це дає такі переваги:

| Перевага        | Пояснення                                             |
| --------------- | ----------------------------------------------------- |
| Контроль        | Користувач бачить, що саме буде записано              |
| Безпека         | AI не має прямого запису в БД                         |
| Прозорість      | Усі зміни видно до підтвердження                      |
| Audit trail     | Після підтвердження зміни пишуться в task_events      |
| Масштабованість | Такий патерн можна використати для інших AI workflows |

---

## 7. Чому обрано саме цей стек

| Компонент   | Технологія             | Чому обрано                                                           |
| ----------- | ---------------------- | --------------------------------------------------------------------- |
| Backend     | Python 3.12, FastAPI   | Швидка розробка API, Swagger UI, зручна інтеграція з Pydantic         |
| Database    | PostgreSQL             | Надійне structured data сховище для задач, довідників та історії змін |
| ORM         | SQLAlchemy             | Логічний опис моделей у Python і відокремлення бізнес-логіки від SQL  |
| Migrations  | Alembic                | Контрольована еволюція структури БД                                   |
| Validation  | Pydantic               | Перевірка вхідних даних і структуровані schemas                       |
| Tests       | Pytest                 | Перевірка бізнес-логіки та стабільності MVP                           |
| Containers  | Docker, Docker Compose | Відтворюваний локальний запуск backend + database                     |
| DB Admin UI | Adminer                | Простий перегляд PostgreSQL під час демо                              |

Цей стек обраний тому, що він добре підходить для production-oriented AI Engineering MVP: є API layer, БД, міграції, тести, ізоляція через Docker і можливість розширити mock AI parser до реального LLM parser.

---

## 8. Технологічний стек

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
* mock AI parser;
* AI preview endpoint;
* voice transcript preview endpoint;
* text input → structured payload → preview → confirm → DB;
* voice transcript → structured payload → preview → confirm → DB;
* тести.

---

## 10. Архітектурна логіка

Загальна схема:

```text
User / Swagger
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

Система розділена на логічні шари:

| Шар        | Призначення                       |
| ---------- | --------------------------------- |
| routers    | API endpoints                     |
| schemas    | Валідація request / response      |
| services   | Бізнес-логіка                     |
| models     | SQLAlchemy-моделі БД              |
| migrations | Alembic-міграції                  |
| tests      | Перевірка критичної логіки        |
| docs       | Документація для здачі та запуску |

---

## 11. Реалізовані workflows задачі

Система підтримує такі сценарії:

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

## 12. Життєвий цикл задачі

Поточна модель статусів:

```text
Оцінка
  ↓
Нова
  ↓
План
  ↓
В роботі
  ↓
Пауза
  ↓
В роботі
  ↓
Виконано
```

Також задача може оновлюватися через update workflow.

---

## 13. Автостатус

Статус задачі розраховується backend-ом.

Базові правила:

| Умова                                         | Статус     |
| --------------------------------------------- | ---------- |
| Є `fact_finish_date`                          | `Виконано` |
| Немає priority або complexity                 | `Оцінка`   |
| Є priority і complexity, але немає start date | `Нова`     |
| Start date у майбутньому                      | `План`     |
| Start date сьогодні або в минулому            | `В роботі` |
| Задача вручну поставлена на паузу             | `Пауза`    |

Це важливо, бо статус не вводиться хаотично вручну, а контролюється бізнес-логікою backend-у.

---

## 14. Автоматична оцінка задачі

Оцінка задачі розраховується за формулою:

```text
auto_task_score = task_type.base_hours × priority.coefficient × complexity.coefficient
```

Результат округлюється до найближчих 0.5 години.

Приклад:

```text
Тип задачі: Запити → 3 години
Пріоритет: High → 0.80
Складність: Easy → 1.00

3 × 0.80 × 1.00 = 2.4 → 2.5
```

Це дозволяє отримати базову автоматичну оцінку складності / трудомісткості задачі.

---

## 15. Audit trail

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

Audit trail важливий для прозорості, контролю та майбутнього аналізу задач.

---

## 16. Локальний запуск

### 16.1. Вимоги

Потрібно мати встановлені:

* Docker;
* Docker Compose;
* Python 3.12;
* Git.

### 16.2. Запуск через Docker Compose

```powershell
docker compose up -d --build
```

### 16.3. Перевірка контейнерів

```powershell
docker compose ps
```

Очікувано мають бути запущені:

```text
ai-task-capture-system-backend
ai-task-capture-system-db
ai-task-capture-system-adminer
```

### 16.4. Health check

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікувано:

```text
status = ok
database = ok
```

### 16.5. Swagger UI

```text
http://localhost:8000/docs
```

### 16.6. Adminer

```text
http://localhost:8080
```

Параметри підключення:

```text
System: PostgreSQL
Server: db
Username: task_user
Password: task_password
Database: task_capture_db
```

---

## 17. Демо-сценарій для перевірки MVP

### 17.1. Health check

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікувано:

```text
status = ok
database = ok
```

---

### 17.2. AI text preview

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

---

### 17.3. Voice transcript preview

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

---

### 17.4. Confirm preview

Після preview потрібно взяти `preview_id` з відповіді.

Наприклад, якщо preview_id = 10:

```powershell
$body = @{
    preview_id = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/tasks/confirm -Method Post -ContentType "application/json" -Body $body
```

Очікувано:

```text
status = confirmed
task_id = new task id
```

---

### 17.5. Перегляд задачі

Якщо створена задача має id = 4:

```powershell
Invoke-RestMethod http://localhost:8000/tasks/4 | ConvertTo-Json -Depth 5
```

Очікувано, що задача містить:

```text
task_type_name = Звіти PBI
business_area = Сільпо
priority_name = High
complexity_name = Complex
planned_finish_date = 2026-07-01
```

---

### 17.6. Перегляд історії змін

```powershell
Invoke-RestMethod http://localhost:8000/tasks/4/events | ConvertTo-Json -Depth 5
```

Очікувано:

```text
event_type = created
source = preview
```

---

## 18. Тести

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
* базові сценарії парсингу тексту.

---

## 19. Відповідність критеріям LMS

### 19.1. Дослідження та концепція

| Критерій             | Як закрито в проєкті                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------- |
| Обґрунтування теми   | Проєкт вирішує проблему хаотичної фіксації задач із тексту, голосових команд і повідомлень  |
| Аналіз проблеми      | Описано проблему неструктурованого input, ризики AI-помилок і потребу preview перед записом |
| Самостійність ідеї   | Реалізовано власний MVP під реальний робочий процес задач                                   |
| Вибір стеку          | Обґрунтовано FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, Pytest                       |
| Очікуваний результат | Описано backend MVP з text / voice transcript input, preview, confirm і audit trail         |

### 19.2. Документація

| Критерій            | Як закрито                                                                       |
| ------------------- | -------------------------------------------------------------------------------- |
| Чіткий опис проєкту | Є в README і `docs/COURSE_SUBMISSION.md`                                         |
| Архітектурна логіка | Описано routing, schemas, services, models, DB, preview/confirm                  |
| Інструкція запуску  | Є команди Docker Compose, health check, Swagger, Adminer                         |
| Залежності          | Описано технологічний стек і основні компоненти                                  |
| Demo flow           | Описано AI text preview, voice transcript preview, confirm, task details, events |

### 19.3. Працездатність MVP

| Критерій                           | Як закрито                                                              |
| ---------------------------------- | ----------------------------------------------------------------------- |
| Проєкт запускається                | Docker Compose піднімає backend, PostgreSQL, Adminer                    |
| Health check працює                | `/health` повертає `status = ok`, `database = ok`                       |
| Основні сценарії працюють          | create, ai-preview, voice-preview, confirm, update, lifecycle workflows |
| Немає критичних крашів у demo flow | Основні endpoints перевірені вручну                                     |
| Тести проходять                    | `19 passed`                                                             |

### 19.4. Якість коду та архітектура

| Критерій                     | Як закрито                                                      |
| ---------------------------- | --------------------------------------------------------------- |
| Логічна структура директорій | app/routers, app/schemas, app/services, app/models, tests, docs |
| Clean Code                   | Бізнес-логіка винесена в services                               |
| Немає прямого AI write в DB  | Використано preview → confirm                                   |
| Є audit trail                | Зміни пишуться в task_events                                    |
| Доречні інструменти          | FastAPI, PostgreSQL, Alembic, SQLAlchemy, Docker, Pytest        |

---

## 20. Обмеження поточної версії

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
* немає real-time notifications;
* немає Excel export/import;
* немає semantic search;
* немає vector database;
* немає RAG.

Ці обмеження свідомо залишені поза MVP, щоб сфокусуватися на core AI Engineering workflow.

---

## 21. Можливий розвиток

Наступні кроки розвитку:

1. Замінити mock parser на реальний LLM parser.
2. Додати JSON schema validation для AI-виводу.
3. Додати guardrails для небезпечних або неповних змін.
4. Додати пряме завантаження audio-файлу.
5. Підключити Speech-to-Text, наприклад Whisper або OpenAI Audio API.
6. Додати Telegram bot або простий frontend.
7. Додати пошук задач.
8. Додати Excel export/import.
9. Додати semantic search через embeddings.
10. Додати monitoring для AI parser якості.
11. Додати user authentication.
12. Додати dashboard по задачах.
13. Додати RAG для пошуку схожих задач або рекомендацій.

---

## 22. Що треба вміти пояснити на захисті

На захисті треба пояснити:

1. Яку проблему вирішує проєкт.
2. Чому це не просто CRUD, а AI Engineering MVP.
3. Як працює text input → AI parser → preview → confirm.
4. Як працює voice transcript → AI parser → preview → confirm.
5. Чому audio upload і speech-to-text винесені за межі MVP.
6. Чому AI не пише напряму в базу.
7. Як працює preview → confirm.
8. Як raw text або transcript перетворюється в structured payload.
9. Чому mock parser можна замінити на реальний LLM.
10. Як backend розраховує статус задачі.
11. Як backend розраховує оцінку задачі.
12. Як працює task_events audit trail.
13. Як Docker Compose запускає систему.
14. Які є обмеження MVP.
15. Як можна розвивати систему далі.

---

## 23. Ключова фраза для захисту

```text
У цьому MVP AI не приймає остаточне рішення і не пише напряму в базу.
AI тільки допомагає перетворити текст або transcript голосової команди у structured payload.
Backend формує preview, користувач підтверджує зміни, і тільки після цього задача записується в PostgreSQL.
```

---

## 24. Висновок

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
* mock AI parser;
* preview → confirm;
* PostgreSQL persistence;
* task_events audit trail;
* Docker-запуск;
* тести;
* документацію для перевірки та запуску.

Це робить систему контрольованою, прозорою і придатною для подальшого розвитку в реальний AI-powered інструмент для управління задачами.
