from datetime import date


STATUS_EVALUATION = "Оцінка"
STATUS_NEW = "Нова"
STATUS_IN_PROGRESS = "В роботі"
STATUS_PLANNED = "План"
STATUS_DONE = "Виконано"


def calculate_auto_status(
    priority_id: int | None,
    complexity_id: int | None,
    fact_start_date: date | None,
    fact_finish_date: date | None,
    today: date | None = None,
) -> str:
    """
    Calculates task auto status based on deterministic business rules.

    Rules:
    1. If fact finish date exists -> Виконано.
    2. If priority or complexity is missing -> Оцінка.
    3. If priority and complexity exist but fact start date is missing -> Нова.
    4. If fact start date is today or in the past -> В роботі.
    5. If fact start date is in the future -> План.

    The 'today' parameter is injectable to make tests stable.
    """

    current_date = today or date.today()

    if fact_finish_date is not None:
        return STATUS_DONE

    if priority_id is None or complexity_id is None:
        return STATUS_EVALUATION

    if fact_start_date is None:
        return STATUS_NEW

    if fact_start_date <= current_date:
        return STATUS_IN_PROGRESS

    return STATUS_PLANNED