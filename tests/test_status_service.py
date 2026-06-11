from datetime import date, timedelta

from app.services.status_service import (
    STATUS_DONE,
    STATUS_EVALUATION,
    STATUS_IN_PROGRESS,
    STATUS_NEW,
    STATUS_PLANNED,
    calculate_auto_status,
)


def test_status_is_done_when_fact_finish_date_exists():
    status = calculate_auto_status(
        priority_id=None,
        complexity_id=None,
        fact_start_date=None,
        fact_finish_date=date(2026, 6, 11),
        today=date(2026, 6, 11),
    )

    assert status == STATUS_DONE


def test_status_is_evaluation_when_priority_is_missing():
    status = calculate_auto_status(
        priority_id=None,
        complexity_id=1,
        fact_start_date=None,
        fact_finish_date=None,
        today=date(2026, 6, 11),
    )

    assert status == STATUS_EVALUATION


def test_status_is_evaluation_when_complexity_is_missing():
    status = calculate_auto_status(
        priority_id=1,
        complexity_id=None,
        fact_start_date=None,
        fact_finish_date=None,
        today=date(2026, 6, 11),
    )

    assert status == STATUS_EVALUATION


def test_status_is_new_when_priority_and_complexity_exist_but_start_is_missing():
    status = calculate_auto_status(
        priority_id=1,
        complexity_id=1,
        fact_start_date=None,
        fact_finish_date=None,
        today=date(2026, 6, 11),
    )

    assert status == STATUS_NEW


def test_status_is_in_progress_when_start_date_is_today():
    today = date(2026, 6, 11)

    status = calculate_auto_status(
        priority_id=1,
        complexity_id=1,
        fact_start_date=today,
        fact_finish_date=None,
        today=today,
    )

    assert status == STATUS_IN_PROGRESS


def test_status_is_in_progress_when_start_date_is_in_past():
    today = date(2026, 6, 11)

    status = calculate_auto_status(
        priority_id=1,
        complexity_id=1,
        fact_start_date=today - timedelta(days=1),
        fact_finish_date=None,
        today=today,
    )

    assert status == STATUS_IN_PROGRESS


def test_status_is_planned_when_start_date_is_in_future():
    today = date(2026, 6, 11)

    status = calculate_auto_status(
        priority_id=1,
        complexity_id=1,
        fact_start_date=today + timedelta(days=1),
        fact_finish_date=None,
        today=today,
    )

    assert status == STATUS_PLANNED