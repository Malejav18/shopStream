import json
import os
import urllib.parse
import unicodedata
from datetime import datetime

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3 = boto3.client("s3", region_name=AWS_REGION)
cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)
glue = boto3.client("glue", region_name=AWS_REGION)


VALIDATED_PREFIX = os.environ.get("VALIDATED_PREFIX", "validated/events/")
QUARANTINE_PREFIX = os.environ.get("QUARANTINE_PREFIX", "quarantine/")
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "ShopStream/Ingestion")
GLUE_WORKFLOW_NAME = os.environ.get("GLUE_WORKFLOW_NAME")


REQUIRED_FIELDS = {
    "page_view": {
        "user_id": str,
        "session_id": str,
        "page_url": str,
        "page_type": str,
        "timestamp": str,
        "time_on_page_seconds": int,
        "referrer": str,
        "device_type": str,
        "country": str
    },
    "click": {
        "user_id": str,
        "session_id": str,
        "element_id": str,
        "element_type": str,
        "page_url": str,
        "timestamp": str,
        "x_position": int,
        "y_position": int
    },
    "search": {
        "user_id": str,
        "session_id": str,
        "query": str,
        "results_count": int,
        "timestamp": str
    },
    "product_view": {
        "user_id": str,
        "session_id": str,
        "product_id": str,
        "category": str,
        "price": (int, float),
        "timestamp": str,
        "time_on_page_seconds": int
    },
    "cart_event": {
        "user_id": str,
        "session_id": str,
        "product_id": str,
        "action": str,
        "timestamp": str
    }
}


VALID_PAGE_TYPES = {
    "home",
    "category",
    "product",
    "cart",
    "checkout",
    "search_results"
}


VALID_DEVICE_TYPES = {
    "mobile",
    "desktop",
    "tablet"
}


VALID_CART_ACTIONS = {
    "add",
    "remove"
}


def to_ascii_metadata(value):
    """
    Convierte texto a ASCII para poder guardarlo como metadata de S3.
    S3 metadata no acepta tildes ni caracteres especiales.
    """
    if value is None:
        return ""

    value = str(value)

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")

    return ascii_value[:900]


def put_metric(metric_name, value, unit="Count"):
    """
    Envía una métrica personalizada a CloudWatch.
    """
    try:
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit
                }
            ]
        )
    except Exception as error:
        print(f"No se pudo enviar métrica {metric_name}: {str(error)}")


def is_valid_iso_timestamp(value):
    """
    Valida timestamps tipo:
    2026-05-25T14:30:00Z
    """
    if not isinstance(value, str):
        return False

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_event(event):
    """
    Valida estructura, tipos y rangos de un evento.

    Retorna:
    - None si el evento es válido
    - string con error si es inválido
    """

    if not isinstance(event, dict):
        return "El registro no es un objeto JSON"

    event_type = event.get("event_type")

    if not event_type:
        return "Falta el campo event_type"

    if event_type not in REQUIRED_FIELDS:
        return f"event_type no valido: {event_type}"

    required_schema = REQUIRED_FIELDS[event_type]

    for field, expected_type in required_schema.items():
        if field not in event:
            return f"Falta campo obligatorio '{field}' para event_type '{event_type}'"

        if not isinstance(event[field], expected_type):
            return (
                f"Tipo invalido en campo '{field}' para event_type '{event_type}'. "
                f"Valor recibido: {event[field]}"
            )

    timestamp = event.get("timestamp")

    if not is_valid_iso_timestamp(timestamp):
        return f"timestamp invalido: {timestamp}"

    if event_type == "page_view":
        if event["time_on_page_seconds"] < 0:
            return "time_on_page_seconds no puede ser negativo"

        if event["page_type"] not in VALID_PAGE_TYPES:
            return f"page_type invalido: {event['page_type']}"

        if event["device_type"] not in VALID_DEVICE_TYPES:
            return f"device_type invalido: {event['device_type']}"

    elif event_type == "click":
        if event["x_position"] < 0:
            return "x_position no puede ser negativo"

        if event["y_position"] < 0:
            return "y_position no puede ser negativo"

    elif event_type == "search":
        if event["results_count"] < 0:
            return "results_count no puede ser negativo"

    elif event_type == "product_view":
        if event["price"] < 0:
            return "price no puede ser negativo"

        if event["time_on_page_seconds"] < 0:
            return "time_on_page_seconds no puede ser negativo"

    elif event_type == "cart_event":
        if event["action"] not in VALID_CART_ACTIONS:
            return f"action invalida: {event['action']}"

    return None


def build_validated_key(original_key):
    """
    Convierte:
    raw/events/year=2026/month=05/day=25/events.jsonl

    En:
    validated/events/year=2026/month=05/day=25/events.jsonl
    """
    return original_key.replace("raw/events/", VALIDATED_PREFIX, 1)


def build_quarantine_key(original_key):
    """
    Convierte:
    raw/events/year=2026/month=05/day=25/events.jsonl

    En:
    quarantine/raw/events/year=2026/month=05/day=25/events.jsonl
    """
    return f"{QUARANTINE_PREFIX}{original_key}"


def clean_metadata(metadata):
    """
    Limpia todos los valores de metadata para evitar errores de S3.
    """
    cleaned = {}

    for key, value in metadata.items():
        cleaned[key] = to_ascii_metadata(value)

    return cleaned


def copy_object(bucket, source_key, destination_key, metadata=None):
    """
    Copia un objeto dentro del mismo bucket.
    """
    copy_source = {
        "Bucket": bucket,
        "Key": source_key
    }

    if metadata:
        s3.copy_object(
            Bucket=bucket,
            CopySource=copy_source,
            Key=destination_key,
            Metadata=clean_metadata(metadata),
            MetadataDirective="REPLACE"
        )
    else:
        s3.copy_object(
            Bucket=bucket,
            CopySource=copy_source,
            Key=destination_key
        )


def delete_object(bucket, key):
    """
    Borra un objeto de S3.
    """
    s3.delete_object(
        Bucket=bucket,
        Key=key
    )


def validate_s3_jsonl_file(bucket, key):
    """
    Lee un archivo JSONL desde S3 línea por línea.
    Retorna un resumen de validación.
    """

    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"]

    total_records = 0
    invalid_records = 0
    first_error = None

    for line_number, raw_line in enumerate(body.iter_lines(), start=1):
        if not raw_line:
            continue

        total_records += 1

        try:
            event = json.loads(raw_line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            invalid_records += 1
            first_error = f"Linea {line_number}: JSON invalido. {str(exc)}"
            break

        error = validate_event(event)

        if error:
            invalid_records += 1
            first_error = f"Linea {line_number}: {error}"
            break

    return {
        "total_records": total_records,
        "invalid_records": invalid_records,
        "first_error": first_error,
        "is_valid": invalid_records == 0
    }


def maybe_start_glue_workflow():
    """
    Inicia Glue Workflow solo si se configuró GLUE_WORKFLOW_NAME.
    """
    if not GLUE_WORKFLOW_NAME:
        print("GLUE_WORKFLOW_NAME no configurado. No se inicia Glue Workflow.")
        return None

    try:
        response = glue.start_workflow_run(
            Name=GLUE_WORKFLOW_NAME
        )

        print(f"Glue Workflow iniciado: {response}")
        return response

    except Exception as error:
        print(f"No se pudo iniciar Glue Workflow: {str(error)}")
        return None


def lambda_handler(event, context):
    print("Evento recibido:")
    print(json.dumps(event))

    processed_files = 0
    error_files = 0
    total_size_bytes = 0

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size = record["s3"]["object"].get("size", 0)

        print(f"Procesando archivo: s3://{bucket}/{key}")

        # Seguridad adicional: solo procesar raw/events/*.jsonl
        if not key.startswith("raw/events/") or not key.endswith(".jsonl"):
            print(f"Archivo ignorado por filtro logico: {key}")
            continue

        total_size_bytes += size

        try:
            validation_result = validate_s3_jsonl_file(bucket, key)

            print("Resultado de validacion:")
            print(json.dumps(validation_result))

            if validation_result["is_valid"]:
                destination_key = build_validated_key(key)

                copy_object(
                    bucket=bucket,
                    source_key=key,
                    destination_key=destination_key,
                    metadata={
                        "validation-status": "valid",
                        "original-key": key,
                        "records": str(validation_result["total_records"])
                    }
                )

                processed_files += 1

                print(f"Archivo valido copiado a: s3://{bucket}/{destination_key}")

                maybe_start_glue_workflow()

            else:
                destination_key = build_quarantine_key(key)

                error_message = validation_result["first_error"] or "Unknown error"
                safe_error_message = to_ascii_metadata(error_message)

                copy_object(
                    bucket=bucket,
                    source_key=key,
                    destination_key=destination_key,
                    metadata={
                        "validation-status": "invalid",
                        "original-key": key,
                        "validation-error": safe_error_message
                    }
                )

                # Para cumplir "mover a quarantine", borramos el original.
                delete_object(bucket, key)

                error_files += 1

                print(f"Archivo invalido movido a: s3://{bucket}/{destination_key}")
                print(f"Error: {safe_error_message}")

        except Exception as error:
            error_files += 1

            error_message = to_ascii_metadata(str(error))
            print(f"Error procesando archivo {key}: {error_message}")

            try:
                destination_key = build_quarantine_key(key)

                copy_object(
                    bucket=bucket,
                    source_key=key,
                    destination_key=destination_key,
                    metadata={
                        "validation-status": "processing-error",
                        "original-key": key,
                        "validation-error": error_message
                    }
                )

                delete_object(bucket, key)

                print(f"Archivo movido a quarantine por error de procesamiento: s3://{bucket}/{destination_key}")

            except Exception as quarantine_error:
                print(f"No se pudo mover a quarantine: {str(quarantine_error)}")

    put_metric("FilesProcessed", processed_files)
    put_metric("FilesWithErrors", error_files)
    put_metric("BytesProcessed", total_size_bytes, unit="Bytes")

    result = {
        "processed_files": processed_files,
        "error_files": error_files,
        "bytes_processed": total_size_bytes
    }

    print("Resultado final:")
    print(json.dumps(result))

    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }
