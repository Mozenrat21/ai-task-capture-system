# AI Task Capture System — фінальний опис для здачі

## 1. Короткий опис проєкту

**AI Task Capture System** — це MVP-система для фіксації, структуризації, ведення та контролю робочих задач.

Основна ідея: користувач вводить задачу звичайною українською мовою, система перетворює цей текст у структуровані дані, формує preview змін, а запис у базу відбувається тільки після підтвердження користувачем.

Базовий workflow:

```text
raw text → AI parser → structured payload → preview → confirm → PostgreSQL
```

Проєкт створений як AI Engineering MVP, а не просто CRUD-додаток. Основний акцент зроблено на безпечну роботу з AI-виводом: система не записує зміни напряму, а спочатку показує користувачу, що саме буде змінено.

---

## 2. Яку проблему вирішує проєкт

У реальній роботі задачі часто фіксуються хаотично:

* в Excel;
* у повідомленнях;
* у нотатках;
* у чатах;
* у неструктурованому тексті.

Через це важко:

* швидко створювати задачі;
* підтримувати єдину структуру;
* контролювати статуси;
* бачити історію змін;
* оцінювати складність і пріоритет;
* аналізувати виконану роботу.

Цей MVP вирішує проблему первинного збору задач і переводить неструктурований текст у контрольований процес.

---

## 3. Основний AI Engineering сценарій

Головний сценарій системи:

```text
Користувач пише:
"Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01"

↓ mock AI parser

Система формує structured payload:
- task_title
- goal
- task_type_id
- business_area
- priority_id
- complexity_id
- planned_finish_date
- source_text
- ai_confidence

↓ preview

Користувач бачить, які поля будуть записані.

↓ confirm

Тільки після підтвердження задача записується в PostgreSQL.
```

У поточній версії використовується deterministic mock AI parser. Його можна замінити на реальний LLM parser без зміни загальної архітектури.

---

## 4. Чому використовується preview → confirm

AI може помилятися:

* неправильно визначити тип задачі;
* переплутати пріоритет;
* неправильно витягнути дату;
* некоректно зрозуміти замовника;
* створити неповні дані.

Тому система не дозволяє AI напряму писати в базу.

Замість цього використовується патерн:

```text
AI output → preview → user confirmation → database write
```

Це зменшує ризики помилкових записів і робить систему безпечнішою для реального використання.

---

## 5. Технологічний стек

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

## 6. Основні можливості MVP

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
* task events audit trail;
* mock AI parser;
* AI preview endpoint;
* тести.

---

## 7. Реалізовані workflows задачі

Система підтримує такі сценарії:

| Workflow          | Endpoint                       | Призначення                        |
| ----------------- | ------------------------------ | ---------------------------------- |
| Create task       | `POST /tasks/preview`          | Створення preview нової задачі     |
| AI create preview | `POST /tasks/ai-preview`       | Створення preview із сирого тексту |
| Confirm preview   | `POST /tasks/confirm`          | Підтвердження preview              |
| Start task        | `POST /tasks/{task_id}/start`  | Взяти задачу в роботу              |
| Plan task         | `POST /tasks/{task_id}/plan`   | Запланувати задачу                 |
| Pause task        | `POST /tasks/{task_id}/pause`  | Поставити задачу на паузу          |
| Resume task       | `POST /tasks/{task_id}/resume` | Повернути задачу в роботу          |
| Update task       | `POST /tasks/{task_id}/update` | Оновити поля задачі                |
| Close task        | `POST /tasks/{task_id}/close`  | Закрити задачу                     |
| List tasks        | `GET /tasks`                   | Перегляд задач                     |
| Task details      | `GET /tasks/{task_id}`         | Деталі задачі                      |
| Task events       | `GET /tasks/{task_id}/events`  | Історія змін                       |

---

## 8. Життєвий цикл задачі

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

## 9. Автостатус

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

---

## 10. Автоматична оцінка задачі

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

---

## 11. Audit trail

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

## 12. Демо-сценарій для перевірки

### 12.1. Запуск

```powershell
docker compose up -d --build
```

### 12.2. Перевірка health

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Очікувано:

```text
status = ok
database = ok
```

### 12.3. AI preview

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

### 12.4. Confirm preview

```powershell
$body = @{
    preview_id = 9
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/tasks/confirm -Method Post -ContentType "application/json" -Body $body
```

### 12.5. Перегляд задачі

```powershell
Invoke-RestMethod http://localhost:8000/tasks/3 | ConvertTo-Json -Depth 5
```

### 12.6. Перегляд історії

```powershell
Invoke-RestMethod http://localhost:8000/tasks/3/events | ConvertTo-Json -Depth 5
```

---

## 13. Тести

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

## 14. Обмеження поточної версії

Поточна версія є MVP.

Обмеження:

* використовується mock AI parser, а не реальний LLM;
* немає frontend UI;
* немає авторизації;
* немає Telegram bot;
* немає production deployment;
* немає real-time notifications;
* немає Excel export/import;
* немає semantic search;
* немає vector database.

Ці обмеження свідомо залишені поза MVP, щоб сфокусуватися на core AI Engineering workflow.

---

## 15. Можливий розвиток

Наступні кроки розвитку:

1. Замінити mock parser на реальний LLM parser.
2. Додати JSON schema validation для AI-виводу.
3. Додати guardrails для небезпечних або неповних змін.
4. Додати Telegram bot або простий frontend.
5. Додати пошук задач.
6. Додати Excel export/import.
7. Додати semantic search через embeddings.
8. Додати monitoring для AI parser якості.
9. Додати user authentication.
10. Додати dashboard по задачах.

---

## 16. Що треба вміти пояснити на захисті

На захисті треба пояснити:

1. Чому AI не пише напряму в базу.
2. Як працює preview → confirm.
3. Як raw text перетворюється в structured payload.
4. Чому mock parser можна замінити на реальний LLM.
5. Як backend розраховує статус задачі.
6. Як backend розраховує оцінку задачі.
7. Як працює task_events audit trail.
8. Як Docker Compose запускає систему.
9. Які є обмеження MVP.
10. Як можна розвивати систему далі.

---

## 17. Висновок

AI Task Capture System демонструє базовий production-oriented AI Engineering підхід:

```text
AI не приймає остаточне рішення самостійно.
AI готує structured output.
Backend валідовує і формує preview.
Користувач підтверджує.
Тільки після цього дані записуються в БД.
```

Це робить систему більш контрольованою, прозорою і придатною для реального використання.