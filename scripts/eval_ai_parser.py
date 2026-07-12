from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Callable

from app.config import settings
from app.schemas.ai_parser import AIParsedTaskPayload
from app.services.ai_parser_service import parse_task_text


EXPECTED_FIELD_MAP = {
    "expected_task_type_id": "task_type_id",
    "expected_priority_id": "priority_id",
    "expected_complexity_id": "complexity_id",
    "expected_business_area": "business_area",
    "expected_planned_finish_date": "planned_finish_date",
}


ParserFunc = Callable[[str, str | None], AIParsedTaskPayload]


def load_cases(path: Path) -> list[dict[str, Any]]:
    """
    Loads JSONL eval cases.
    """

    cases: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            try:
                cases.append(json.loads(cleaned_line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at line {line_number}: {error}") from error

    return cases


def date_to_iso(value: Any) -> str | None:
    """
    Converts date-like values to YYYY-MM-DD string for comparison.
    """

    if value is None:
        return None

    if isinstance(value, date):
        return value.isoformat()

    return str(value)


def evaluate_case(
    case: dict[str, Any],
    parser_func: ParserFunc = parse_task_text,
) -> dict[str, Any]:
    """
    Evaluates one parser case against expected structured fields.
    """

    raw_text = case["raw_text"]
    created_by = case.get("created_by")
    case_id = case.get("case_id", raw_text[:40])

    try:
        parsed = parser_func(raw_text=raw_text, created_by=created_by)
    except Exception as error:
        return {
            "case_id": case_id,
            "passed": 0,
            "total": 1,
            "score": 0.0,
            "checks": [
                {
                    "field": "parser_execution",
                    "expected": "success",
                    "actual": type(error).__name__,
                    "passed": False,
                    "detail": str(error),
                }
            ],
        }

    checks: list[dict[str, Any]] = []

    for expected_key, parsed_attr in EXPECTED_FIELD_MAP.items():
        if expected_key not in case:
            continue

        expected_value = case[expected_key]
        actual_value = getattr(parsed, parsed_attr)

        if parsed_attr == "planned_finish_date":
            actual_value = date_to_iso(actual_value)

        checks.append(
            {
                "field": parsed_attr,
                "expected": expected_value,
                "actual": actual_value,
                "passed": actual_value == expected_value,
            }
        )

    if case.get("check_title_non_empty", True):
        title_value = parsed.task_title.strip() if parsed.task_title else ""

        checks.append(
            {
                "field": "task_title_non_empty",
                "expected": True,
                "actual": bool(title_value),
                "passed": bool(title_value),
            }
        )

    total = len(checks)
    passed = sum(1 for check in checks if check["passed"])
    score = passed / total if total else 0.0

    return {
        "case_id": case_id,
        "passed": passed,
        "total": total,
        "score": score,
        "checks": checks,
    }


def run_evaluation(
    cases: list[dict[str, Any]],
    parser_func: ParserFunc = parse_task_text,
) -> dict[str, Any]:
    """
    Runs parser eval and returns aggregate metrics.
    """

    results = [
        evaluate_case(case=case, parser_func=parser_func)
        for case in cases
    ]

    total_checks = sum(result["total"] for result in results)
    passed_checks = sum(result["passed"] for result in results)
    overall_score = passed_checks / total_checks if total_checks else 0.0

    return {
        "provider": settings.ai_provider,
        "model": settings.openai_model if settings.ai_provider == "openai" else None,
        "total_cases": len(results),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "overall_score": overall_score,
        "results": results,
    }


def format_report(report: dict[str, Any], show_failures: bool = False) -> str:
    """
    Formats eval report as readable console output.
    """

    lines = [
        "AI Parser Eval Report",
        "=====================",
        f"Provider: {report['provider']}",
        f"Model: {report['model'] or '-'}",
        f"Cases: {report['total_cases']}",
        f"Checks: {report['passed_checks']} / {report['total_checks']}",
        f"Overall score: {report['overall_score']:.2%}",
    ]

    if show_failures:
        lines.append("")
        lines.append("Failures:")
        has_failures = False

        for result in report["results"]:
            failed_checks = [
                check for check in result["checks"]
                if not check["passed"]
            ]

            if not failed_checks:
                continue

            has_failures = True
            lines.append(f"- {result['case_id']}")

            for check in failed_checks:
                lines.append(
                    "  "
                    f"{check['field']}: "
                    f"expected={check['expected']!r}, "
                    f"actual={check['actual']!r}"
                )

        if not has_failures:
            lines.append("- no failures")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate AI parser quality.")
    parser.add_argument(
        "--cases",
        default="eval/openai_parser_cases.jsonl",
        help="Path to JSONL eval cases.",
    )
    parser.add_argument(
        "--min-overall",
        type=float,
        default=0.0,
        help="Optional minimum overall score. Example: 0.8",
    )
    parser.add_argument(
        "--show-failures",
        action="store_true",
        help="Show failed checks in console output.",
    )

    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    report = run_evaluation(cases)

    print(format_report(report, show_failures=args.show_failures))

    if report["overall_score"] < args.min_overall:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())