import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request


app = Flask(__name__)


def get_db_connection():
    """
    Creates a PostgreSQL connection using environment variables.
    These variables are configured locally or in zappa_settings.json.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def query_db(query, params=None):
    """
    Executes a SQL query and returns the result as a list of dictionaries.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "ShopStream Analytics API",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "top_pages": "/pages/top?metric=time_on_page&date=2026-05-25&limit=10",
                "top_bounce_rate": "/pages/top?metric=bounce_rate&date=2026-05-25&limit=10",
                "sessions_summary": "/sessions/summary?country=CO&device=mobile&date=2026-05-25",
                "anomalies": "/anomalies?date=2026-05-25",
            },
        }
    )


@app.route("/health", methods=["GET"])
def health():
    try:
        result = query_db("SELECT 1 AS ok;")
        return jsonify(
            {
                "status": "ok",
                "database": result[0]["ok"] if result else None,
            }
        )
    except Exception as exc:
        return jsonify(
            {
                "status": "error",
                "message": str(exc),
            }
        ), 500


@app.route("/pages/top", methods=["GET"])
def pages_top():
    metric = request.args.get("metric")
    date = request.args.get("date")
    limit = request.args.get("limit", "10")

    if not metric:
        return jsonify({"error": "El parámetro metric es obligatorio"}), 400

    if not date:
        return jsonify({"error": "El parámetro date es obligatorio"}), 400

    try:
        limit = int(limit)
    except ValueError:
        return jsonify({"error": "El parámetro limit debe ser numérico"}), 400

    if limit <= 0:
        return jsonify({"error": "El parámetro limit debe ser mayor que 0"}), 400

    if metric == "time_on_page":
        sql = """
            SELECT
                metric_date,
                page_url,
                avg_time_on_page,
                total_views
            FROM page_metrics_daily
            WHERE metric_date = %s
            ORDER BY avg_time_on_page DESC
            LIMIT %s;
        """

        data = query_db(sql, (date, limit))

        return jsonify(
            {
                "metric": metric,
                "date": date,
                "limit": limit,
                "data": data,
            }
        )

    if metric == "bounce_rate":
        sql = """
            SELECT
                metric_date,
                page_type,
                total_sessions,
                bounce_sessions,
                bounce_rate
            FROM bounce_rate_daily
            WHERE metric_date = %s
            ORDER BY bounce_rate DESC
            LIMIT %s;
        """

        data = query_db(sql, (date, limit))

        return jsonify(
            {
                "metric": metric,
                "date": date,
                "limit": limit,
                "data": data,
            }
        )

    return jsonify(
        {
            "error": "metric inválido. Use: bounce_rate o time_on_page"
        }
    ), 400


@app.route("/sessions/summary", methods=["GET"])
def sessions_summary():
    country = request.args.get("country")
    device = request.args.get("device")
    date = request.args.get("date")

    if not date:
        return jsonify({"error": "El parámetro date es obligatorio"}), 400

    filters = ["metric_date = %s"]
    params = [date]

    if country:
        filters.append("country = %s")
        params.append(country)

    if device:
        filters.append("device_type = %s")
        params.append(device)

    where_clause = " AND ".join(filters)

    sql = f"""
        SELECT
            metric_date,
            country,
            device_type,
            sessions,
            avg_time_on_page
        FROM device_country_daily
        WHERE {where_clause}
        ORDER BY sessions DESC;
    """

    data = query_db(sql, tuple(params))

    return jsonify(
        {
            "date": date,
            "country": country,
            "device": device,
            "data": data,
        }
    )


@app.route("/anomalies", methods=["GET"])
def anomalies():
    date = request.args.get("date")

    if not date:
        return jsonify({"error": "El parámetro date es obligatorio"}), 400

    sql = """
        SELECT
            metric_date,
            session_id,
            metric_name,
            metric_value,
            z_score,
            anomaly_type
        FROM anomalies_daily
        WHERE metric_date = %s
        ORDER BY ABS(z_score) DESC;
    """

    data = query_db(sql, (date,))

    return jsonify(
        {
            "date": date,
            "data": data,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
