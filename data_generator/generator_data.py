import argparse
import csv
import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

try:
    import boto3
except ImportError:
    boto3 = None


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

EVENT_TYPES = [
    "page_view",
    "click",
    "search",
    "product_view",
    "cart_event"
]

COUNTRIES = {
    "CO": 0.40,
    "MX": 0.20,
    "US": 0.15,
    "PE": 0.10,
    "CL": 0.10,
    "AR": 0.05
}

DEVICES = {
    "mobile": 0.60,
    "desktop": 0.30,
    "tablet": 0.10
}

REFERRERS = {
    "google": 0.35,
    "instagram": 0.20,
    "facebook": 0.15,
    "direct": 0.15,
    "email": 0.10,
    "tiktok": 0.05
}

PAGE_TYPES = [
    "home",
    "category",
    "product",
    "cart",
    "checkout",
    "search_results"
]

PRODUCT_CATEGORIES = [
    "technology",
    "fashion",
    "home",
    "sports",
    "beauty",
    "books",
    "gaming"
]

ELEMENT_TYPES = [
    "button",
    "banner",
    "product_card",
    "menu",
    "filter",
    "search_box",
    "carousel"
]

SEARCH_QUERIES = [
    "iphone",
    "laptop gamer",
    "tenis nike",
    "camiseta",
    "audifonos bluetooth",
    "monitor",
    "silla ergonomica",
    "reloj inteligente",
    "maleta",
    "perfume",
    "teclado mecanico",
    "tablet",
    "celular samsung",
    "zapatos deportivos",
    "chaqueta"
]


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def weighted_choice(weight_dict):
    """
    Escoge un valor según pesos.
    Ejemplo:
    {"mobile": 0.6, "desktop": 0.3, "tablet": 0.1}
    """
    values = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(values, weights=weights, k=1)[0]


def money(value):
    """
    Redondea valores monetarios a 2 decimales.
    """
    return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def random_timestamp_for_day(date_str):
    """
    Genera un timestamp aleatorio dentro del día indicado.
    date_str debe venir en formato YYYY-MM-DD.
    """
    base_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    seconds = random.randint(0, 86399)
    return base_date + timedelta(seconds=seconds)


def isoformat_z(dt):
    """
    Convierte datetime a formato ISO con Z.
    """
    return dt.isoformat().replace("+00:00", "Z")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_csv(path, rows, fieldnames):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upload_file_to_s3(local_path, bucket, s3_key):
    """
    Sube un archivo a S3. Requiere boto3 instalado y credenciales configuradas.
    """
    if boto3 is None:
        raise ImportError("boto3 no está instalado. Ejecuta: pip install boto3")

    s3_client = boto3.client("s3")
    s3_client.upload_file(local_path, bucket, s3_key)
    print(f"Subido a S3: s3://{bucket}/{s3_key}")


# ============================================================
# GENERACIÓN DE ENTIDADES
# ============================================================

def generate_users(num_users, date_str):
    users = []
    start_date = datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=365)

    segments = ["new", "regular", "premium", "inactive"]
    age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]

    for i in range(1, num_users + 1):
        signup_dt = start_date + timedelta(days=random.randint(0, 365))
        country = weighted_choice(COUNTRIES)

        users.append({
            "user_id": f"user_{i:07d}",
            "signup_date": signup_dt.strftime("%Y-%m-%d"),
            "country": country,
            "age_group": random.choice(age_groups),
            "customer_segment": random.choices(
                segments,
                weights=[0.25, 0.45, 0.20, 0.10],
                k=1
            )[0]
        })

    return users


def generate_products(num_products):
    products = []

    brands_by_category = {
        "technology": ["Apple", "Samsung", "Lenovo", "HP", "Xiaomi", "Sony"],
        "fashion": ["Nike", "Adidas", "Zara", "Lacoste", "H&M"],
        "home": ["Ikea", "HomeCenter", "Mabe", "Oster"],
        "sports": ["Nike", "Adidas", "Puma", "Under Armour"],
        "beauty": ["L'Oreal", "Nivea", "Dior", "Maybelline"],
        "books": ["Penguin", "Planeta", "Norma", "Pearson"],
        "gaming": ["Logitech", "Razer", "Xbox", "PlayStation", "Nintendo"]
    }

    for i in range(1, num_products + 1):
        category = random.choice(PRODUCT_CATEGORIES)
        brand = random.choice(brands_by_category[category])

        if category == "technology":
            price = money(random.uniform(80, 2500))
        elif category == "fashion":
            price = money(random.uniform(10, 300))
        elif category == "home":
            price = money(random.uniform(20, 800))
        elif category == "sports":
            price = money(random.uniform(15, 500))
        elif category == "beauty":
            price = money(random.uniform(5, 250))
        elif category == "books":
            price = money(random.uniform(5, 120))
        else:
            price = money(random.uniform(20, 1000))

        products.append({
            "product_id": f"prod_{i:06d}",
            "product_name": f"{brand} {category} item {i}",
            "category": category,
            "brand": brand,
            "price": price,
            "rating": round(random.uniform(2.5, 5.0), 1),
            "stock": random.randint(0, 500)
        })

    return products


# ============================================================
# GENERACIÓN DE EVENTOS
# ============================================================

def build_page_url(page_type, product=None, category=None):
    if page_type == "home":
        return "/"
    if page_type == "category":
        return f"/category/{category or random.choice(PRODUCT_CATEGORIES)}"
    if page_type == "product" and product:
        return f"/product/{product['product_id']}"
    if page_type == "cart":
        return "/cart"
    if page_type == "checkout":
        return "/checkout"
    if page_type == "search_results":
        return "/search"
    return "/"


def create_page_view_event(user, session_id, timestamp, sequence_number, page_type, page_url, device, country):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "page_view",
        "user_id": user["user_id"],
        "session_id": session_id,
        "sequence_number": sequence_number,
        "page_url": page_url,
        "page_type": page_type,
        "timestamp": isoformat_z(timestamp),
        "time_on_page_seconds": random.randint(3, 420),
        "referrer": weighted_choice(REFERRERS),
        "device_type": device,
        "country": country
    }


def create_click_event(user, session_id, timestamp, sequence_number, page_url):
    element_type = random.choice(ELEMENT_TYPES)

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "click",
        "user_id": user["user_id"],
        "session_id": session_id,
        "sequence_number": sequence_number,
        "element_id": f"el_{random.randint(1, 5000):05d}",
        "element_type": element_type,
        "page_url": page_url,
        "timestamp": isoformat_z(timestamp),
        "x_position": random.randint(0, 1920),
        "y_position": random.randint(0, 1080)
    }


def create_search_event(user, session_id, timestamp, sequence_number):
    query = random.choice(SEARCH_QUERIES)

    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "search",
        "user_id": user["user_id"],
        "session_id": session_id,
        "sequence_number": sequence_number,
        "query": query,
        "results_count": random.randint(0, 250),
        "timestamp": isoformat_z(timestamp)
    }


def create_product_view_event(user, session_id, timestamp, sequence_number, product):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "product_view",
        "user_id": user["user_id"],
        "session_id": session_id,
        "sequence_number": sequence_number,
        "product_id": product["product_id"],
        "category": product["category"],
        "price": product["price"],
        "timestamp": isoformat_z(timestamp),
        "time_on_page_seconds": random.randint(5, 600)
    }


def create_cart_event(user, session_id, timestamp, sequence_number, product, action):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "cart_event",
        "user_id": user["user_id"],
        "session_id": session_id,
        "sequence_number": sequence_number,
        "product_id": product["product_id"],
        "action": action,
        "timestamp": isoformat_z(timestamp)
    }


def generate_session_events(user, products, date_str):
    """
    Genera una secuencia realista de navegación para una sesión.
    Puede terminar en rebote, búsqueda, vista de producto, carrito o compra.
    """
    session_id = str(uuid.uuid4())
    device = weighted_choice(DEVICES)

    # Mantiene el país del usuario, pero permite algo de variación.
    country = user["country"] if random.random() < 0.85 else weighted_choice(COUNTRIES)

    start_time = random_timestamp_for_day(date_str)
    current_time = start_time
    sequence = 1

    events = []
    transactions = []
    cart_items = []

    selected_category = random.choice(PRODUCT_CATEGORIES)
    selected_product = random.choice(products)

    # 1. Casi toda sesión inicia en home o categoría.
    first_page_type = random.choices(
        ["home", "category"],
        weights=[0.65, 0.35],
        k=1
    )[0]

    first_page_url = build_page_url(first_page_type, category=selected_category)

    events.append(
        create_page_view_event(
            user=user,
            session_id=session_id,
            timestamp=current_time,
            sequence_number=sequence,
            page_type=first_page_type,
            page_url=first_page_url,
            device=device,
            country=country
        )
    )

    sequence += 1

    # 2. Rebote: sesión con un solo page_view.
    # Aproximadamente 25% de las sesiones abandonan rápido.
    if random.random() < 0.25:
        session = {
            "session_id": session_id,
            "user_id": user["user_id"],
            "start_timestamp": isoformat_z(start_time),
            "device_type": device,
            "country": country,
            "referrer": weighted_choice(REFERRERS),
            "events_count": len(events),
            "converted": False
        }
        return session, events, transactions, cart_items

    # 3. Algunos usuarios hacen búsqueda.
    if random.random() < 0.35:
        current_time += timedelta(seconds=random.randint(5, 40))
        events.append(
            create_search_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence
            )
        )
        sequence += 1

        current_time += timedelta(seconds=random.randint(3, 25))
        page_url = build_page_url("search_results")
        events.append(
            create_page_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                page_type="search_results",
                page_url=page_url,
                device=device,
                country=country
            )
        )
        sequence += 1

    # 4. Vista de categoría.
    if random.random() < 0.65:
        current_time += timedelta(seconds=random.randint(5, 60))
        category_page = build_page_url("category", category=selected_category)
        events.append(
            create_page_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                page_type="category",
                page_url=category_page,
                device=device,
                country=country
            )
        )
        sequence += 1

    # 5. Clicks dentro de la página.
    click_count = random.choices(
        [0, 1, 2, 3],
        weights=[0.35, 0.35, 0.20, 0.10],
        k=1
    )[0]

    last_page_url = events[-1].get("page_url", "/")

    for _ in range(click_count):
        current_time += timedelta(seconds=random.randint(2, 30))
        events.append(
            create_click_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                page_url=last_page_url
            )
        )
        sequence += 1

    # 6. Vista de producto.
    viewed_product = False

    if random.random() < 0.70:
        selected_product = random.choice(products)
        current_time += timedelta(seconds=random.randint(5, 80))

        product_page = build_page_url("product", product=selected_product)

        events.append(
            create_page_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                page_type="product",
                page_url=product_page,
                device=device,
                country=country
            )
        )
        sequence += 1

        current_time += timedelta(seconds=random.randint(2, 20))
        events.append(
            create_product_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                product=selected_product
            )
        )
        sequence += 1

        viewed_product = True

    # 7. Evento de carrito.
    added_to_cart = False

    if viewed_product and random.random() < 0.28:
        current_time += timedelta(seconds=random.randint(10, 120))

        events.append(
            create_cart_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                product=selected_product,
                action="add"
            )
        )
        sequence += 1

        cart_items.append({
            "cart_item_id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": user["user_id"],
            "product_id": selected_product["product_id"],
            "quantity": random.randint(1, 3),
            "unit_price": selected_product["price"],
            "created_at": isoformat_z(current_time)
        })

        added_to_cart = True

        # Algunos usuarios eliminan el producto del carrito.
        if random.random() < 0.12:
            current_time += timedelta(seconds=random.randint(5, 90))
            events.append(
                create_cart_event(
                    user=user,
                    session_id=session_id,
                    timestamp=current_time,
                    sequence_number=sequence,
                    product=selected_product,
                    action="remove"
                )
            )
            sequence += 1
            added_to_cart = False

    # 8. Checkout y transacción completada.
    converted = False

    if added_to_cart and random.random() < 0.38:
        current_time += timedelta(seconds=random.randint(20, 180))
        checkout_url = build_page_url("checkout")

        events.append(
            create_page_view_event(
                user=user,
                session_id=session_id,
                timestamp=current_time,
                sequence_number=sequence,
                page_type="checkout",
                page_url=checkout_url,
                device=device,
                country=country
            )
        )
        sequence += 1

        transaction_id = str(uuid.uuid4())
        quantity = random.randint(1, 3)
        total_amount = money(selected_product["price"] * quantity)

        transactions.append({
            "transaction_id": transaction_id,
            "user_id": user["user_id"],
            "session_id": session_id,
            "product_id": selected_product["product_id"],
            "quantity": quantity,
            "total_amount": total_amount,
            "payment_method": random.choice(["credit_card", "debit_card", "paypal", "cash_on_delivery"]),
            "transaction_status": "completed",
            "created_at": isoformat_z(current_time + timedelta(seconds=random.randint(5, 40)))
        })

        converted = True

    session = {
        "session_id": session_id,
        "user_id": user["user_id"],
        "start_timestamp": isoformat_z(start_time),
        "device_type": device,
        "country": country,
        "referrer": weighted_choice(REFERRERS),
        "events_count": len(events),
        "converted": converted
    }

    return session, events, transactions, cart_items


# ============================================================
# GENERACIÓN PRINCIPAL DEL DATASET
# ============================================================

def generate_dataset(
    output_dir,
    date_str,
    total_events=500_000,
    num_users=50_000,
    num_products=10_000
):
    year, month, day = date_str.split("-")

    print("Generando usuarios...")
    users = generate_users(num_users=num_users, date_str=date_str)

    print("Generando productos...")
    products = generate_products(num_products=num_products)

    users_path = os.path.join(output_dir, "users", "users.csv")
    products_path = os.path.join(output_dir, "products", "products.csv")

    write_csv(
        users_path,
        users,
        ["user_id", "signup_date", "country", "age_group", "customer_segment"]
    )

    write_csv(
        products_path,
        products,
        ["product_id", "product_name", "category", "brand", "price", "rating", "stock"]
    )

    partition_path = f"year={year}/month={month}/day={day}"

    events_dir = os.path.join(output_dir, "raw", "events", partition_path)
    sessions_dir = os.path.join(output_dir, "raw", "sessions", partition_path)
    transactions_dir = os.path.join(output_dir, "raw", "transactions", partition_path)
    cart_items_dir = os.path.join(output_dir, "raw", "cart_items", partition_path)

    ensure_dir(events_dir)
    ensure_dir(sessions_dir)
    ensure_dir(transactions_dir)
    ensure_dir(cart_items_dir)

    events_path = os.path.join(events_dir, "events.jsonl")
    sessions_path = os.path.join(sessions_dir, "sessions.csv")
    transactions_path = os.path.join(transactions_dir, "transactions.csv")
    cart_items_path = os.path.join(cart_items_dir, "cart_items.csv")

    sessions = []
    transactions = []
    cart_items = []

    event_count = 0
    session_count = 0

    print(f"Generando {total_events:,} eventos...")

    with open(events_path, "w", encoding="utf-8") as events_file:
        while event_count < total_events:
            user = random.choice(users)

            session, session_events, session_transactions, session_cart_items = generate_session_events(
                user=user,
                products=products,
                date_str=date_str
            )

            # Si la sesión genera más eventos de los que faltan, se recorta.
            remaining = total_events - event_count
            session_events = session_events[:remaining]

            session["events_count"] = len(session_events)

            sessions.append(session)
            transactions.extend(session_transactions)
            cart_items.extend(session_cart_items)

            for event in session_events:
                events_file.write(json.dumps(event, ensure_ascii=False) + "\n")

            event_count += len(session_events)
            session_count += 1

            if event_count % 50_000 == 0:
                print(f"Eventos generados: {event_count:,}")

    write_csv(
        sessions_path,
        sessions,
        [
            "session_id",
            "user_id",
            "start_timestamp",
            "device_type",
            "country",
            "referrer",
            "events_count",
            "converted"
        ]
    )

    write_csv(
        transactions_path,
        transactions,
        [
            "transaction_id",
            "user_id",
            "session_id",
            "product_id",
            "quantity",
            "total_amount",
            "payment_method",
            "transaction_status",
            "created_at"
        ]
    )

    write_csv(
        cart_items_path,
        cart_items,
        [
            "cart_item_id",
            "session_id",
            "user_id",
            "product_id",
            "quantity",
            "unit_price",
            "created_at"
        ]
    )

    print("\nDataset generado correctamente.")
    print(f"Eventos: {event_count:,}")
    print(f"Sesiones: {session_count:,}")
    print(f"Usuarios: {len(users):,}")
    print(f"Productos: {len(products):,}")
    print(f"Transacciones: {len(transactions):,}")
    print(f"Items de carrito: {len(cart_items):,}")

    print("\nArchivos creados:")
    print(events_path)
    print(sessions_path)
    print(transactions_path)
    print(cart_items_path)
    print(users_path)
    print(products_path)

    return {
        "events_path": events_path,
        "sessions_path": sessions_path,
        "transactions_path": transactions_path,
        "cart_items_path": cart_items_path,
        "users_path": users_path,
        "products_path": products_path,
        "partition_path": partition_path
    }


# ============================================================
# SUBIDA OPCIONAL A S3
# ============================================================

def upload_dataset_to_s3(paths, bucket, base_prefix):
    """
    Sube los archivos generados a S3 respetando particiones.
    """

    partition_path = paths["partition_path"]

    uploads = [
        (
            paths["events_path"],
            f"{base_prefix}/events/{partition_path}/events.jsonl"
        ),
        (
            paths["sessions_path"],
            f"{base_prefix}/sessions/{partition_path}/sessions.csv"
        ),
        (
            paths["transactions_path"],
            f"{base_prefix}/transactions/{partition_path}/transactions.csv"
        ),
        (
            paths["cart_items_path"],
            f"{base_prefix}/cart_items/{partition_path}/cart_items.csv"
        ),
        (
            paths["users_path"],
            f"{base_prefix}/users/users.csv"
        ),
        (
            paths["products_path"],
            f"{base_prefix}/products/products.csv"
        )
    ]

    for local_path, s3_key in uploads:
        upload_file_to_s3(local_path, bucket, s3_key)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generador de datos sintéticos para ShopStream"
    )

    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Fecha del dataset en formato YYYY-MM-DD. Ejemplo: 2026-05-25"
    )

    parser.add_argument(
        "--records",
        type=int,
        default=500_000,
        help="Cantidad de eventos a generar. Default: 500000"
    )

    parser.add_argument(
        "--users",
        type=int,
        default=50_000,
        help="Cantidad de usuarios sintéticos. Default: 50000"
    )

    parser.add_argument(
        "--products",
        type=int,
        default=10_000,
        help="Cantidad de productos sintéticos. Default: 10000"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output_shopstream",
        help="Carpeta local de salida"
    )

    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="Bucket S3 destino. Si se omite, no sube a S3"
    )

    parser.add_argument(
        "--s3-prefix",
        type=str,
        default="raw",
        help="Prefijo base en S3. Default: raw"
    )

    args = parser.parse_args()

    random.seed(123)

    paths = generate_dataset(
        output_dir=args.output,
        date_str=args.date,
        total_events=args.records,
        num_users=args.users,
        num_products=args.products
    )

    if args.bucket:
        print("\nSubiendo dataset a S3...")
        upload_dataset_to_s3(
            paths=paths,
            bucket=args.bucket,
            base_prefix=args.s3_prefix
        )

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()
