from decimal import Decimal

from app.services.score_service import calculate_auto_task_score, round_to_nearest_half_hour


def test_score_is_none_when_task_type_base_hours_is_missing():
    score = calculate_auto_task_score(
        task_type_base_hours=None,
        priority_coefficient=Decimal("1.00"),
        complexity_coefficient=Decimal("2.00"),
    )

    assert score is None


def test_score_is_none_when_priority_coefficient_is_missing():
    score = calculate_auto_task_score(
        task_type_base_hours=Decimal("5.00"),
        priority_coefficient=None,
        complexity_coefficient=Decimal("2.00"),
    )

    assert score is None


def test_score_is_none_when_complexity_coefficient_is_missing():
    score = calculate_auto_task_score(
        task_type_base_hours=Decimal("5.00"),
        priority_coefficient=Decimal("1.00"),
        complexity_coefficient=None,
    )

    assert score is None


def test_score_for_pbi_high_complex_task():
    score = calculate_auto_task_score(
        task_type_base_hours=Decimal("8.00"),
        priority_coefficient=Decimal("0.80"),
        complexity_coefficient=Decimal("2.00"),
    )

    assert score == Decimal("13.00")


def test_score_for_db_critical_complex_task():
    score = calculate_auto_task_score(
        task_type_base_hours=Decimal("5.00"),
        priority_coefficient=Decimal("1.00"),
        complexity_coefficient=Decimal("2.00"),
    )

    assert score == Decimal("10.00")


def test_round_to_nearest_half_hour_rounds_down():
    result = round_to_nearest_half_hour(Decimal("1.74"))

    assert result == Decimal("1.50")


def test_round_to_nearest_half_hour_rounds_up():
    result = round_to_nearest_half_hour(Decimal("1.75"))

    assert result == Decimal("2.00")