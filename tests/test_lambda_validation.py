from lambda_ingestion.lambda_function import validate_event, is_valid_iso_timestamp, build_validated_key, build_quarantine_key


def test_valid_iso_timestamp():
    assert is_valid_iso_timestamp("2026-05-25T10:00:00Z") is True


def test_invalid_iso_timestamp():
    assert is_valid_iso_timestamp("fecha-mala") is False


def test_valid_page_view_event():
    event = {
        "event_id": "evt_1",
        "event_type": "page_view",
        "user_id": "user_1",
        "session_id": "session_1",
        "page_url": "/",
        "page_type": "home",
        "timestamp": "2026-05-25T10:00:00Z",
        "time_on_page_seconds": 60,
        "referrer": "google",
        "device_type": "mobile",
        "country": "CO"
    }

    assert validate_event(event) is None


def test_page_view_missing_required_field():
    event = {
        "event_id": "evt_1",
        "event_type": "page_view",
        "user_id": "user_1",
        "session_id": "session_1",
        "page_url": "/",
        "page_type": "home",
        "timestamp": "2026-05-25T10:00:00Z",
        "time_on_page_seconds": 60,
        "device_type": "mobile",
        "country": "CO"
    }

    error = validate_event(event)

    assert error is not None
    assert "referrer" in error


def test_page_view_negative_time():
    event = {
        "event_id": "evt_1",
        "event_type": "page_view",
        "user_id": "user_1",
        "session_id": "session_1",
        "page_url": "/",
        "page_type": "home",
        "timestamp": "2026-05-25T10:00:00Z",
        "time_on_page_seconds": -10,
        "referrer": "google",
        "device_type": "mobile",
        "country": "CO"
    }

    error = validate_event(event)

    assert error is not None
    assert "negativo" in error


def test_valid_cart_event():
    event = {
        "event_id": "evt_2",
        "event_type": "cart_event",
        "user_id": "user_1",
        "session_id": "session_1",
        "product_id": "prod_1",
        "action": "add",
        "timestamp": "2026-05-25T10:05:00Z"
    }

    assert validate_event(event) is None


def test_invalid_cart_action():
    event = {
        "event_id": "evt_2",
        "event_type": "cart_event",
        "user_id": "user_1",
        "session_id": "session_1",
        "product_id": "prod_1",
        "action": "delete",
        "timestamp": "2026-05-25T10:05:00Z"
    }

    error = validate_event(event)

    assert error is not None
    assert "action" in error


def test_invalid_event_type():
    event = {
        "event_id": "evt_3",
        "event_type": "purchase_fake",
        "timestamp": "2026-05-25T10:05:00Z"
    }

    error = validate_event(event)

    assert error is not None
    assert "event_type" in error


def test_build_validated_key():
    key = "raw/events/year=2026/month=05/day=25/events.jsonl"

    result = build_validated_key(key)

    assert result == "validated/events/year=2026/month=05/day=25/events.jsonl"


def test_build_quarantine_key():
    key = "raw/events/year=2026/month=05/day=25/events.jsonl"

    result = build_quarantine_key(key)

    assert result == "quarantine/raw/events/year=2026/month=05/day=25/events.jsonl"
