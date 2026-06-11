from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.dictionaries import (
    ComplexityDict,
    PriorityDict,
    TaskScoreMatrix,
    TaskTypeDict,
)



def upsert_priority_dict(db: Session) -> None:
    priorities = [
        {
            "id": 1,
            "code": "critical",
            "name": "Critical",
            "description": "Задача безпосередньо впливає на бізнес, її невиконання може зупинити процеси.",
            "response_time": "негайно",
            "coefficient": Decimal("1.00"),
            "sort_order": 1,
            "is_active": True,
        },
        {
            "id": 2,
            "code": "high",
            "name": "High",
            "description": "Задача впливає на ефективність роботи, але процеси можуть продовжуватися.",
            "response_time": "до 2 днів",
            "coefficient": Decimal("0.80"),
            "sort_order": 2,
            "is_active": True,
        },
        {
            "id": 3,
            "code": "medium",
            "name": "Medium",
            "description": "Важлива задача, але її можна трохи відкласти без серйозних наслідків.",
            "response_time": "до 1 тижня",
            "coefficient": Decimal("0.60"),
            "sort_order": 3,
            "is_active": True,
        },
        {
            "id": 4,
            "code": "low",
            "name": "Low",
            "description": "Задача не впливає на поточні процеси, можна виконати у вільний час.",
            "response_time": "коли буде можливість",
            "coefficient": Decimal("0.50"),
            "sort_order": 4,
            "is_active": True,
        },
    ]

    for item in priorities:
        existing = db.query(PriorityDict).filter(PriorityDict.code == item["code"]).first()

        if existing:
            for key, value in item.items():
                setattr(existing, key, value)
        else:
            db.add(PriorityDict(**item))


def upsert_complexity_dict(db: Session) -> None:
    complexities = [
        {
            "id": 1,
            "code": "very_complex",
            "name": "Very Complex",
            "description": "Потрібне стратегічне планування, узгодження з бізнесом або інтеграція різних систем.",
            "expected_duration": "від тижня і більше",
            "coefficient": Decimal("3.00"),
            "sort_order": 1,
            "is_active": True,
        },
        {
            "id": 2,
            "code": "complex",
            "name": "Complex",
            "description": "Потрібні зміни в кількох системах, інтеграція або переробка існуючої логіки.",
            "expected_duration": "до 7 робочих днів",
            "coefficient": Decimal("2.00"),
            "sort_order": 2,
            "is_active": True,
        },
        {
            "id": 3,
            "code": "moderate",
            "name": "Moderate",
            "description": "Потрібен аналіз, робота з даними або тестування.",
            "expected_duration": "до 2 робочих днів",
            "coefficient": Decimal("1.50"),
            "sort_order": 3,
            "is_active": True,
        },
        {
            "id": 4,
            "code": "easy",
            "name": "Easy",
            "description": "Стандартна задача без складного аналізу або складної логіки.",
            "expected_duration": "до 2 годин",
            "coefficient": Decimal("1.00"),
            "sort_order": 4,
            "is_active": True,
        },
    ]

    for item in complexities:
        existing = db.query(ComplexityDict).filter(ComplexityDict.code == item["code"]).first()

        if existing:
            for key, value in item.items():
                setattr(existing, key, value)
        else:
            db.add(ComplexityDict(**item))


def upsert_task_type_dict(db: Session) -> None:
    task_types = [
        {
            "id": 1,
            "code": "db_reports",
            "name": "БД/Звіти",
            "base_hours": Decimal("5.00"),
            "sort_order": 1,
            "is_active": True,
        },
        {
            "id": 2,
            "code": "pbi_reports",
            "name": "Звіти PBI",
            "base_hours": Decimal("8.00"),
            "sort_order": 2,
            "is_active": True,
        },
        {
            "id": 3,
            "code": "requests",
            "name": "Запити",
            "base_hours": Decimal("3.00"),
            "sort_order": 3,
            "is_active": True,
        },
        {
            "id": 4,
            "code": "ssrs_reports",
            "name": "Звіти SSRS",
            "base_hours": Decimal("5.00"),
            "sort_order": 4,
            "is_active": True,
        },
    ]

    for item in task_types:
        existing = db.query(TaskTypeDict).filter(TaskTypeDict.code == item["code"]).first()

        if existing:
            for key, value in item.items():
                setattr(existing, key, value)
        else:
            db.add(TaskTypeDict(**item))


def upsert_task_score_matrix(db: Session) -> None:
    priorities = [
        ("critical", Decimal("1.00")),
        ("high", Decimal("0.80")),
        ("medium", Decimal("0.60")),
        ("low", Decimal("0.50")),
    ]

    complexities = [
        ("very_complex", Decimal("3.00")),
        ("complex", Decimal("2.00")),
        ("moderate", Decimal("1.50")),
        ("easy", Decimal("1.00")),
    ]

    for priority_code, priority_coefficient in priorities:
        for complexity_code, complexity_coefficient in complexities:
            multiplier = priority_coefficient * complexity_coefficient

            existing = (
                db.query(TaskScoreMatrix)
                .filter(
                    TaskScoreMatrix.priority_code == priority_code,
                    TaskScoreMatrix.complexity_code == complexity_code,
                )
                .first()
            )

            if existing:
                existing.score_multiplier = multiplier
                existing.comment = "Автоматично згенерований коефіцієнт."
                existing.is_active = True
            else:
                db.add(
                    TaskScoreMatrix(
                        priority_code=priority_code,
                        complexity_code=complexity_code,
                        score_multiplier=multiplier,
                        comment="Автоматично згенерований коефіцієнт.",
                        is_active=True,
                    )
                )

def reset_sequences(db: Session) -> None:
    """
    Resets PostgreSQL sequences after manual inserts with explicit IDs.

    This prevents duplicate key errors when new records are added later
    without manually specified IDs.
    """

    sequence_queries = [
        """
        SELECT setval(
            pg_get_serial_sequence('priority_dict', 'id'),
            COALESCE((SELECT MAX(id) FROM priority_dict), 1),
            true
        )
        """,
        """
        SELECT setval(
            pg_get_serial_sequence('complexity_dict', 'id'),
            COALESCE((SELECT MAX(id) FROM complexity_dict), 1),
            true
        )
        """,
        """
        SELECT setval(
            pg_get_serial_sequence('task_type_dict', 'id'),
            COALESCE((SELECT MAX(id) FROM task_type_dict), 1),
            true
        )
        """,
        """
        SELECT setval(
            pg_get_serial_sequence('task_score_matrix', 'id'),
            COALESCE((SELECT MAX(id) FROM task_score_matrix), 1),
            true
        )
        """,
    ]

    for query in sequence_queries:
        db.execute(text(query))

def seed_dictionaries() -> None:
    db = SessionLocal()

    try:
        upsert_priority_dict(db)
        upsert_complexity_dict(db)
        upsert_task_type_dict(db)
        upsert_task_score_matrix(db)
        reset_sequences(db)

        db.commit()

        print("Dictionaries seeded successfully.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_dictionaries()