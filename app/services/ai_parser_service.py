import re
from datetime import date

from app.schemas.ai_parser import AIParsedTaskPayload


def parse_task_text(
    raw_text: str,
    created_by: str | None = None,
) -> AIParsedTaskPayload:
    """
    Mock AI parser.

    In future this service can be replaced with real LLM call.
    For now it converts Ukrainian free text into structured task payload
    using simple deterministic rules.
    """

    cleaned_text = raw_text.strip()

    if not cleaned_text:
        raise ValueError("raw_text cannot be empty")

    lower_text = cleaned_text.lower()
    parser_notes: list[str] = []

    task_type_id = _detect_task_type_id(lower_text, parser_notes)
    priority_id = _detect_priority_id(lower_text, parser_notes)
    complexity_id = _detect_complexity_id(lower_text, parser_notes)
    business_area = _detect_business_area(lower_text, parser_notes)
    customer = _detect_customer(cleaned_text, parser_notes)
    planned_finish_date = _detect_planned_finish_date(lower_text, parser_notes)

    task_title = _build_task_title(cleaned_text)
    goal = _build_goal(cleaned_text)

    ai_confidence = _calculate_mock_confidence(
        task_type_id=task_type_id,
        priority_id=priority_id,
        complexity_id=complexity_id,
        business_area=business_area,
        planned_finish_date=planned_finish_date,
    )

    return AIParsedTaskPayload(
        task_title=task_title,
        goal=goal,
        task_type_id=task_type_id,
        business_area=business_area,
        customer=customer,
        priority_id=priority_id,
        complexity_id=complexity_id,
        executor=created_by,
        planned_finish_date=planned_finish_date,
        source_text=cleaned_text,
        ai_confidence=ai_confidence,
        created_by=created_by,
        parser_notes=parser_notes,
    )


def _build_task_title(raw_text: str) -> str:
    text = raw_text.strip()

    prefixes = [
        "додай задачу",
        "створи задачу",
        "потрібно",
        "треба",
        "зробити",
        "заведи задачу",
    ]

    lower_text = text.lower()

    for prefix in prefixes:
        if lower_text.startswith(prefix):
            text = text[len(prefix):].strip(" .:-")
            break

    if not text:
        return "Нова задача з тексту"

    if len(text) > 90:
        return text[:87].rstrip() + "..."

    return text


def _build_goal(raw_text: str) -> str:
    return f"Виконати задачу на основі вхідного тексту: {raw_text.strip()}"


def _detect_task_type_id(
    lower_text: str,
    parser_notes: list[str],
) -> int:
    """
    Dictionary mapping from seed data:
    1 - БД/Звіти
    2 - Звіти PBI
    3 - Запити
    4 - Звіти SSRS
    """

    if any(keyword in lower_text for keyword in ["power bi", "pbi", "дашборд", "dashboard", "звіт"]):
        parser_notes.append("Detected task type: Звіти PBI.")
        return 2

    if any(keyword in lower_text for keyword in ["ssrs"]):
        parser_notes.append("Detected task type: Звіти SSRS.")
        return 4

    if any(keyword in lower_text for keyword in ["sql", "бд", "база даних", "database"]):
        parser_notes.append("Detected task type: БД/Звіти.")
        return 1

    parser_notes.append("Task type was not detected confidently. Defaulted to Запити.")
    return 3


def _detect_priority_id(
    lower_text: str,
    parser_notes: list[str],
) -> int:
    """
    Dictionary mapping from seed data:
    1 - Critical
    2 - High
    3 - Medium
    4 - Low
    """

    if any(keyword in lower_text for keyword in ["критично", "critical", "терміново", "asap", "аварія"]):
        parser_notes.append("Detected priority: Critical.")
        return 1

    if any(keyword in lower_text for keyword in ["високий", "важливо", "high", "пріоритетна"]):
        parser_notes.append("Detected priority: High.")
        return 2

    if any(keyword in lower_text for keyword in ["низький", "не терміново", "low"]):
        parser_notes.append("Detected priority: Low.")
        return 4

    parser_notes.append("Priority was not detected confidently. Defaulted to Medium.")
    return 3


def _detect_complexity_id(
    lower_text: str,
    parser_notes: list[str],
) -> int:
    """
    Dictionary mapping from seed data:
    1 - Very Complex
    2 - Complex
    3 - Moderate
    4 - Easy
    """

    if any(keyword in lower_text for keyword in ["дуже склад", "very complex"]):
        parser_notes.append("Detected complexity: Very Complex.")
        return 1

    if any(keyword in lower_text for keyword in ["склад", "complex"]):
        parser_notes.append("Detected complexity: Complex.")
        return 2

    if any(keyword in lower_text for keyword in ["прост", "easy", "легко"]):
        parser_notes.append("Detected complexity: Easy.")
        return 4

    parser_notes.append("Complexity was not detected confidently. Defaulted to Moderate.")
    return 3


def _detect_business_area(
    lower_text: str,
    parser_notes: list[str],
) -> str | None:
    if "сільпо" in lower_text or "silpo" in lower_text:
        parser_notes.append("Detected business area: Сільпо.")
        return "Сільпо"

    if "фора" in lower_text or "fora" in lower_text:
        parser_notes.append("Detected business area: Фора.")
        return "Фора"

    if "it" in lower_text or "іт" in lower_text:
        parser_notes.append("Detected business area: IT.")
        return "IT"

    parser_notes.append("Business area was not detected.")
    return None


def _detect_customer(
    raw_text: str,
    parser_notes: list[str],
) -> str | None:
    patterns = [
        r"(?:для|замовник|клієнт)\s+([A-Za-zА-Яа-яІіЇїЄєҐґ0-9 _\"'-]{2,40})",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)

        if match:
            customer = match.group(1).strip(" .,:;")
            parser_notes.append(f"Detected customer: {customer}.")
            return customer

    parser_notes.append("Customer was not detected.")
    return None


def _detect_planned_finish_date(
    lower_text: str,
    parser_notes: list[str],
) -> date | None:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", lower_text)

    if not match:
        parser_notes.append("Planned finish date was not detected.")
        return None

    try:
        detected_date = date.fromisoformat(match.group(1))
    except ValueError:
        parser_notes.append("Detected date has invalid format.")
        return None

    parser_notes.append(f"Detected planned finish date: {detected_date.isoformat()}.")
    return detected_date


def _calculate_mock_confidence(
    task_type_id: int | None,
    priority_id: int | None,
    complexity_id: int | None,
    business_area: str | None,
    planned_finish_date: date | None,
) -> float:
    confidence = 0.50

    if task_type_id is not None:
        confidence += 0.10

    if priority_id is not None:
        confidence += 0.10

    if complexity_id is not None:
        confidence += 0.10

    if business_area is not None:
        confidence += 0.05

    if planned_finish_date is not None:
        confidence += 0.05

    return round(min(confidence, 0.90), 2)