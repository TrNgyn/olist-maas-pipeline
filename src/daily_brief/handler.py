"""
Lambda: Daily Executive Brief
Trigger: EventBridge (scheduled, 9 AM)
Timeout target: 15 seconds

Reads the latest batch from report_business_vitals, compares against KPI
targets, and delivers a high-level executive summary to Telegram.
"""
import json
import os
import boto3
import requests
import awswrangler as wr
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET      = os.environ["S3_BUCKET"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
AWS_REGION     = os.environ.get("AWS_REGION", "us-east-1")

KPI = {
    "on_time_delivery_rate_pct": float(os.environ.get("KPI_ONTIME_RATE_PCT", 90)),
    "cancellation_rate_pct":     float(os.environ.get("KPI_CANCELLATION_RATE_PCT", 5)),
    "avg_delivery_days":         float(os.environ.get("KPI_AVG_DELIVERY_DAYS", 7)),
    "daily_orders_target":       float(os.environ.get("KPI_DAILY_ORDERS", 0)),
    "daily_revenue_target_brl":  float(os.environ.get("KPI_DAILY_REVENUE_BRL", 0)),
}

BEDROCK_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"
TELEGRAM_URL  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
GOLD_BASE     = f"s3://{S3_BUCKET}/serving/gold"

_boto_session = boto3.Session()


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

def _read_latest_vitals() -> pd.DataFrame:
    """Read the most recent batch of report_business_vitals from S3."""
    try:
        df = wr.s3.read_parquet(
            path=f"{GOLD_BASE}/report_business_vitals/",
            boto3_session=_boto_session,
        )
        if "processed_at" in df.columns:
            df = df[df["processed_at"] == df["processed_at"].max()]
        return df
    except Exception as exc:
        print(f"[DailyBrief] S3 read error: {exc}")
        return pd.DataFrame()


def _aggregate_metrics(df: pd.DataFrame) -> dict:
    """Roll up platform-wide headline metrics from the vitals snapshot."""
    if df.empty:
        return {}

    m = {}

    for col in ["total_orders", "order_count", "orders"]:
        if col in df.columns:
            m["total_orders"] = int(df[col].sum())
            break

    for col in ["total_revenue_brl", "revenue_brl", "gmv_brl", "revenue"]:
        if col in df.columns:
            m["total_revenue_brl"] = round(float(df[col].sum()), 2)
            break

    for col in ["on_time_delivery_rate", "on_time_rate", "delivery_rate_pct"]:
        if col in df.columns:
            raw = float(df[col].mean())
            m["on_time_delivery_rate_pct"] = round(raw * 100 if raw <= 1 else raw, 2)
            break

    for col in ["cancellation_rate", "cancel_rate", "cancellation_rate_pct"]:
        if col in df.columns:
            raw = float(df[col].mean())
            m["cancellation_rate_pct"] = round(raw * 100 if raw <= 1 else raw, 2)
            break

    for col in ["avg_delivery_days", "average_delivery_days", "mean_delivery_days"]:
        if col in df.columns:
            m["avg_delivery_days"] = round(float(df[col].mean()), 1)
            break

    for col in ["active_sellers", "seller_count", "sellers"]:
        if col in df.columns:
            m["active_sellers"] = int(df[col].sum())
            break

    if "processed_at" in df.columns:
        m["processed_at"] = str(df["processed_at"].max())

    return m


def _kpi_deltas(metrics: dict) -> list[dict]:
    """Compare actual metrics against KPI targets."""
    checks = [
        ("on_time_delivery_rate_pct", KPI["on_time_delivery_rate_pct"],  ">=", "%"),
        ("cancellation_rate_pct",     KPI["cancellation_rate_pct"],       "<=", "%"),
        ("avg_delivery_days",         KPI["avg_delivery_days"],           "<=", " days"),
    ]
    if KPI["daily_orders_target"] > 0:
        checks.append(("total_orders", KPI["daily_orders_target"], ">=", " orders"))
    if KPI["daily_revenue_target_brl"] > 0:
        checks.append(("total_revenue_brl", KPI["daily_revenue_target_brl"], ">=", " BRL"))

    results = []
    for metric, target, direction, unit in checks:
        actual = metrics.get(metric)
        if actual is None:
            continue
        delta = round(actual - target, 2)
        on_target = actual >= target if direction == ">=" else actual <= target
        results.append({
            "metric":  metric.replace("_", " ").title(),
            "actual":  f"{actual}{unit}",
            "target":  f"{target}{unit}",
            "delta":   f"{'+' if delta >= 0 else ''}{delta}{unit}",
            "status":  "ON TARGET" if on_target else "OFF TARGET",
        })

    return results


# ---------------------------------------------------------------------------
# AI reasoning
# ---------------------------------------------------------------------------

def _build_prompt(metrics: dict, kpi_deltas: list[dict]) -> str:
    processed_at = metrics.get("processed_at", "N/A")
    return f"""You are an AI assistant generating a morning executive briefing for a C-level audience.
The platform is an e-commerce logistics marketplace (Olist MaaS).

## Latest Performance Snapshot
Data as of: {processed_at}
{json.dumps({k: v for k, v in metrics.items() if k != "processed_at"}, indent=2)}

## KPI Scorecard
{json.dumps(kpi_deltas, indent=2)}

Generate a concise Executive Morning Briefing as raw HTML (no markdown, no code fences).

Structure:
1. <h2>Olist MaaS — Executive Morning Brief</h2>
2. <b>Data as of:</b> {processed_at} (one line, no heading)
3. <h3>Performance at a Glance</h3> — key metrics in a clean <table>: Metric | Actual | Target | Status
4. <h3>Delivery Performance</h3> — 2–3 sentences on on-time rate and avg delivery days
5. <h3>Business Pulse</h3> — 2–3 sentences on order volume and revenue (skip if data unavailable)
6. <h3>Watch Points</h3> — bullet list of any OFF TARGET metric with a one-line implication; omit section entirely if all metrics are ON TARGET

Rules:
- No regional breakdowns, no seller names, no root-cause analysis
- Professional, direct language — the reader has 60 seconds
- Total length under 450 words"""


def _call_bedrock(prompt: str) -> str:
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1100,
        "messages": [{"role": "user", "content": prompt}],
    })
    response = client.invoke_model(modelId=BEDROCK_MODEL, body=body)
    return json.loads(response["body"].read())["content"][0]["text"]


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------

def _send_telegram(html: str) -> None:
    if len(html) > 4000:
        html = html[:3990] + "…"
    requests.post(
        TELEGRAM_URL,
        json={
            "chat_id": CHAT_ID,
            "text": html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    ).raise_for_status()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    print("[DailyBrief] Triggered by EventBridge.")

    vitals  = _read_latest_vitals()
    metrics = _aggregate_metrics(vitals)
    deltas  = _kpi_deltas(metrics)

    print(f"[DailyBrief] Metrics: {list(metrics.keys())} | KPI checks: {len(deltas)}")

    html = _call_bedrock(_build_prompt(metrics, deltas))
    _send_telegram(html)

    print("[DailyBrief] Brief delivered.")
    return {"statusCode": 200, "body": "Brief delivered."}
