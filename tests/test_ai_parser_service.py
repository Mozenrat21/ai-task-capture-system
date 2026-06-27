import pytest

from app.services.ai_parser_service import parse_task_text


def test_parse_task_text_detects_pbi_task():
    result = parse_task_text(
        raw_text="Додай складну задачу по PBI звіту для IT, високий пріоритет",
        created_by="Кондес П.",
    )

    assert result.task_type_id == 2
    assert result.priority_id == 2
    assert result.complexity_id == 2
    assert result.business_area == "IT"
    assert result.executor == "Кондес П."
    assert result.created_by == "Кондес П."
    assert result.source_text.startswith("Додай складну задачу")


def test_parse_task_text_detects_critical_request():
    result = parse_task_text(
        raw_text="Терміново заведи задачу для бізнесу, аварія в сервісі",
        created_by="Кондес П.",
    )

    assert result.task_type_id == 3
    assert result.priority_id == 1
    assert result.business_area == "Сільпо"
    assert result.ai_confidence is not None
    assert result.ai_confidence >= 0.7


def test_parse_task_text_detects_iso_date():
    result = parse_task_text(
        raw_text="Потрібно зробити просту задачу до 2026-07-01",
        created_by="Кондес П.",
    )

    assert result.planned_finish_date is not None
    assert result.planned_finish_date.isoformat() == "2026-07-01"
    assert result.complexity_id == 4


def test_parse_task_text_rejects_empty_text():
    with pytest.raises(ValueError):
        parse_task_text(raw_text="   ")