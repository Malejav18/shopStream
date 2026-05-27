from data_generator.generate_data import (
    generate_users,
    generate_products,
    generate_session_events,
    weighted_choice,
    COUNTRIES,
    DEVICES
)


def test_generate_users_count():
    users = generate_users(num_users=10, date_str="2026-05-25")

    assert len(users) == 10
    assert "user_id" in users[0]
    assert "country" in users[0]
    assert "customer_segment" in users[0]


def test_generate_products_count():
    products = generate_products(num_products=10)

    assert len(products) == 10
    assert "product_id" in products[0]
    assert "category" in products[0]
    assert "price" in products[0]


def test_weighted_choice_countries():
    value = weighted_choice(COUNTRIES)

    assert value in COUNTRIES.keys()


def test_weighted_choice_devices():
    value = weighted_choice(DEVICES)

    assert value in DEVICES.keys()


def test_generate_session_events_structure():
    users = generate_users(num_users=1, date_str="2026-05-25")
    products = generate_products(num_products=10)

    session, events, transactions, cart_items = generate_session_events(
        user=users[0],
        products=products,
        date_str="2026-05-25"
    )

    assert "session_id" in session
    assert "user_id" in session
    assert isinstance(events, list)
    assert len(events) >= 1
    assert "event_type" in events[0]


def test_session_events_have_valid_event_types():
    users = generate_users(num_users=1, date_str="2026-05-25")
    products = generate_products(num_products=10)

    _, events, _, _ = generate_session_events(
        user=users[0],
        products=products,
        date_str="2026-05-25"
    )

    valid_types = {
        "page_view",
        "click",
        "search",
        "product_view",
        "cart_event"
    }

    for event in events:
        assert event["event_type"] in valid_types


def test_product_prices_are_positive():
    products = generate_products(num_products=50)

    for product in products:
        assert product["price"] >= 0


def test_users_have_valid_countries():
    users = generate_users(num_users=50, date_str="2026-05-25")

    for user in users:
        assert user["country"] in COUNTRIES.keys()
