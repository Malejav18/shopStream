import argparse
import csv
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any


COUNTRIES = {
    "CO": 0.35,
    "MX": 0.18,
    "US": 0.15,
    "BR": 0.12,
    "AR": 0.08,
    "CL": 0.06,
    "PE": 0.06,
}

DEVICES = {
    "mobile": 0.55,
    "desktop": 0.30,
    "tablet": 0.15,
}

CUSTOMER_SEGMENTS = {
    "new": 0.35,
    "returning": 0.45,
    "premium": 0.20,
}

PAGE_TYPES = {
    "home": 0.20,
    "category": 0.20,
    "product": 0.30,
    "search": 0.15,
    "cart": 0.10,
    "checkout": 0.05,
}

REFERRERS = {
    "google": 0.35,
    "facebook": 0.15,
    "instagram": 0.15,
    "direct": 0.20,
    "email": 0.10,
    "tiktok": 0.05,
}

PRODUCT_CATEGORIES = [
    "electronics",
    "fashion",
    "home",
    "sports",
    "beauty",
    "books",
    "toys",
    "gaming",
]

SEARCH_TERMS = [
    "laptop",
    "tennis shoes",
    "phone",
    "headphones",
    "jacket",
    "watch",
    "backpack",
    "camera",
    "keyboard",
    "monitor",
]


def weighted_choice(options: Dict[str, float]) -> str:
    """
    Selects a random key based on the weights provided.
    """
    values = list(options.keys())
    weights = list(options.values())
    return random.choices(values, weights=weights, k=1)[0]


def random_timestamp(date_str: str) -> datetime:
    """
    Generates a random timestamp inside a specific date.
    """
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    seconds = random.randint(0, 86399)
    return base_date + timedelta(seconds=seconds)


def iso_format(dt: datetime) -> str:
    """
    Converts datetime to ISO format ending with Z.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_users(num_users: int = 1000, date_str: str = "2026-05-25") -> List[Dict[str, Any]]:
    """
    Generates synthetic users.
    """
    users = []

    for i in range(num_users):
        created_at = random_timestamp(date_str) - timedelta(days=random.randint(1, 365))

        users.append(
            {
                "user_id": f"user_{i + 1:06d}",
                "country": weighted_choice(COUNTRIES),
                "device_type": weighted_choice(DEVICES),
                "customer_segment": weighted_choice(CUSTOMER_SEGMENTS),
                "created_at": iso_format(created_at),
            }
        )

    return users


def generate_products(num_products: int = 500) -> List[Dict[str, Any]]:
    """
    Generates synthetic products.
    """
    products = []

    for i in range(num_products):
        category = random.choice(PRODUCT_CATEGORIES)
        price = round(random.uniform(5.0, 1500.0), 2)

        products.append(
            {
                "product_id": f"prod_{i + 1:06d}",
                "category": category,
                "name": f"{category}_product_{i + 1}",
                "price": price,
                "stock": random.randint(0, 500),
            }
        )

    return products


def create_page_view_event(
    user: Dict[str, Any],
    session_id: str,
    timestamp: datetime,
    sequence_number: int,
    page_type: str,
) -> Dict[str, Any]:
    """
    Creates a page_view event.
    """
    page_url = "/" if page_type == "home" else f"/{page_type}/{random.randint(1, 100)}"

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "page_view",
        "user_id": user["user_id"],
        "session_id": session_id,
        "page_url": page_url,
        "page_type": page_type,
        "timestamp": iso_format(timestamp),
        "time_on_page_seconds": random.randint(5, 600),
        "referrer": weighted_choice(REFERRERS),
        "device_type": user["device_type"],
        "country": user["country"],
        "sequence_number": sequence_number,
    }


def create_click_event(
    user: Dict[str, Any],
    session_id: str,
    timestamp: datetime,
    sequence_number: int,
) -> Dict[str, Any]:
    """
    Creates a click event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "click",
        "user_id": user["user_id"],
        "session_id": session_id,
        "element_id": f"button_{random.randint(1, 50)}",
        "element_type": random.choice(["button", "banner", "link", "menu"]),
        "timestamp": iso_format(timestamp),
        "device_type": user["device_type"],
        "country": user["country"],
        "sequence_number": sequence_number,
    }


def create_search_event(
    user: Dict[str, Any],
    session_id: str,
    timestamp: datetime,
    sequence_number: int,
) -> Dict[str, Any]:
    """
    Creates a search event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "search",
        "user_id": user["user_id"],
        "session_id": session_id,
        "search_term": random.choice(SEARCH_TERMS),
        "results_count": random.randint(0, 200),
        "timestamp": iso_format(timestamp),
        "device_type": user["device_type"],
        "country": user["country"],
        "sequence_number": sequence_number,
    }


def create_product_view_event(
    user: Dict[str, Any],
    session_id: str,
    timestamp: datetime,
    sequence_number: int,
    product: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates a product_view event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "product_view",
        "user_id": user["user_id"],
        "session_id": session_id,
        "product_id": product["product_id"],
        "category": product["category"],
        "price": product["price"],
        "timestamp": iso_format(timestamp),
        "device_type": user["device_type"],
        "country": user["country"],
        "sequence_number": sequence_number,
    }


def create_cart_event(
    user: Dict[str, Any],
    session_id: str,
    timestamp: datetime,
    sequence_number: int,
    product: Dict[str, Any],
    action: str,
) -> Dict[str, Any]:
    """
    Creates a cart_event event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "cart_event",
        "user_id": user["user_id"],
        "session_id": session_id,
        "product_id": product["product_id"],
        "action": action,
        "quantity": random.randint(1, 3),
        "timestamp": iso_format(timestamp),
        "device_type": user["device_type"],
        "country": user["country"],
        "sequence_number": sequence_number,
    }


def generate_session_events(
    user: Dict[str, Any],
    products: List[Dict[str, Any]],
    date_str: str = "2026-05-25",
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates events for one user session.

    Returns:
    - session
    - events
    - transactions
    - cart_items
    """
    session_id = f"session_{uuid.uuid4()}"
    start_time = random_timestamp(date_str)
    event_count = random.randint(3, 12)

    events = []
    transactions = []
    cart_items = []

    current_time = start_time
    selected_products = []

    for sequence_number in range(1, event_count + 1):
        current_time += timedelta(seconds=random.randint(5, 180))

        event_choice = random.choices(
            ["page_view", "click", "search", "product_view", "cart_event"],
            weights=[0.35, 0.15, 0.15, 0.25, 0.10],
            k=1,
        )[0]

        if sequence_number == 1:
            event_choice = "page_view"

        if event_choice == "page_view":
            page_type = weighted_choice(PAGE_TYPES)
            event = create_page_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence_number,
                page_type=page_type,
            )

        elif event_choice == "click":
            event = create_click_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence_number,
            )

        elif event_choice == "search":
            event = create_search_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence_number,
            )

        elif event_choice == "product_view":
            product = random.choice(products)
            selected_products.append(product)

            event = create_product_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence_number,
                product=product,
            )

        else:
            product = random.choice(selected_products) if selected_products else random.choice(products)
            action = random.choices(["add", "remove"], weights=[0.85, 0.15], k=1)[0]

            event = create_cart_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence_number,
                product=product,
                action=action,
            )

            if action == "add":
                cart_items.append(
                    {
                        "cart_item_id": str(uuid.uuid4()),
                        "session_id": session_id,
                        "user_id": user["user_id"],
                        "product_id": product["product_id"],
                        "quantity": event["quantity"],
                        "unit_price": product["price"],
                        "created_at": event["timestamp"],
                    }
                )

        events.append(event)

    has_purchase = random.random() < 0.18 and len(cart_items) > 0

    if has_purchase:
        total_amount = round(
            sum(item["quantity"] * item["unit_price"] for item in cart_items),
            2,
        )

        transactions.append(
            {
                "transaction_id": f"txn_{uuid.uuid4()}",
                "session_id": session_id,
                "user_id": user["user_id"],
                "total_amount": total_amount,
                "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
                "status": "approved",
                "transaction_timestamp": iso_format(current_time + timedelta(seconds=random.randint(10, 300))),
            }
        )

    session = {
        "session_id": session_id,
        "user_id": user["user_id"],
        "country": user["country"],
        "device_type": user["device_type"],
        "started_at": iso_format(start_time),
        "ended_at": iso_format(current_time),
        "event_count": len(events),
        "purchased": has_purchase,
    }

    return session, events, transactions, cart_items


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    """
    Writes dictionaries to CSV.
    """
    if not rows:
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    """
    Writes dictionaries to JSONL.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def partition_path(base_dir: str, entity: str, date_str: str, filename: str) -> str:
    """
    Builds a partitioned local path by year/month/day.
    """
    year, month, day = date_str.split("-")

    return os.path.join(
        base_dir,
        "raw",
        entity,
        f"year={year}",
        f"month={month}",
        f"day={day}",
        filename,
    )


def generate_dataset(
    date_str: str,
    records: int,
    output_dir: str,
    num_users: int = 5000,
    num_products: int = 1000,
) -> None:
    """
    Generates the complete ShopStream dataset.
    """
    print("Generating users...")
    users = generate_users(num_users=num_users, date_str=date_str)

    print("Generating products...")
    products = generate_products(num_products=num_products)

    sessions = []
    events = []
    transactions = []
    cart_items = []

    print(f"Generating approximately {records} events...")

    while len(events) < records:
        user = random.choice(users)

        session, session_events, session_transactions, session_cart_items = generate_session_events(
            user=user,
            products=products,
            date_str=date_str,
        )

        sessions.append(session)
        events.extend(session_events)
        transactions.extend(session_transactions)
        cart_items.extend(session_cart_items)

    events = events[:records]

    users_path = os.path.join(output_dir, "raw", "users", "users.csv")
    products_path = os.path.join(output_dir, "raw", "products", "products.csv")
    sessions_path = partition_path(output_dir, "sessions", date_str, "sessions.csv")
    events_path = partition_path(output_dir, "events", date_str, "events.jsonl")
    transactions_path = partition_path(output_dir, "transactions", date_str, "transactions.csv")
    cart_items_path = partition_path(output_dir, "cart_items", date_str, "cart_items.csv")

    write_csv(users_path, users)
    write_csv(products_path, products)
    write_csv(sessions_path, sessions)
    write_jsonl(events_path, events)
    write_csv(transactions_path, transactions)
    write_csv(cart_items_path, cart_items)

    print("Dataset generated successfully.")
    print(f"Users: {len(users)}")
    print(f"Products: {len(products)}")
    print(f"Sessions: {len(sessions)}")
    print(f"Events: {len(events)}")
    print(f"Transactions: {len(transactions)}")
    print(f"Cart items: {len(cart_items)}")
    print("")
    print("Main events file:")
    print(events_path)


def upload_directory_to_s3(local_dir: str, bucket: str, prefix: str = "") -> None:
    """
    Uploads a local directory to S3.
    Requires boto3 and AWS credentials configured.
    """
    import boto3

    s3_client = boto3.client("s3")

    for root, _, files in os.walk(local_dir):
        for file_name in files:
            local_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_key = os.path.join(prefix, relative_path).replace("\\", "/")

            print(f"Uploading {local_path} to s3://{bucket}/{s3_key}")
            s3_client.upload_file(local_path, bucket, s3_key)


def main():
    parser = argparse.ArgumentParser(description="Generate ShopStream synthetic dataset")

    parser.add_argument(
        "--date",
        default="2026-05-25",
        help="Date for the generated data in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--records",
        type=int,
        default=10000,
        help="Number of events to generate",
    )

    parser.add_argument(
        "--output",
        default="data_generator/output_shopstream",
        help="Local output directory",
    )

    parser.add_argument(
        "--users",
        type=int,
        default=5000,
        help="Number of users to generate",
    )

    parser.add_argument(
        "--products",
        type=int,
        default=1000,
        help="Number of products to generate",
    )

    parser.add_argument(
        "--upload-s3",
        action="store_true",
        help="Upload generated files to S3",
    )

    parser.add_argument(
        "--bucket",
        default=None,
        help="S3 bucket name",
    )

    parser.add_argument(
        "--prefix",
        default="",
        help="S3 prefix",
    )

    args = parser.parse_args()

    generate_dataset(
        date_str=args.date,
        records=args.records,
        output_dir=args.output,
        num_users=args.users,
        num_products=args.products,
    )

    if args.upload_s3:
        if not args.bucket:
            raise ValueError("You must provide --bucket when using --upload-s3")

        upload_directory_to_s3(
            local_dir=args.output,
            bucket=args.bucket,
            prefix=args.prefix,
        )


if __name__ == "__main__":
    main()
