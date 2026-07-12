import json
import re
from datetime import date
from typing import Any

from app.config import settings
from app.schemas.ai_parser import AIParsedTaskPayload


TASK_TYPE_IDS = {
    "db_reports": 1,
    "pbi_reports": 2,
    "requests": 3,
    "ssrs_reports": 4,
}

PRIORITY_IDS = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
}

COMPLEXITY_IDS = {
    "very_complex": 1,
    "complex": 2,
    "moderate": 3,
    "easy": 4,
}


TASK_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "task_title",
        "goal",
        "task_type_id",
        "business_area",
        "customer",
        "priority_id",
        "complexity_id",
        "executor",
        "planned_finish_date",
        "ai_confidence",
        "parser_notes",
    ],
    "properties": {
        "task_title": {
            "type": "string",
            "description": "Short, clean Ukrainian task title.",
        },
        "goal": {
            "type": ["string", "null"],
            "description": "Clear business goal of the task in Ukrainian.",
        },
        "task_type_id": {
            "type": ["integer", "null"],
            "enum": [1, 2, 3, 4, None],
            "description": "1=БД/Звіти, 2=Звіти PBI, 3=Запити, 4=Звіти SSRS.",
        },
        "business_area": {
            "type": ["string", "null"],
            "description": "Business area, for example Сільпо, Фора, IT.",
        },
        "customer": {
            "type": ["string", "null"],
            "description": "Customer or requester. If unknown, use business area or null.",
        },
        "priority_id": {
            "type": ["integer", "null"],
            "enum": [1, 2, 3, 4, None],
            "description": "1=Critical, 2=High, 3=Medium, 4=Low.",
        },
        "complexity_id": {
            "type": ["integer", "null"],
            "enum": [1, 2, 3, 4, None],
            "description": "1=Very Complex, 2=Complex, 3=Moderate, 4=Easy.",
        },
        "executor": {
            "type": ["string", "null"],
            "description": "Executor name if present or provided by created_by.",
        },
        "planned_finish_date": {
            "type": ["string", "null"],
            "description": "Planned finish date in YYYY-MM-DD format or null.",
        },
        "ai_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence score from 0 to 1.",
        },
        "parser_notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Short parser notes in Ukrainian.",
        },
    },
}


def parse_task_text(raw_text: str, created_by: str | None = None) -> AIParsedTaskPayload:
    """
    Parses raw Ukrainian task text into a structured task payload.

    Provider selection:
    - AI_PROVIDER=mock: deterministic local parser for tests/offline mode.
    - AI_PROVIDER=openai: real LLM structured extraction via OpenAI API.
    """

    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must not be empty")

    cleaned_raw_text = raw_text.strip()

    provider = (settings.ai_provider or "mock").lower().strip()

    if provider == "openai":
        return parse_task_text_with_openai(
            raw_text=cleaned_raw_text,
            created_by=created_by,
        )

    return parse_task_text_with_mock(
        raw_text=cleaned_raw_text,
        created_by=created_by,
    )


def parse_task_text_with_openai(
    raw_text: str,
    created_by: str | None = None,
) -> AIParsedTaskPayload:
    """
    Uses a real LLM to convert messy raw text into a structured task payload.

    The model returns JSON that must match TASK_EXTRACTION_SCHEMA.
    """

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required when AI_PROVIDER=openai. "
            "Use AI_PROVIDER=mock for offline mode."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    system_prompt = """
Ти AI parser для системи ведення робочих задач.

Твоє завдання:
- прочитати сирий український текст або transcript голосової команди;
- зрозуміти сенс задачі;
- створити коротку, чисту і зрозумілу назву задачі українською;
- сформувати goal;
- визначити тип задачі;
- визначити бізнес-напрям;
- визначити замовника, якщо можливо;
- визначити пріоритет;
- визначити складність;
- визначити планову дату, якщо вона є;
- повернути тільки структуровані дані за JSON Schema.

Мапінг task_type_id:
1 = БД/Звіти
2 = Звіти PBI
3 = Запити
4 = Звіти SSRS

Мапінг priority_id:
1 = Critical
2 = High
3 = Medium
4 = Low

Мапінг complexity_id:
1 = Very Complex
2 = Complex
3 = Moderate
4 = Easy

Правила:
- Якщо текст неакуратний або голосовий — нормалізуй його.
- Не копіюй весь raw text у task_title.
- task_title має бути коротким і професійним.
- goal має пояснювати, який результат треба отримати.
- Якщо дата вказана словами, спробуй перетворити її у YYYY-MM-DD.
- Якщо поле неможливо визначити — поверни null.
- Якщо created_by відомий, його можна використати як executor.
"""

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": raw_text,
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "task_extraction",
                "strict": True,
                "schema": TASK_EXTRACTION_SCHEMA,
            }
        },
    )

    parsed_json = json.loads(response.output_text)

    parser_notes = parsed_json.get("parser_notes") or []
    parser_notes.append(f"provider=openai")
    parser_notes.append(f"model={settings.openai_model}")

    return AIParsedTaskPayload(
        task_title=parsed_json["task_title"],
        goal=parsed_json.get("goal"),
        task_type_id=parsed_json.get("task_type_id"),
        business_area=parsed_json.get("business_area"),
        customer=parsed_json.get("customer"),
        priority_id=parsed_json.get("priority_id"),
        complexity_id=parsed_json.get("complexity_id"),
        executor=parsed_json.get("executor") or created_by,
        planned_finish_date=parsed_json.get("planned_finish_date"),
        source_text=raw_text,
        ai_confidence=parsed_json.get("ai_confidence"),
        created_by=created_by,
        parser_notes=parser_notes,
    )


def parse_task_text_with_mock(
    raw_text: str,
    created_by: str | None = None,
) -> AIParsedTaskPayload:
    """
    Deterministic local parser.

    Used for:
    - offline development;
    - tests;
    - stable LMS verification without external API key.
    """

    normalized_text = _normalize_text(raw_text)

    task_title = _extract_title(raw_text)
    task_type_id = _detect_task_type(normalized_text)
    priority_id = _detect_priority(normalized_text)
    complexity_id = _detect_complexity(normalized_text)
    business_area = _detect_business_area(normalized_text)
    planned_finish_date = _extract_planned_finish_date(raw_text)

    parser_notes = [
        "provider=mock",
        "deterministic parser used for offline mode",
    ]

    return AIParsedTaskPayload(
        task_title=task_title,
        goal=f"Виконати задачу на основі вхідного тексту: {raw_text}",
        task_type_id=task_type_id,
        business_area=business_area,
        customer=business_area,
        priority_id=priority_id,
        complexity_id=complexity_id,
        executor=created_by,
        planned_finish_date=planned_finish_date,
        source_text=raw_text,
        ai_confidence=0.85,
        created_by=created_by,
        parser_notes=parser_notes,
    )


def _normalize_text(value: str) -> str:
    return value.lower().strip()


def _extract_title(raw_text: str) -> str:
    cleaned = raw_text.strip()

    prefixes = [
        "додай задачу",
        "створи задачу",
        "додати задачу",
        "треба",
        "потрібно",
    ]

    lowered = cleaned.lower()

    for prefix in prefixes:
        if lowered.startswith(prefix):
            return cleaned[len(prefix):].strip(" :,-") or cleaned

    return cleaned


def _detect_task_type(normalized_text: str) -> int:
    if "ssrs" in normalized_text:
        return TASK_TYPE_IDS["ssrs_reports"]

    db_keywords = [
        "sql",
        "бд",
        "база даних",
        "базі даних",
        "бази даних",
        "database",
    ]

    pbi_keywords = [
        "pbi",
        "power bi",
        "дашборд",
        "dashboard",
        "звіт",
        "звіту",
    ]

    if any(keyword in normalized_text for keyword in db_keywords):
        return TASK_TYPE_IDS["db_reports"]

    if any(keyword in normalized_text for keyword in pbi_keywords):
        return TASK_TYPE_IDS["pbi_reports"]

    return TASK_TYPE_IDS["requests"]


def _detect_priority(normalized_text: str) -> int:
    critical_keywords = [
        "критично",
        "critical",
        "терміново",
        "asap",
        "аварія",
    ]

    high_keywords = [
        "високий",
        "важливо",
        "high",
        "пріоритетна",
    ]

    low_keywords = [
        "низький",
        "не терміново",
        "low",
    ]

    if any(keyword in normalized_text for keyword in critical_keywords):
        return PRIORITY_IDS["critical"]

    if any(keyword in normalized_text for keyword in high_keywords):
        return PRIORITY_IDS["high"]

    if any(keyword in normalized_text for keyword in low_keywords):
        return PRIORITY_IDS["low"]

    return PRIORITY_IDS["medium"]


def _detect_complexity(normalized_text: str) -> int:
    if "дуже склад" in normalized_text or "very complex" in normalized_text:
        return COMPLEXITY_IDS["very_complex"]

    if "склад" in normalized_text or "complex" in normalized_text:
        return COMPLEXITY_IDS["complex"]

    if "прост" in normalized_text or "easy" in normalized_text or "легко" in normalized_text:
        return COMPLEXITY_IDS["easy"]

    return COMPLEXITY_IDS["moderate"]


def _detect_business_area(normalized_text: str) -> str | None:
    if "сільпо" in normalized_text or "silpo" in normalized_text:
        return "Сільпо"

    if "фора" in normalized_text or "fora" in normalized_text:
        return "Фора"

    if " it" in f" {normalized_text}" or "іт" in normalized_text:
        return "IT"

    return None


def _extract_planned_finish_date(raw_text: str) -> date | None:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", raw_text)

    if not match:
        return None

    return date.fromisoformat(match.group(1))