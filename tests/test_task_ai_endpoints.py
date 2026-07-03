from fastapi.testclient import TestClient

import app.routers.tasks as tasks_router
from app.main import app


client = TestClient(app)


def test_ai_preview_returns_400_for_blank_raw_text():
    response = client.post(
        "/tasks/ai-preview",
        json={
            "raw_text": "   ",
            "created_by": "Кондес П.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "raw_text must not be empty"


def test_voice_preview_returns_400_for_blank_transcript():
    response = client.post(
        "/tasks/voice-preview",
        json={
            "transcript": "   ",
            "created_by": "Кондес П.",
            "language": "uk-UA",
            "speech_confidence": 0.91,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "raw_text must not be empty"


def test_ai_preview_returns_503_when_parser_provider_is_unavailable(monkeypatch):
    def fake_parse_task_text(raw_text: str, created_by: str | None = None):
        raise RuntimeError(
            "OPENAI_API_KEY is required when AI_PROVIDER=openai. "
            "Use AI_PROVIDER=mock for offline mode."
        )

    monkeypatch.setattr(tasks_router, "parse_task_text", fake_parse_task_text)

    response = client.post(
        "/tasks/ai-preview",
        json={
            "raw_text": "Додай задачу по PBI звіту для Сільпо",
            "created_by": "Кондес П.",
        },
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY is required" in response.json()["detail"]