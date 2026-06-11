from decimal import Decimal, ROUND_HALF_UP


SCORE_STEP = Decimal("0.50")


def round_to_nearest_half_hour(value: Decimal) -> Decimal:
    """
    Rounds a Decimal value to the nearest 0.5 hour.

    Examples:
    1.74 -> 1.50
    1.75 -> 2.00
    12.80 -> 13.00
    """

    return (value / SCORE_STEP).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * SCORE_STEP


def calculate_auto_task_score(
    task_type_base_hours: Decimal | None,
    priority_coefficient: Decimal | None,
    complexity_coefficient: Decimal | None,
) -> Decimal | None:
    """
    Calculates automatic task score.

    Formula:
    auto_task_score = task_type_base_hours * priority_coefficient * complexity_coefficient

    If one of the required values is missing, returns None.
    """

    if (
        task_type_base_hours is None
        or priority_coefficient is None
        or complexity_coefficient is None
    ):
        return None

    raw_score = task_type_base_hours * priority_coefficient * complexity_coefficient

    return round_to_nearest_half_hour(raw_score)