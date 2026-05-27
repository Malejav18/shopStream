import pytest

try:
    from pyspark.sql import SparkSession
    from emr_jobs.shopstream_metrics import add_partition_columns
except ImportError:
    SparkSession = None
    add_partition_columns = None


@pytest.mark.skipif(SparkSession is None, reason="pyspark no está instalado en este entorno")
def test_add_partition_columns():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("test-shopstream")
        .getOrCreate()
    )

    df = spark.createDataFrame(
        [
            ("/home", 100.0, 10)
        ],
        ["page_url", "avg_time_on_page", "total_views"]
    )

    result = add_partition_columns(df, "2026-05-25")
    row = result.collect()[0]

    assert row["metric_date"] == "2026-05-25"
    assert row["year"] == "2026"
    assert row["month"] == "05"
    assert row["day"] == "25"

    spark.stop()
