# 04_gold_S3_export.py
# Layer: serving
# Purpose: Stamp each Gold table with batch_id + processed_at, then append to the S3 Serving Layer.

import uuid
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

S3_SERVING_BUCKET = "s3://olist-maas-landing-442186c8/serving/gold"

GOLD_TABLES = [
    # fact tables
    "fact_orders",
    "fact_order_items",
    # dimension tables
    "dim_date",
    "dim_product",
    "dim_customer",
    "dim_seller",
    # reporting / action tables
    "report_business_vitals",
    "rca_customer_churn_5whys",
    "rca_cancellation_leakage",
    "action_early_adopter_leads",
    "action_seller_intervention",
]

# Spark session
spark = SparkSession.builder.appName("olist-maas-gold-s3-export").getOrCreate()

# Production-run metadata  
BATCH_ID     = str(uuid.uuid4())
PROCESSED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

print(f"\n{'='*60}")
print(f"  [S3 Export]  batch_id    = {BATCH_ID}")
print(f"  [S3 Export]  processed_at = {PROCESSED_AT}")
print(f"{'='*60}\n")

# Export loop
# For each Gold table: read, stamp with batch metadata, and append to S3 in Parquet format
results: list[dict] = []

for table in GOLD_TABLES:
    s3_path = f"{S3_SERVING_BUCKET}/{table}"
    try:
        df = spark.table(f"olist_maas_pipeline.gold.{table}")

        df_export = (
            df
            .withColumn("processed_at", F.lit(PROCESSED_AT).cast("timestamp"))
            .withColumn("batch_id",     F.lit(BATCH_ID))
        )

        (
            df_export
            .write
            .format("parquet")
            .mode("append")
            .partitionBy("batch_id")   # each run lands in its own partition
            .save(s3_path)
        )

        row_count = df_export.count()
        print(f"  [OK]   {table:<40}  {row_count:>8,} rows  →  {s3_path}")
        results.append({
            "table":  table,
            "status": "OK",
            "rows":   row_count,
            "path":   s3_path,
            "error":  "",
        })

    except Exception as exc:
        print(f"  [FAIL] {table:<40}  ERROR: {exc}")
        results.append({
            "table":  table,
            "status": "FAIL",
            "rows":   -1,
            "path":   s3_path,
            "error":  str(exc),
        })

# Batch manifest  ─ lightweight audit trail of every run
manifest_rows = [
    (
        BATCH_ID,
        PROCESSED_AT,
        r["table"],
        r["status"],
        r["rows"],
        r["path"],
        r["error"],
    )
    for r in results
]

manifest_schema = [
    "batch_id",
    "processed_at",
    "table_name",
    "status",
    "row_count",
    "s3_path",
    "error_message",
]

manifest_df = spark.createDataFrame(manifest_rows, manifest_schema)
manifest_path = f"{S3_SERVING_BUCKET}/_batch_manifest"
manifest_df.write.format("parquet").mode("append").save(manifest_path)

# Summary
ok_count   = sum(1 for r in results if r["status"] == "OK")
fail_count = len(results) - ok_count

print(f"\n{'='*60}")
print(f"  Manifest  → {manifest_path}")
print(f"  Exported  → {ok_count}/{len(results)} tables")
if fail_count:
    print(f"  FAILED    → {fail_count} table(s) — check errors above")
print(f"{'='*60}\n")

if fail_count:
    raise RuntimeError(f"{fail_count} table(s) failed to export — see log above.")