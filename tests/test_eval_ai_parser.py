from datetime import date

from app.schemas.ai_parser import AIParsedTaskPayload
from scripts.eval_ai_parser import date_to_iso, run_evaluation


def fake_parser(raw_text: str, created_by: str | None = None) -> AIParsedTaskPayload:
    return AIParsedTaskPayload(
        task_title="Перевірити PBI звіт для Сільпо",
        goal="Перевірити коректність PBI звіту для бізнес-напряму Сільпо.",
        task_type_id=2,
        business_area="Сільпо",
        customer="Сільпо",
        priority_id=2,
        complexity_id=2,
        executor=created_by,
        planned_finish_date=date(2026, 7, 1),
        source_text=raw_text,
        ai_confidence=0.9,
        created_by=created_by,
        parser_notes=["test parser"],
    )


def test_date_to_iso_converts_date_value():
    assert date_to_iso(date(2026, 7, 1)) == "2026-07-01"


def test_date_to_iso_keeps_none():
    assert date_to_iso(None) is None


def test_run_evaluation_returns_full_score_for_matching_case():
    cases = [
        {
            "case_id": "matching_case",
            "raw_text": "Додай задачу по PBI звіту для Сільпо",
            "created_by": "Кондес П.",
            "expected_task_type_id": 2,
            "expected_priority_id": 2,
            "expected_complexity_id": 2,
            "expected_business_area": "Сільпо",
            "expected_planned_finish_date": "2026-07-01",
        }
    ]

    report = run_evaluation(cases=cases, parser_func=fake_parser)

    assert report["total_cases"] == 1
    assert report["overall_score"] == 1.0
    assert report["passed_checks"] == report["total_checks"]


def test_run_evaluation_reports_field_mismatch():
    cases = [
        {
            "case_id": "priority_mismatch",
            "raw_text": "Додай задачу по PBI звіту для Сільпо",
            "created_by": "Кондес П.",
            "expected_task_type_id": 2,
            "expected_priority_id": 1,
            "expected_complexity_id": 2,
            "expected_business_area": "Сільпо",
            "expected_planned_finish_date": "2026-07-01",
        }
    ]

    report = run_evaluation(cases=cases, parser_func=fake_parser)

    assert report["total_cases"] == 1
    assert report["overall_score"] < 1.0

    failed_checks = [
        check
        for check in report["results"][0]["checks"]
        if not check["passed"]
    ]

    assert len(failed_checks) == 1
    assert failed_checks[0]["field"] == "priority_id"