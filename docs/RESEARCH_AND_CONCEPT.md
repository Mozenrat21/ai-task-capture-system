# Research and Concept — AI Task Capture System

## 1. Назва проєкту

**AI Task Capture System**

MVP-система для фіксації, структуризації, голосового або текстового введення, контролю та аналізу робочих задач із використанням AI Engineering підходу.

---

## 2. Проблема

У щоденній роботі задачі часто виникають у неструктурованому вигляді:

* у чатах;
* у листуванні;
* у голосових нотатках;
* у швидких усних формулюваннях;
* у Excel;
* у коротких повідомленнях від замовників;
* у власних робочих записах.

Користувач не завжди має час або бажання вручну заповнювати форму задачі. Часто простіше швидко сказати або написати:

```text
Додай складну задачу по PBI звіту для Сільпо, високий пріоритет, до 2026-07-01
```

Але така команда сама по собі не є структурованою задачею. Її потрібно перетворити на набір контрольованих полів:

* назва задачі;
* ціль;
* тип задачі;
* бізнес-напрям;
* замовник;
* пріоритет;
* складність;
* планова дата;
* виконавець;
* статус;
* історія змін.

Також є ризик, що AI або parser може помилитися. Тому система не повинна записувати результат напряму в базу без перевірки користувачем.

---

## 3. Ідея рішення

Ідея проєкту — створити backend-систему, яка приймає задачу у вигляді тексту або transcript голосової команди, перетворює її у structured payload, формує preview змін і записує результат у базу тільки після підтвердження користувачем.

Основний workflow:

```text
text input / voice transcript
→ AI parser
→ structured payload
→ preview
→ confirm
→ PostgreSQL
→ task_events
```

Для голосового сценарію pipeline виглядає так:

```text
voice command
→ Speech-to-Text
→ transcript
→ AI parser
→ structured payload
→ preview
→ user confirmation
→ database write
```

У межах MVP система не обробляє audio-файл напряму. Реалізовано voice-ready сценарій: endpoint приймає вже розпізнаний transcript голосової команди та запускає той самий AI workflow, що й для текстового введення.

---

## 4. Чому обрана саме ця тема

Тема обрана тому, що вона поєднує реальну робочу проблему з ключовими темами AI Engineering:

* робота з неструктурованим текстом;
* голосове введення як потенційний input channel;
* structured output;
* backend API;
* валідація AI-виводу;
* human-in-the-loop;
* preview before write;
* PostgreSQL як основне сховище;
* audit trail;
* Docker Compose;
* тести;
* production-oriented architecture.

Проєкт не є просто CRUD-додатком. Його головна ідея — показати, як AI може допомагати створювати й оновлювати задачі, але не мати неконтрольованого доступу до запису в базу.

---

## 5. Цільовий користувач

Основний користувач MVP:

* аналітик;
* BI-розробник;
* AI engineer;
* технічний спеціаліст;
* людина, яка отримує багато задач із різних джерел.

Типовий сценарій:

```text
Користувач отримує задачу або формулює її сам.
Він пише або диктує коротку команду.
Система перетворює текст / transcript у structured payload.
Користувач бачить preview.
Після підтвердження задача записується в PostgreSQL.
```

---

## 6. Real AI parser scope

Початково MVP використовував deterministic mock parser, щоб забезпечити стабільність локальної перевірки.

Після доопрацювання додано provider-based AI parser:

```text
AI_PROVIDER=mock
AI_PROVIDER=openai
```

Це дозволяє розділити два сценарії:

1. **Offline verification** — перевіряючий може запустити проєкт без API ключа.
2. **Real AI extraction** — при наявності OpenAI API key система може використовувати LLM для осмислення сирого тексту або transcript голосової команди.

У режимі `openai` система вирішує саме ту задачу, для якої створювався проєкт:

```text
сирий неструктурований текст
→ AI осмислення
→ гарна назва задачі
→ goal
→ тип задачі
→ пріоритет
→ складність
→ preview
→ confirm
```

Mock provider не є фінальною AI-логікою. Він потрібен як стабільний fallback для тестів, локального запуску і здачі без зовнішніх секретів.

---

## 7. Очікуваний результат MVP

Очікуваний результат MVP — працююча backend-система, яка:

1. запускається локально через Docker Compose;
2. має FastAPI backend;
3. використовує PostgreSQL як основне сховище;
4. має міграції через Alembic;
5. має seed-довідники;
6. підтримує життєвий цикл задачі;
7. використовує preview → confirm pattern;
8. зберігає історію змін у task_events;
9. має provider-based AI parser;
10. має mock fallback provider;
11. має optional OpenAI LLM provider;
12. дозволяє створювати задачу з українського тексту;
13. дозволяє створювати задачу з transcript голосової команди;
14. має тести;
15. має документацію для запуску й пояснення архітектури.

---

## 8. Межі MVP

До MVP входить:

* обробка текстового введення;
* обробка transcript голосової команди;
* створення preview задачі з raw text;
* створення preview задачі з voice transcript;
* provider-based AI parser;
* optional real LLM parser через OpenAI provider;
* mock fallback parser для запуску без API ключа;
* підтвердження preview;
* створення задачі;
* старт задачі;
* планування задачі;
* постановка на паузу;
* повернення в роботу;
* оновлення задачі;
* закриття задачі;
* перегляд задач;
* перегляд історії змін;
* автоматичний статус;
* автоматична оцінка задачі;
* Docker-запуск;
* тести.

Поза межами MVP залишено:

* пряме завантаження audio-файлу;
* власний speech-to-text engine;
* frontend UI;
* Telegram bot;
* авторизацію;
* production deployment;
* Excel export/import;
* vector database;
* RAG;
* semantic search;
* monitoring dashboard.

Ці речі можна додати в майбутньому, але для курсового MVP головний фокус зроблено на core AI Engineering workflow.

---

## 9. Voice-ready scope

Початкова ідея проєкту включає не тільки текстове введення, а й голосове управління задачами.

У production-сценарії голосовий pipeline має виглядати так:

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

У межах поточного MVP реалізовано частину після Speech-to-Text:

```text
transcript
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

Повноцінна обробка audio-файлу залишена за межами MVP, оскільки це окрема інтеграція зі speech-to-text сервісом, наприклад Whisper, OpenAI Audio API, Google Speech-to-Text або іншим STT-рішенням.

---

## 10. Чому потрібен preview → confirm

AI-системи можуть помилятися:

* неправильно визначити тип задачі;
* неправильно визначити пріоритет;
* пропустити дату;
* некоректно витягнути замовника;
* створити неповний payload;
* помилково інтерпретувати голосову команду.

Тому система не дозволяє AI напряму змінювати дані.

Обраний патерн:

```text
AI output → backend validation → preview → user confirmation → database write
```

Переваги:

| Перевага        | Пояснення                                        |
| --------------- | ------------------------------------------------ |
| Контроль        | Користувач бачить, що саме буде записано         |
| Безпека         | AI не має прямого запису в БД                    |
| Прозорість      | Усі зміни видно до підтвердження                 |
| Audit trail     | Після підтвердження зміни пишуться в task_events |
| Масштабованість | Патерн можна застосувати до інших AI workflows   |

---

## 11. Вибір технологій

| Технологія      | Чому використовується                                 |
| --------------- | ----------------------------------------------------- |
| FastAPI         | API layer, Swagger UI, Pydantic validation            |
| PostgreSQL      | Надійне structured data сховище                       |
| SQLAlchemy      | ORM для моделей і роботи з БД                         |
| Alembic         | Контрольовані міграції                                |
| OpenAI provider | Реальна AI-обробка сирого тексту в structured payload |
| Mock provider   | Стабільна перевірка без зовнішнього API ключа         |
| Docker Compose  | Відтворюваний локальний запуск                        |
| Pytest          | Перевірка бізнес-логіки                               |
| Adminer         | Простий перегляд PostgreSQL                           |

---

## 12. Чому це AI Engineering проєкт

Проєкт демонструє важливі AI Engineering принципи:

1. **Structured output**
   Неструктурований текст або transcript перетворюється у structured payload.

2. **Provider-based AI architecture**
   Є mock fallback і optional OpenAI LLM provider.

3. **Human-in-the-loop**
   Користувач підтверджує запропоновані зміни.

4. **Validation before write**
   Дані не записуються одразу в базу.

5. **Replaceable AI component**
   Parser винесено в service layer, тому provider можна замінити або розширити.

6. **Voice-ready architecture**
   Система готова приймати transcript голосової команди.

7. **Auditability**
   Усі підтверджені зміни пишуться в task_events.

8. **Production-like setup**
   Docker Compose, PostgreSQL, Alembic, тести.

---

## 13. Альтернативи, які розглядалися

### Excel

Плюси:

* швидко;
* знайомий інструмент.

Мінуси:

* немає API;
* немає audit trail;
* немає контрольованого AI workflow;
* складно масштабувати.

### Простий CRUD API

Плюси:

* швидше реалізувати.

Мінуси:

* немає AI Engineering складової;
* немає preview/confirm;
* менше цінності для курсу.

### Тільки real LLM без fallback

Плюси:

* сильна AI-складова.

Мінуси:

* потрібні API keys;
* тести стають нестабільними;
* перевірка залежить від зовнішнього сервісу.

### Обране рішення

Обрано provider-based підхід:

```text
AI_PROVIDER=mock
AI_PROVIDER=openai
```

Це дає баланс:

* стабільна перевірка без ключа;
* реальна AI-інтеграція при наявності OpenAI API key;
* правильна архітектура для розвитку.

---

## 14. Ризики та обмеження

| Ризик                           | Як зменшується                    |
| ------------------------------- | --------------------------------- |
| AI неправильно розпізнає задачу | preview перед записом             |
| Некоректні статуси              | статус рахує backend              |
| Неправильна оцінка задачі       | score рахується за довідниками    |
| Втрата історії змін             | task_events                       |
| Складний запуск                 | Docker Compose                    |
| Відсутність API key             | mock fallback provider            |
| Нестабільність зовнішнього LLM  | fallback + тести на mock provider |
| Неконтрольований запис          | confirm required                  |

---

## 15. Як перевірити результат

Мінімальний smoke-test:

```powershell
docker compose up -d --build
Invoke-RestMethod http://localhost:8000/health
python -m pytest
```

Очікувано:

```text
database = ok
19 passed
```

Основні endpoints:

```http
POST /tasks/ai-preview
POST /tasks/voice-preview
POST /tasks/confirm
GET /tasks/{id}
GET /tasks/{id}/events
```

---

## 16. Очікуваний фінальний результат

Фінальний результат MVP:

* користувач може ввести задачу українською мовою;
* користувач може передати transcript голосової команди;
* система перетворює текст / transcript у structured payload;
* у режимі `openai` система використовує реальний LLM parser;
* у режимі `mock` система працює без зовнішнього API ключа;
* система формує preview;
* користувач підтверджує preview;
* задача записується в PostgreSQL;
* зміни логуються в task_events;
* проєкт запускається через Docker Compose;
* є документація;
* є тести.

---

## 17. Висновок

AI Task Capture System демонструє production-oriented AI Engineering підхід.

Головна ідея:

```text
AI допомагає структурувати задачі, але не приймає остаточне рішення без користувача.
```

У межах MVP реалізовано:

* текстове введення;
* voice-ready сценарій через transcript;
* provider-based AI parser;
* optional OpenAI LLM provider;
* mock fallback provider;
* preview → confirm;
* audit trail;
* Docker-запуск;
* тести.

Це робить систему контрольованою, прозорою та придатною для подальшого розвитку в реальний робочий AI-powered інструмент.
