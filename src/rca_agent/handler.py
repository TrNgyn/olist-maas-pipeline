"""
Lambda: Real-Time On-Demand RCA Agent
Trigger: Telegram Webhook (API Gateway → Lambda URL)
AI: Google Gemini
Security: chat_id whitelist enforced before any data access
"""
import os
import json
import boto3
import requests
import awswrangler as wr
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET          = os.environ["S3_BUCKET"]
TELEGRAM_TOKEN     = os.environ["TELEGRAM_TOKEN"]
AUTHORIZED_CHAT_ID = str(os.environ["AUTHORIZED_CHAT_ID"])
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]
AWS_REGION         = os.environ.get("AWS_REGION", "us-east-1")

GEMINI_MODEL  = "gemini-2.0-flash"
TELEGRAM_URL  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
GOLD_BASE     = f"s3://{S3_BUCKET}/serving/gold"

_boto_session = boto3.Session()

genai.configure(api_key=GEMINI_API_KEY)
_gemini = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    system_instruction=(
        "You are a Senior Logistics Engineer and Data Analyst for an e-commerce platform. "
        "Answer only using the dataset provided. Apply the 5 Whys framework when diagnosing root causes. "
        "If the user asks about a specific region or seller, focus exclusively on that subset of the data. "
        "If the question is unrelated to seller interventions or logistics performance, politely explain your scope. "
        "Format your response in clean HTML (no markdown, no code fences — raw HTML only). "
        "Keep responses concise and actionable."
    ),
)


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

def _fetch_intervention() -> pd.DataFrame:
    try:
        df = wr.s3.read_parquet(
            path=f"{GOLD_BASE}/action_seller_intervention/",
            boto3_session=_boto_session,
        )
        if "processed_at" in df.columns:
            df = df[df["processed_at"] == df["processed_at"].max()]
        return df
    except Exception as exc:
        print(f"[RCA] S3 read error: {exc}")
        return pd.DataFrame()


def _smart_filter(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Narrow the dataset to the region or seller mentioned in the user's query."""
    q = query.lower()

    if "region" in df.columns:
        for region in df["region"].dropna().unique():
            if str(region).lower() in q:
                return df[df["region"] == region]

    if "seller_id" in df.columns:
        for sid in df["seller_id"].dropna().unique():
            if str(sid).lower() in q:
                return df[df["seller_id"] == sid]

    return df


# ---------------------------------------------------------------------------
# AI reasoning
# ---------------------------------------------------------------------------

def _call_gemini(question: str, data_json: str) -> str:
    prompt = f"Question: {question}\n\nDataset (JSON):\n{data_json}"
    response = _gemini.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=1200),
    )
    return response.text


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------

def _reply(chat_id: str, html: str) -> None:
    if len(html) > 4000:
        html = html[:3990] + "…"
    requests.post(
        TELEGRAM_URL,
        json={
            "chat_id": chat_id,
            "text": html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return {"statusCode": 400, "body": "Invalid JSON"}

    message = body.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text    = (message.get("text") or "").strip()

    # Security gate — reject before touching any data
    if chat_id != AUTHORIZED_CHAT_ID:
        print(f"[RCA] Blocked unauthorised chat_id: {chat_id}")
        return {"statusCode": 403, "body": "Forbidden"}

    if not text or text.startswith("/"):
        if text == "/start":
            _reply(chat_id,
                   "<b>Olist MaaS RCA Agent</b>\n\n"
                   "Ask me anything about seller interventions and logistics performance.\n"
                   "I apply the <b>5 Whys</b> framework to diagnose root causes.")
        return {"statusCode": 200, "body": "OK"}

    print(f"[RCA] Question from {chat_id}: {text}")

    df = _fetch_intervention()
    if df.empty:
        _reply(chat_id,
               "<b>Data Unavailable</b>\n\n"
               "Could not retrieve the seller intervention dataset from S3. "
               "Please try again later.")
        return {"statusCode": 200, "body": "OK"}

    filtered  = _smart_filter(df, text).head(50)
    data_json = filtered.to_json(orient="records", indent=2)

    try:
        html_response = _call_gemini(text, data_json)
    except Exception as exc:
        print(f"[RCA] Gemini error: {exc}")
        _reply(chat_id,
               "<b>Analysis Error</b>\n\n"
               "Failed to generate the RCA. Please rephrase your question or try again.")
        return {"statusCode": 200, "body": "OK"}

    _reply(chat_id, html_response)
    print("[RCA] Response delivered.")
    return {"statusCode": 200, "body": "OK"}
