# Olist MaaS Pipeline

An end-to-end data intelligence system for **Olist**, Brazil's Marketplace-as-a-Service platform — turning raw e-commerce transactions into AI-powered operational insights.

---

## Table of Contents

1. [Business Context](#1-business-context)
2. [Economic Model](#2-economic-model)
3. [Business Journey](#3-business-journey)
4. [Key Findings](#4-key-findings)
5. [Strategic Recommendations](#5-strategic-recommendations)
6. [Architecture](#6-architecture)
7. [Tool Stack](#7-tool-stack)
8. [Project Structure](#8-project-structure)
9. [Data Pipeline](#9-data-pipeline)
10. [AI Agents](#10-ai-agents)
11. [Infrastructure](#11-infrastructure)
12. [Setup & Deployment](#12-setup--deployment)

---

## 1. Business Context

Olist acts as a "Digital Bridge" — allowing small-to-medium Brazilian merchants to sell through major retail platforms (Amazon, Mercado Livre, Americanas) under a single high-reputation storefront. The platform managed ~100,000 orders across 2016–2018, spanning 3,000+ active sellers across all 26 Brazilian states.

**The four core questions this project answers:**

1. **Revenue Analysis** — What geographic and economic factors drive sales performance across Brazil's 26 states?
2. **Logistics Optimisation** — Where does national infrastructure disparity inflate freight costs and delivery lead times?
3. **Value Segmentation** — Which customer cohorts and product categories generate the highest Lifetime Value?
4. **Churn Mitigation** — What are the exact delivery delay thresholds that trigger customer dissatisfaction and revenue leakage?

---

## 2. Economic Model

Olist earns from three stacked revenue streams on every transaction. Understanding how they interact is essential for interpreting every metric in this project.

| Revenue Stream | Mechanism | Financial Assumption |
|---|---|---|
| SaaS Subscriptions | Monthly platform fee | Any seller with ≥1 order in a given month is counted as "Active" and billed |
| Take Rate (Commission) | 15% of GMV | Industry-average commission applied to every successfully delivered order |
| Logistics Markup | 5% of freight value | Margin earned by reselling carrier capacity at scale — directly eroded by delays and refunds |

**Why this matters for the analysis:** Each revenue stream has a different failure mode:

- **SaaS** leaks when sellers churn — driven by poor logistics performance degrading their own reviews
- **Take Rate** leaks when orders are cancelled or refunded — driven by late delivery or damaged goods
- **Logistics Markup** leaks when freight has to be subsidised, refunded, or re-routed — driven by infrastructure tier disparities

The analysis therefore tracks **Commission Leakage** and **Seller Churn** as leading indicators of total revenue health, not just top-line GMV.

---

## 3. Business Journey

Olist is a two-sided marketplace. Revenue health depends on both sides running well simultaneously. We model each side with the **Acquisition, Retention, and Growth (ARG)** framework, powered by RFM scoring.

### Side A — Seller Journey (B2B / Supply Side)

Sellers enter through the marketing funnel and are segmented by acquisition channel and behavioral profile:

| Funnel Stage | Data Source | Key Metric | Failure Signal |
|---|---|---|---|
| Lead Generation | MQL dataset | MQL volume by origin channel | High paid spend, low MQL quality |
| Qualification | Closed deals dataset | Conversion rate, days to close | Long sales cycles → low channel ROI |
| Onboarding | Orders dataset (first order date) | Time-to-first-transaction | Stalled sellers post-signup |
| Performance | Orders + Reviews | GMV per seller, review score | Low GMV + low rating → churn risk |
| Retention | RFM scoring (Monetary axis) | Seller revenue tier | Drop in tier = early churn warning |

Sellers are further profiled by **behavioral archetype** from the funnel data:

| Archetype | Description | Strategy |
|---|---|---|
| **Shark** | Aggressive, high-volume, revenue-driven | Fast onboarding, volume incentives |
| **Wolf** | Growth-oriented, relationship-focused | Account management, co-marketing |
| **Cat** | Cautious, low-volume, quality-focused | Education, gradual scaling support |

### Side B — Customer Journey (B2C / Demand Side)

The customer lifecycle runs across six stages. Each has a measurable data signal and a targeted intervention:

| Stage | Goal | Data Signal | Intervention |
|---|---|---|---|
| **1–3. Awareness → Consideration** | Drive traffic to listings | Search volume vs. product page visits (Marketing Funnel) | Flag poor listings with AI; improve product descriptions |
| **4. Intent (Cart)** | Minimise decision friction | Cart abandonment rate by region | Freight subsidies for high-intent cohorts in high-cost regions |
| **5. Purchase & Logistics** | Fulfill on the SLA promise | SLA Variance (actual vs. estimated delivery days) | Proactive CS voucher triggered at day 4 delay — before the breaking point |
| **6. Advocacy (Post-Purchase)** | Convert buyers into repeat Champions | RFM Recency + Frequency scores, review sentiment | Referral incentives and product bundles for Potential Loyalists |

**The Breaking Point (Stage 5)** is the pivotal insight of this project. Delay tolerance is not uniform — it varies by infrastructure tier:

| Tier | Regions | Breaking Point | Action Threshold |
|---|---|---|---|
| Tier 1 | Southeast | 5 days late | Trigger CS voucher at day **4** |
| Tier 2 | South, Central-West | 7 days late | Trigger CS voucher at day **6** |
| Tier 3 | North, Northeast | 10 days late | Trigger CS voucher at day **9** |

Crossing the breaking point without intervention converts a fulfilled order into a 1-star review, Commission Leakage, and Seller Churn — compounding losses across all three revenue streams simultaneously.

### RFM Segmentation (Both Sides)

RFM scores (Recency, Frequency, Monetary) are computed at the Gold layer and map each customer and seller into actionable segments:

| Segment | % of Customers | % of Revenue | Action |
|---|---|---|---|
| Champions | 2% | — | Reward & retain |
| Loyal Customers | 5% | — | Upsell premium tiers |
| Potential Loyalists | 8% | — | Convert to loyal via bundles |
| At Risk | 15% | — | Win-back campaigns now |
| Hibernating | 48% | — | Reactivation campaigns |

> Champions + Loyal (7% of customers) generate **28% of total revenue** — a textbook Pareto distribution. Protecting this segment is the highest-leverage action available.

---

## 4. Key Findings

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

## 5. Strategic Recommendations

> Olist does not have a growth problem. It has a retention problem. Every percentage point improvement in on-time delivery translates directly to revenue retained.

### The Core Revenue Leakage

8.2% of delivered orders cross their tier-specific breaking point. Each one forfeits future customer value:

| Metric | Value |
|---|---|
| Orders past breaking point | 7,911 orders/year |
| Lost future revenue per customer | R$139.30 (AOV × 28% repeat rate × LTV multiplier) |
| Total revenue at risk annually | **R$1.1M** |
| Recovery per 1,000 orders (50% recoverable) | R$33,845 |

### Recovery Scenarios

| Scenario | Annual Revenue Recovery | Investment Required | Payback |
|---|---|---|---|
| Do nothing | R$0 (R$1.1M continues to leak) | R$0 | — |
| Quick wins only | R$440K (40% recovery) | R$50K | ~6 weeks |
| Full implementation | R$880K (80% recovery) | R$200K | **~90 days** |

---

### Immediate Actions — 0 to 30 Days

These require no new infrastructure. They use data already produced by this pipeline.

| Priority | Action | Expected Impact |
|---|---|---|
| Critical | Deploy tier-specific SLA monitoring dashboard (Databricks → Power BI) | Real-time visibility into breaking points by region |
| Critical | Trigger proactive delay notification + CS voucher at day 4 (Tier 1), day 6 (Tier 2), day 9 (Tier 3) | Intercept churn before the breaking point crystallises |
| High | Reallocate 20% of paid search budget to referral incentive program | Referral converts at 14.7% vs. 10.4% paid — +8–12% overall conversion efficiency |
| High | Concentrate ad spend on Monday–Thursday, 10am–4pm | +15% ad efficiency based on A/B engagement data |

---

### Short-Term Initiatives — 30 to 90 Days

| Initiative | Description | Expected ROI |
|---|---|---|
| Carrier Performance Scoring | Score carriers by tier; penalise underperformers via contract; surface scores in RCA agent | 10% SLA improvement |
| RFM-Triggered Win-Back Campaigns | Automated outreach for "At Risk" (15% of customers) segment using Gold layer RFM scores | 12% reactivation rate |
| Health & Beauty Subscription Pilot | Launch recurring order option for the top-revenue category (R$1.42M, 4.12 avg rating) | 25% LTV increase for converted subscribers |
| Regional Warehouse Feasibility Study | Analyse whether a Tier 3 fulfillment node in the Northeast reduces avg delivery from 17 → 12 days | Unlocks the 10% of orders currently arriving past the Tier 3 breaking point |

---

### Long-Term Strategic Investments — 90+ Days

| Investment | Description | Strategic Value |
|---|---|---|
| Predictive Delay Model | ML model trained on carrier + route + weather data to flag at-risk shipments before dispatch | Shifts from reactive CS to proactive logistics rerouting |
| Seller Quality Score | Composite score (GMV, review rating, SLA compliance) that influences search ranking on the platform | Creates a self-improving marketplace — good sellers get more visibility, reinforcing quality |
| Regional Dynamic Pricing Engine | Automatically apply freight subsidies for Tier 3 cohorts in high-intent, high-AOV categories | Closes the conversion gap in the North and Northeast without blanket discounting |
| RAG Chatbot (RCA Agent) | Full deployment of the Gemini-powered Telegram agent to all non-technical stakeholders | Democratises data access — operations, CS, and marketing answer their own questions without SQL |

---

### Marketing Channel Reallocation

Referral is the highest-converting and fastest-closing channel but receives only 2% of lead volume. The reallocation case:

| Channel | Current Share | Conversion Rate | Action |
|---|---|---|---|
| Paid Search | ~40% of budget | 10.4% | Reduce by 20% |
| Referral Program | ~2% of budget | 14.7% | Reinvest freed budget here |
| Organic Search | Zero cost | 12.2% | Double down on SEO content (zero marginal cost) |

Redirecting 20% of paid spend to referral incentives is projected to improve overall funnel conversion by 8–12% with faster close cycles (19.5 days vs. 28.4 days).

---

### Underperforming Categories — Fix or Deprioritise

| Category | Revenue | Avg Rating | Root Cause | Recommended Action |
|---|---|---|---|---|
| Office Furniture | R$420K | 3.45 | Delivery damage | Mandate reinforced packaging; carrier accountability SLA |
| Large Appliances | R$380K | 3.38 | Long delivery times | Dedicated carrier contract for bulky goods; Tier 2/3 depot |
| Garden Tools | R$210K | 3.52 | Seasonal volatility | Inventory pre-positioning before peak seasons; markdown triggers |

---

## 6. Architecture

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

## 7. Tool Stack

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

## 8. Project Structure

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

## 9. Data Pipeline

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

## 10. AI Agents

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

## 11. Infrastructure

Managed by Terraform (`terraform/main.tf`):

- **S3 Bucket:** `olist-maas-landing-{random-hex}` in `us-east-1`
- **Public access:** Fully blocked
- **Initial folders provisioned:**
  - `raw/sales/`
  - `raw/marketing/`
  - `raw/testing/`
- **Serving layer path:** `serving/gold/{table_name}/` (written by `04_gold_S3_export.py`)

---

## 12. Setup & Deployment

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
