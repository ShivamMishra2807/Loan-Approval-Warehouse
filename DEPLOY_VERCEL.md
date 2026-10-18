# Vercel Deployment Guide

This guide walks you through deploying the **Indian Loan Intelligence Warehouse** to [Vercel](https://vercel.com).

---

## ⚡ Quick Reference: Vercel "New Project" Settings

When importing `srkhandagale1601-del/loan-approval-warehouse` on Vercel, configure the fields as follows:

| Field | Setting / Value | Critical Notes |
|---|---|---|
| **Project Name** | `loan-approval-warehouse` (or any custom name) | Your public URL will be `https://<project-name>.vercel.app` |
| **Framework Preset** | **Other** | Do not pick Next.js or Vite |
| **Root Directory** | **`./` (Project Root)** | ⚠️ **DO NOT SELECT `src`**. If Vercel defaults to `src`, click **Edit**, select the root directory `./`, and click **Continue**. Selecting `src` prevents Vercel from finding `requirements.txt`, `web/`, and `models/`. |
| **Build Command** | Leave empty (toggle **OFF**) | Handled automatically by Vercel's Python runtime |
| **Output Directory** | Leave empty (toggle **OFF**) | Static routes and serverless functions are routed via [`vercel.json`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/vercel.json) |
| **Install Command** | Leave empty (toggle **OFF**) | Vercel automatically runs `pip install -r requirements.txt` |

---

## 🔐 Environment Variables (`.env`)

In the **Environment Variables** section on Vercel, add the following key-value pairs:

```env
LN_DSN=postgresql://username:password@ep-xyz.region.aws.neon.tech/neondb?sslmode=require
LN_REPORT_DIR=reports
LN_MODEL_DIR=models
LN_RANDOM_SEED=42
```

> [!IMPORTANT]
> **Database Requirement for Cloud:**
> `localhost:5432` **will not work on Vercel** because Vercel functions run in isolated AWS Lambda serverless containers in the cloud.
> You must provide a publicly accessible cloud PostgreSQL connection string for `LN_DSN`.

---

## ☁️ Step-by-Step Deployment Walkthrough

### Step 1: Set Up a Free Cloud PostgreSQL Database (2 minutes)
If you do not already have a cloud database:
1. Go to [Neon.tech](https://neon.tech) (recommended, 100% free serverless Postgres) or [Supabase](https://supabase.com).
2. Create a project named `loan-warehouse`.
3. Copy the **Direct / Pooled Connection String**:
   ```
   postgresql://neondb_owner:AbCdEf123@ep-cool-cloud.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Initialize the tables by running the SQL scripts from [`sql/schema.sql`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/sql/schema.sql) in Neon's SQL Editor, or run the ETL script locally pointing to this cloud DSN:
   ```powershell
   $env:LN_DSN="postgresql://neondb_owner:AbCdEf123@ep-cool-cloud.us-east-2.aws.neon.tech/neondb?sslmode=require"
   python -m ln.etl_loans
   python -m ln.warehouse
   python -m ln.mining
   ```

---

### Step 2: Push the Vercel Files to GitHub
The project includes the two required Vercel serverless integration files:
- [`api/index.py`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/api/index.py): Bridges requests into the FastAPI instance in `ln.api:app`.
- [`vercel.json`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/vercel.json): Configures automatic routing for `/api/*` to the serverless Python function and `/web/*` to the static analytics assets.

Commit and push them to your repository:
```bash
git add api/index.py vercel.json DEPLOY_VERCEL.md
git commit -m "feat: add Vercel serverless routing and deployment config"
git push origin main
```

---

### Step 3: Import Project in Vercel
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New…** ➔ **Project**.
3. Under **Import Git Repository**, find `srkhandagale1601-del/loan-approval-warehouse` and click **Import**.
4. In the configuration modal:
   - **Root Directory**: Make sure it is `./` (Root). If it shows `src`, click **Edit** and choose the top-level repo directory.
   - **Environment Variables**: Add `LN_DSN`, `LN_REPORT_DIR`, `LN_MODEL_DIR`, and `LN_RANDOM_SEED`.
5. Click **Deploy**.

Vercel will install Python dependencies from [`requirements.txt`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/requirements.txt), compile the serverless function, upload static web assets, and provide you with a live URL (e.g. `https://loan-approval-warehouse.vercel.app`).

---

## 🚀 Alternative: Static Showcase Deployment (No Cloud Database Needed)

If you only want to host a fast, public **demonstration/showcase** of the platform on Vercel without configuring a live PostgreSQL database:
1. Set **Root Directory** in Vercel to `web`.
2. The precomputed model metrics, confusion matrix, customer segments, and feature importances will load directly from [`web/data/`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/web/data/).
3. The platform's charts and dashboards will render purely in the browser with zero cloud infrastructure costs or cold starts.

---

## 🛠️ Common Vercel Issues & Troubleshooting

| Error | Root Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'ln'` | Root Directory was set to `src` instead of `./` | Change **Root Directory** in Vercel Project Settings to `./`. Ensure [`api/index.py`](file:///c:/Users/Lenovo/Desktop/loan-intelligence-warehouse/api/index.py) is present. |
| `psycopg.OperationalError: connection to server at "localhost"` | `LN_DSN` was not configured or still points to `localhost:5432` | Set `LN_DSN` in Vercel Environment Variables to your cloud Postgres URL (e.g. Neon, Supabase, Aiven). |
| `504 Gateway Timeout` | Serverless cold start or un-pooled database connection | In your cloud PostgreSQL URL, add `?sslmode=require` and use a pooled connection string (Neon provides pooled endpoints by default). |
| `FUNCTION_INVOCATION_TIMEOUT` | Heavy ML fitting triggered at request time | Ensure models are pre-trained locally and checked into `models/` or loaded from cache rather than training during an HTTP request. |
