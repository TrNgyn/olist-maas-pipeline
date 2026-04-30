# Olist MaaS Pipeline

An end-to-end data intelligence system for **Olist**, Brazil's Marketplace-as-a-Service platform — turning raw e-commerce transactions into AI-powered operational insights.

---

## Table of Contents

1. [Business Context](#1-business-context)
2. [Key Findings](#2-key-findings)
3. [Architecture](#3-architecture)
4. [Tool Stack](#4-tool-stack)
5. [Project Structure](#5-project-structure)
6. [Data Pipeline](#6-data-pipeline)
7. [AI Agents](#7-ai-agents)
8. [Infrastructure](#8-infrastructure)
9. [Setup & Deployment](#9-setup--deployment)

---

## 1. Business Context

Olist acts as a "Digital Bridge" — allowing small-to-medium Brazilian merchants to sell through major retail platforms (Amazon, Mercado Livre, Americanas) under a single high-reputation storefront. The platform managed ~100,000 orders across 2016–2018, spanning 3,000+ active sellers across all 26 Brazilian states.

**Revenue model applied to the dataset:**

| Stream | Model | Notes |
|---|---|---|
| SaaS Subscriptions | Monthly fee | Access, inventory sync, SEO tools |
| Take Rate | 15% of GMV | Commission on every transaction |
| Logistics Markup | 5% of freight | Revenue from shipping services |

**The four core questions this project answers:**

1. **Revenue Analysis** — What geographic and economic factors drive sales performance across Brazil's 26 states?
2. **Logistics Optimisation** — Where does national infrastructure disparity inflate freight costs and delivery lead times?
3. **Value Segmentation** — Which customer cohorts and product categories generate the highest Lifetime Value?
4. **Churn Mitigation** — What are the exact delivery delay thresholds that trigger customer dissatisfaction and revenue leakage?

---

## 2. Key Findings

### Platform Overview (2016–2018)

| Metric | Value |
|---|---|
| Total GMV | R$16.0M |
| Platform Revenue | R$2.4M (15% take rate) |
| Logistics Revenue | R$320K (5% freight markup) |
| Total Orders | 99,441 |
| Delivered Orders | 96,478 (97%) |
| Active Sellers | 3,095 |
| YoY Growth (2017→2018) | 138% |

### The Breaking Point: Delivery Delay vs. Churn

A strong negative correlation (r = -0.42, p < 0.001) between delivery delay and review score was found. Breaking points vary by infrastructure tier:

| Tier | Regions | Breaking Point | Churn Risk at Break |
|---|---|---|---|
| Tier 1 | Southeast (SP, RJ, MG) | 5 days late | 2.1× baseline |
| Tier 2 | South, Central-West | 7 days late | 2.0× baseline |
| Tier 3 | North, Northeast | 10 days late | 1.9× baseline |

**Revenue at risk:** 8.2% of delivered orders cross their tier-specific breaking point, representing ~R$1.1M in annual future revenue at risk.

### Champion Product Categories

| Category | Revenue | AOV | Avg Rating |
|---|---|---|---|
| Health & Beauty | R$1.42M | R$147 | 4.12 |
| Watches & Gifts | R$1.38M | R$230 | 4.08 |
| Bed, Bath & Table | R$1.26M | R$132 | 4.15 |
| Sports & Leisure | R$1.14M | R$132 | 4.18 |
| Computers & Accessories | R$1.09M | R$139 | 4.05 |

### Marketing Funnel

| Channel | Conversion Rate | Avg Days to Close |
|---|---|---|
| Referral | 14.7% | 19.5 days |
| Organic Search | 12.2% | 22.8 days |
| Paid Search | 10.4% | 28.4 days |
| Social Media | 9.0% | 31.2 days |

**A/B Testing:** Ad exposure drove a **+43% lift** in conversion rate vs. PSA control (chi-square = 196.07, p < 0.001). Optimal windows: Monday–Thursday, 10am–4pm.

---

## 3. Architecture

```
Raw CSVs (dataset/)
      │
      ▼  Airflow DAG triggers
┌──────────────────────────────────────────────────────────────┐
│              Medallion Pipeline — Databricks                  │
│                                                              │
│  [Bronze]      →     [Silver]      →        [Gold]           │
│  PySpark ingest     dbt transform           dbt models       │
│  + validation       + enrichment            + RFM scoring    │
│                                                 │            │
│                                          S3 Serving          │
│                                          (Parquet export)    │
└──────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │   daily_brief   │   │   rca_agent     │   │    Power BI     │
   │  Lambda (9 AM)  │   │  Lambda (Webhook)│   │  (incoming)     │
   │                 │   │                  │   │                  │
   │  S3 → Gemini →  │   │  Telegram msg →  │   │  S3 → Executive │
   │  Telegram HTML  │   │  S3 → Gemini →   │   │  Dashboard      │
   │  Executive Brief│   │  RCA Analysis    │   │                  │
   └─────────────────┘   └─────────────────┘   └─────────────────┘
```

**Infrastructure:** Terraform-provisioned AWS S3 as the central data lake. The processing layer runs on **Databricks** (PySpark notebooks) following the Medallion Architecture, with **dbt** handling Silver and Gold transformations and **Apache Airflow** (Docker on EC2) orchestrating the full pipeline. Two AWS Lambda functions serve as the AI application layer, both powered by **Google Gemini 2.0 Flash** and delivering results via Telegram. A **Power BI** executive dashboard is incoming, connecting directly to the S3 Gold serving layer.

---

## 4. Tool Stack

| Layer | Tool | Role |
|---|---|---|
| Infrastructure | Terraform | S3 bucket provisioning |
| Storage | Amazon S3 | Data lake — raw, Silver, Gold, serving |
| Processing | Databricks (PySpark) | Medallion pipeline — Bronze → Silver → Gold |
| Transformation | dbt | Silver & Gold model definitions, tests, lineage |
| Orchestration | Apache Airflow (Docker on EC2) | Schedules Databricks jobs and dbt runs |
| AI / LLM | Google Gemini 2.0 Flash | Executive briefs, RCA generation |
| Serving (AI) | AWS Lambda + API Gateway | Scheduled and on-demand agent triggers |
| Notifications | Telegram Bot API | Delivery channel for briefs and RCA responses |
| Visualisation | Power BI *(incoming)* | Executive dashboard connecting to S3 Gold layer |

---

## 5. Project Structure

```
olist-maas-pipeline/
├── dataset/                        # Source data (~150 MB, git-ignored)
│   ├── sales/                      # 11 CSV files — orders, customers, products, reviews
│   ├── marketing/                  # MQL + closed deals CSVs
│   └── testing/                    # A/B testing experiment (588K rows)
│
├── docs/
│   └── ERD.png                     # Entity-relationship diagram
│
├── notebooks/                      # Medallion pipeline (run in order)
│   ├── 01_bronze_01_ingestion.ipynb
│   ├── 01_bronze_02_validation.ipynb
│   ├── 02_silver_01_logic.ipynb
│   ├── 02_silver_02_dataquality.ipynb
│   ├── 03_gold_01_core_tables.ipynb
│   ├── 03_gold_02_scoring.ipynb
│   ├── 03_gold_03_actions.ipynb
│   └── 04_gold_S3_export.py        # Spark job — exports Gold tables to S3
│
├── src/
│   ├── daily_brief/
│   │   └── handler.py              # Lambda: daily executive briefing via Telegram
│   └── rca_agent/
│       └── handler.py              # Lambda: on-demand RCA chatbot via Telegram
│
├── terraform/
│   └── main.tf                     # S3 bucket provisioning (us-east-1)
│
└── .env                            # AWS, Gemini, Telegram credentials + KPI targets
```

---

## 6. Data Pipeline

The pipeline follows the **Medallion Architecture** across three layers:

### Bronze — Ingestion & Validation
| Notebook | Purpose |
|---|---|
| `01_bronze_01_ingestion.ipynb` | Load all CSVs, enforce schema, write Delta tables |
| `01_bronze_02_validation.ipynb` | Row counts, null checks, referential integrity |

### Silver — Transformation & Enrichment
| Notebook | Purpose |
|---|---|
| `02_silver_01_logic.ipynb` | Business logic: SLA variance, freight ratios, revenue attribution |
| `02_silver_02_dataquality.ipynb` | Anomaly detection, quality metrics |

### Gold — Analytics-Ready Serving Layer
| Notebook | Purpose |
|---|---|
| `03_gold_01_core_tables.ipynb` | Star schema: `fact_orders`, `fact_order_items`, dimension tables |
| `03_gold_02_scoring.ipynb` | RFM segmentation, customer LTV scoring |
| `03_gold_03_actions.ipynb` | Seller intervention flags, early adopter lead scoring |
| `04_gold_S3_export.py` | Spark job: exports all Gold tables to S3 as Parquet |

### Gold Tables Exported to S3

| Table | Description |
|---|---|
| `fact_orders` | Core order transactions |
| `fact_order_items` | Line-item detail |
| `dim_date` / `dim_product` / `dim_customer` / `dim_seller` | Dimension tables |
| `report_business_vitals` | Aggregated KPI snapshot |
| `rca_customer_churn_5whys` | 5-Whys churn root cause analysis |
| `rca_cancellation_leakage` | Cancellation revenue leakage |
| `action_early_adopter_leads` | High-priority seller acquisition targets |
| `action_seller_intervention` | Sellers flagged for logistics intervention |

---

## 7. AI Agents

Both agents are AWS Lambda functions powered by **Google Gemini 2.0 Flash** and communicate via **Telegram**.

### Daily Brief (`src/daily_brief/handler.py`)

- **Trigger:** AWS EventBridge scheduled rule — 9 AM daily
- **Flow:**
  1. Reads latest `report_business_vitals` Parquet from S3
  2. Aggregates: total orders, revenue (BRL), on-time delivery rate, cancellation rate, avg delivery days, active sellers
  3. Compares each metric against KPI targets (configured in `.env`)
  4. Prompts Gemini to generate a structured HTML executive briefing
  5. Delivers the formatted brief to a Telegram chat

### RCA Agent (`src/rca_agent/handler.py`)

- **Trigger:** Telegram webhook via AWS API Gateway → Lambda URL
- **Flow:**
  1. Validates sender against `AUTHORIZED_CHAT_ID` whitelist
  2. Reads `action_seller_intervention` Parquet from S3
  3. Smart-filters by region or seller ID extracted from the user's message
  4. Prompts Gemini (as a Senior Logistics Engineer using the 5 Whys framework) to diagnose the issue
  5. Returns an HTML root cause analysis back to Telegram
- **Use case:** A stakeholder can message the bot — *"Why are deliveries failing in the Northeast?"* — and receive a data-backed diagnosis instantly

---

## 8. Infrastructure

Managed by Terraform (`terraform/main.tf`):

- **S3 Bucket:** `olist-maas-landing-{random-hex}` in `us-east-1`
- **Public access:** Fully blocked
- **Initial folders provisioned:**
  - `raw/sales/`
  - `raw/marketing/`
  - `raw/testing/`
- **Serving layer path:** `serving/gold/{table_name}/` (written by `04_gold_S3_export.py`)

---

## 9. Setup & Deployment

### Prerequisites

- Python 3.9+
- Jupyter / JupyterLab
- AWS CLI configured with appropriate IAM permissions
- Terraform
- A Telegram bot token and chat ID
- A Google Gemini API key

### 1. Configure environment

Copy `.env` and fill in your credentials:

```
S3_BUCKET=olist-maas-landing-<your-suffix>
AWS_REGION=us-east-1

GEMINI_API_KEY=<your-gemini-key>

TELEGRAM_TOKEN=<your-bot-token>
CHAT_ID=<your-chat-id>
AUTHORIZED_CHAT_ID=<your-chat-id>

# KPI Targets
KPI_ONTIME_RATE_PCT=90
KPI_CANCELLATION_RATE_PCT=5
KPI_AVG_DELIVERY_DAYS=7
```

### 2. Provision infrastructure

```bash
cd terraform
terraform init
terraform apply
```

### 3. Upload raw data to S3

```bash
aws s3 sync dataset/sales/     s3://$S3_BUCKET/raw/sales/
aws s3 sync dataset/marketing/ s3://$S3_BUCKET/raw/marketing/
aws s3 sync dataset/testing/   s3://$S3_BUCKET/raw/testing/
```

### 4. Run the medallion pipeline

Execute notebooks in order inside Jupyter:

```
01_bronze_01_ingestion.ipynb
01_bronze_02_validation.ipynb
02_silver_01_logic.ipynb
02_silver_02_dataquality.ipynb
03_gold_01_core_tables.ipynb
03_gold_02_scoring.ipynb
03_gold_03_actions.ipynb
```

Then run the Spark export job:

```bash
spark-submit notebooks/04_gold_S3_export.py
```

### 5. Deploy Lambda functions

Package and deploy each handler in `src/daily_brief/` and `src/rca_agent/` to AWS Lambda. Set the `.env` variables as Lambda environment variables.

- `daily_brief`: attach an EventBridge rule for a 9 AM daily cron
- `rca_agent`: configure an API Gateway trigger and register the URL as your Telegram webhook

---

## Dataset Sources

| Dataset | Source | Size |
|---|---|---|
| Brazilian E-Commerce Public Dataset | [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | ~100K orders |
| Marketing Funnel Dataset | [Kaggle](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist) | ~8K MQLs |
| Marketing A/B Testing Dataset | [Kaggle](https://www.kaggle.com/datasets/faviovaz/marketing-ab-testing) | ~588K users |
