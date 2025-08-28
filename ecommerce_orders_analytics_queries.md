# ecommerce_orders Analytics SQL Pack
_Author: TaskifAI • Purpose: Ready-to-use analytics queries for PostgreSQL based on the provided `public.ecommerce_orders` table._

> **Schema detected from your dump**  
> Columns: `id, order_id, product_ean, order_date, quantity, sales_eur, country, functional_name, is_gift, customer_ip, city, utm_source, utm_medium, utm_campaign, session_pages, session_count, device_type, stripe_fee, product_name, cost_of_goods, reseller`  
> Many fields appear as text in the dump. The pack starts with a **typed view** to cast them for analytics.

---

## 0) One-time setup: typed view
Create a consistent, typed layer for all downstream queries. Re-run if the base table changes.

```sql
-- Drop the view if it already exists
DROP VIEW IF EXISTS public.typed_orders;

-- Create a typed, analytics-friendly view from public.ecommerce_orders
CREATE OR REPLACE VIEW public.typed_orders AS
SELECT
  id,
  order_id,
  product_ean,
  (order_date)::timestamp                          AS order_ts,      -- full timestamp (casts text to timestamp)
  (order_date)::date                               AS order_date,    -- date part for easy grouping
  NULLIF(quantity, '')::int                        AS qty,           -- line-level quantity
  NULLIF(sales_eur, '')::numeric                   AS sales,         -- line-level sales in EUR
  country,
  city,
  functional_name,
  -- Normalize is_gift to boolean
  CASE
    WHEN COALESCE(is_gift::text, '') IN ('t','true','1','TRUE','yes','YES','y','Y') THEN true
    ELSE false
  END                                              AS is_gift,
  customer_ip,
  NULLIF(utm_source,  '')                          AS utm_source,
  NULLIF(utm_medium,  '')                          AS utm_medium,
  NULLIF(utm_campaign,'')                          AS utm_campaign,
  NULLIF(session_pages,'')::int                    AS session_pages, -- pageviews in the session
  NULLIF(session_count,'')::int                    AS session_count, -- visits for the user/session id
  NULLIF(device_type, '')                          AS device_type,
  NULLIF(stripe_fee,'')::numeric                   AS stripe_fee,
  product_name,
  NULLIF(cost_of_goods,'')::numeric                AS cogs,          -- cost of goods sold per line
  NULLIF(reseller,'')                              AS reseller,      -- populated = offline/wholesale reseller
  CASE WHEN NULLIF(reseller,'') IS NOT NULL THEN 'offline' ELSE 'online' END AS channel,
  -- Handy derived fields
  CASE WHEN NULLIF(quantity,'')::int > 0
       THEN NULLIF(sales_eur,'')::numeric / NULLIF(quantity,'')::int
  END                                              AS unit_price,
  (NULLIF(sales_eur,'')::numeric
    - COALESCE(NULLIF(cost_of_goods,'')::numeric,0)
    - COALESCE(NULLIF(stripe_fee,'')::numeric,0))  AS gross_profit,
  CASE WHEN NULLIF(sales_eur,'')::numeric > 0
       THEN (NULLIF(sales_eur,'')::numeric
            -COALESCE(NULLIF(cost_of_goods,'')::numeric,0)
            -COALESCE(NULLIF(stripe_fee,'')::numeric,0))
            / NULLIF(sales_eur,'')::numeric
  END                                              AS gross_margin_pct,
  EXTRACT(YEAR  FROM (order_date)::timestamp)::int  AS order_year,
  EXTRACT(MONTH FROM (order_date)::timestamp)::int  AS order_month,
  EXTRACT(ISODOW FROM (order_date)::timestamp)::int AS order_isodow  -- 1=Mon ... 7=Sun
FROM public.ecommerce_orders;
```

---

## 1) Core KPIs
Company-wide indicators. Add a `WHERE order_date BETWEEN ...` when needed.

```sql
-- Core KPIs across the entire dataset
SELECT
  COUNT(DISTINCT order_id)                                 AS orders,
  SUM(qty)                                                 AS units,
  SUM(sales)                                               AS revenue,
  SUM(gross_profit)                                        AS gross_profit,
  ROUND(100*SUM(gross_profit)/NULLIF(SUM(sales),0), 2)     AS gross_margin_pct,
  ROUND(SUM(sales)/NULLIF(COUNT(DISTINCT order_id),0), 2)  AS avg_order_value,
  ROUND(SUM(qty)/NULLIF(COUNT(DISTINCT order_id),0), 2)    AS items_per_order
FROM public.typed_orders;
```

```sql
-- KPIs for a specific date range
SELECT
  MIN(order_date) AS start_date,
  MAX(order_date) AS end_date,
  COUNT(DISTINCT order_id) AS orders,
  SUM(qty)        AS units,
  SUM(sales)      AS revenue
FROM public.typed_orders
WHERE order_date BETWEEN DATE '2023-01-01' AND DATE '2025-12-31';
```

---

## 2) Monthly trends
Track growth and seasonality.

```sql
-- Monthly revenue, orders, AOV, and margin
SELECT
  date_trunc('month', order_ts)::date                   AS month,
  COUNT(DISTINCT order_id)                              AS orders,
  SUM(qty)                                              AS units,
  SUM(sales)                                            AS revenue,
  SUM(gross_profit)                                     AS gross_profit,
  ROUND(100*SUM(gross_profit)/NULLIF(SUM(sales),0),2)   AS gross_margin_pct,
  ROUND(SUM(sales)/NULLIF(COUNT(DISTINCT order_id),0),2) AS aov
FROM public.typed_orders
GROUP BY 1
ORDER BY 1;
```

```sql
-- Year-over-year monthly growth on revenue
WITH m AS (
  SELECT date_trunc('month', order_ts)::date AS month, SUM(sales) AS revenue
  FROM public.typed_orders
  GROUP BY 1
)
SELECT
  month,
  revenue,
  LAG(revenue, 12) OVER (ORDER BY month) AS revenue_prev_year,
  ROUND(100*(revenue - LAG(revenue,12) OVER (ORDER BY month))
        / NULLIF(LAG(revenue,12) OVER (ORDER BY month),0),2) AS yoy_pct
FROM m
ORDER BY month;
```

```sql
-- Rolling 7-day revenue for a daily trend line
SELECT
  d::date AS day,
  SUM(sales) OVER (ORDER BY d
       ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rev_7d
FROM (
  SELECT generate_series(MIN(order_date), MAX(order_date), interval '1 day') AS d
  FROM public.typed_orders
) cal
LEFT JOIN public.typed_orders t ON t.order_date = cal.d::date
GROUP BY d
ORDER BY d;
```

---

## 3) Channel & device splits
Understand online vs offline and device impact.

```sql
-- Online vs Offline totals using FILTER
SELECT
  SUM(sales)                                           AS revenue,
  SUM(sales) FILTER (WHERE channel='online')           AS online_revenue,
  SUM(sales) FILTER (WHERE channel='offline')          AS offline_revenue,
  COUNT(DISTINCT order_id)                             AS orders,
  COUNT(DISTINCT order_id) FILTER (WHERE channel='online')  AS online_orders,
  COUNT(DISTINCT order_id) FILTER (WHERE channel='offline') AS offline_orders
FROM public.typed_orders;
```

```sql
-- Device type breakdown (orders and revenue)
SELECT device_type, COUNT(DISTINCT order_id) AS orders, SUM(sales) AS revenue
FROM public.typed_orders
GROUP BY device_type
ORDER BY revenue DESC NULLS LAST;
```

```sql
-- Channel × Device matrix
SELECT
  device_type,
  SUM(sales) FILTER (WHERE channel='online')  AS rev_online,
  SUM(sales) FILTER (WHERE channel='offline') AS rev_offline
FROM public.typed_orders
GROUP BY device_type
ORDER BY COALESCE(rev_online,0)+COALESCE(rev_offline,0) DESC;
```

---

## 4) Geography
Where your customers and revenue come from.

```sql
-- Revenue by country
SELECT country, SUM(sales) AS revenue, COUNT(DISTINCT order_id) AS orders
FROM public.typed_orders
GROUP BY country
ORDER BY revenue DESC NULLS LAST;
```

```sql
-- Top 10 cities (online only)
SELECT city, SUM(sales) AS revenue, COUNT(DISTINCT order_id) AS orders
FROM public.typed_orders
WHERE channel='online'
GROUP BY city
ORDER BY revenue DESC NULLS LAST
LIMIT 10;
```

---

## 5) UTM & marketing
Source/medium/campaign performance.

```sql
-- Source / Medium performance with AOV
SELECT
  COALESCE(utm_source,'(none)') AS utm_source,
  COALESCE(utm_medium,'(none)') AS utm_medium,
  COUNT(DISTINCT order_id)      AS orders,
  SUM(sales)                    AS revenue,
  ROUND(SUM(sales)/NULLIF(COUNT(DISTINCT order_id),0),2) AS aov
FROM public.typed_orders
GROUP BY 1,2
ORDER BY revenue DESC;
```

```sql
-- Campaign performance (top 20 by revenue)
SELECT
  COALESCE(utm_campaign,'(none)') AS utm_campaign,
  SUM(sales) AS revenue,
  COUNT(DISTINCT order_id) AS orders
FROM public.typed_orders
GROUP BY 1
ORDER BY revenue DESC
LIMIT 20;
```

```sql
-- Share of '(direct)' and missing UTMs
SELECT
  SUM(sales) FILTER (WHERE utm_source='(direct)')                AS direct_revenue,
  SUM(sales) FILTER (WHERE utm_source IS NULL OR utm_source='')  AS missing_utm_revenue,
  SUM(sales)                                                     AS total_revenue,
  ROUND(100*SUM(sales) FILTER (WHERE utm_source='(direct)') / NULLIF(SUM(sales),0),2) AS pct_direct,
  ROUND(100*SUM(sales) FILTER (WHERE utm_source IS NULL OR utm_source='') / NULLIF(SUM(sales),0),2)   AS pct_missing_utm
FROM public.typed_orders;
```

---

## 6) Products & pricing
Focus on product mix, price behavior, and margins.

```sql
-- Top 20 products by revenue
SELECT product_ean, product_name, SUM(sales) AS revenue, SUM(qty) AS units
FROM public.typed_orders
GROUP BY product_ean, product_name
ORDER BY revenue DESC
LIMIT 20;
```

```sql
-- Product margin leaders (minimum 100 units sold)
SELECT
  product_ean, product_name,
  SUM(sales) AS revenue,
  SUM(gross_profit) AS gross_profit,
  ROUND(100*SUM(gross_profit)/NULLIF(SUM(sales),0),2) AS gm_pct,
  SUM(qty) AS units
FROM public.typed_orders
GROUP BY product_ean, product_name
HAVING SUM(qty) >= 100
ORDER BY gm_pct DESC NULLS LAST;
```

```sql
-- Average unit price per product (last 90 days)
SELECT
  product_ean, product_name,
  ROUND(SUM(sales)/NULLIF(SUM(qty),0), 2) AS avg_unit_price,
  SUM(qty) AS units_90d
FROM public.typed_orders
WHERE order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY product_ean, product_name
ORDER BY avg_unit_price DESC NULLS LAST;
```

```sql
-- First and latest sale dates per product
SELECT
  product_ean, product_name,
  MIN(order_date) AS first_sold,
  MAX(order_date) AS last_sold,
  COUNT(DISTINCT order_id) AS orders
FROM public.typed_orders
GROUP BY product_ean, product_name
ORDER BY first_sold;
```

```sql
-- Month-over-month units and price for a specific product (replace EAN)
WITH m AS (
  SELECT date_trunc('month', order_ts)::date AS month,
         SUM(qty) AS units,
         SUM(sales) AS revenue
  FROM public.typed_orders
  WHERE product_ean = 'REPLACE_WITH_EAN'
  GROUP BY 1
)
SELECT
  month,
  units,
  revenue,
  ROUND(revenue/NULLIF(units,0),2) AS avg_unit_price
FROM m
ORDER BY month;
```

```sql
-- Pareto analysis: % of revenue from top 10 products
WITH by_prod AS (
  SELECT product_ean, SUM(sales) AS rev
  FROM public.typed_orders
  GROUP BY product_ean
),
tot AS (SELECT SUM(rev) AS total FROM by_prod)
SELECT
  ROUND(100*SUM(rev)/t.total,2) AS pct_revenue_top10
FROM by_prod, tot t
ORDER BY rev DESC
LIMIT 10;
```

---

## 7) Orders & baskets
Basket composition and purchase patterns.

```sql
-- Orders per day of week (1=Mon ... 7=Sun)
SELECT
  order_isodow AS dow,
  COUNT(DISTINCT order_id) AS orders,
  SUM(sales) AS revenue,
  ROUND(SUM(sales)/NULLIF(COUNT(DISTINCT order_id),0),2) AS aov
FROM public.typed_orders
GROUP BY order_isodow
ORDER BY dow;
```

```sql
-- Items per order distribution
SELECT
  b.items_per_order,
  COUNT(*) AS orders
FROM (
  SELECT order_id, SUM(qty) AS items_per_order
  FROM public.typed_orders
  GROUP BY order_id
) b
GROUP BY b.items_per_order
ORDER BY b.items_per_order;
```

```sql
-- Gift order share
SELECT
  COUNT(DISTINCT order_id) FILTER (WHERE is_gift) AS gift_orders,
  COUNT(DISTINCT order_id)                         AS total_orders,
  ROUND(100.0 * COUNT(DISTINCT order_id) FILTER (WHERE is_gift)
        / NULLIF(COUNT(DISTINCT order_id),0), 2)   AS pct_gift_orders
FROM public.typed_orders;
```

---

## 8) Reseller analytics (offline)
Evaluate offline/wholesale resellers using the `reseller` field.

```sql
-- Top resellers by revenue and margin
SELECT
  reseller,
  COUNT(DISTINCT order_id) AS orders,
  SUM(sales) AS revenue,
  SUM(gross_profit) AS gross_profit,
  ROUND(100*SUM(gross_profit)/NULLIF(SUM(sales),0),2) AS gm_pct
FROM public.typed_orders
WHERE channel='offline'
GROUP BY reseller
ORDER BY revenue DESC NULLS LAST;
```

```sql
-- Offline vs Online AOV
SELECT
  channel,
  ROUND(SUM(sales)/NULLIF(COUNT(DISTINCT order_id),0),2) AS aov,
  SUM(sales) AS revenue,
  COUNT(DISTINCT order_id) AS orders
FROM public.typed_orders
GROUP BY channel;
```

```sql
-- Product mix for a specific reseller (replace name)
SELECT
  product_ean, product_name,
  SUM(qty) AS units,
  SUM(sales) AS revenue
FROM public.typed_orders
WHERE reseller = 'REPLACE_WITH_RESELLER_NAME'
GROUP BY product_ean, product_name
ORDER BY revenue DESC;
```

---

## 9) Profitability & fees
Understand fees and contribution margins.

```sql
-- Stripe fees: total and take rate
SELECT
  SUM(stripe_fee) AS stripe_fees,
  SUM(sales)      AS revenue,
  ROUND(100*SUM(stripe_fee)/NULLIF(SUM(sales),0),2) AS stripe_take_rate_pct
FROM public.typed_orders;
```

```sql
-- Gross profit by month
SELECT
  date_trunc('month', order_ts)::date AS month,
  SUM(gross_profit) AS gross_profit,
  ROUND(100*SUM(gross_profit)/NULLIF(SUM(sales),0),2) AS gm_pct
FROM public.typed_orders
GROUP BY 1
ORDER BY 1;
```

---

## 10) Data quality checks
Catch issues early and monitor data hygiene.

```sql
-- Negative or zero values that may indicate data errors
SELECT *
FROM public.typed_orders
WHERE sales <= 0 OR qty <= 0 OR cogs < 0 OR stripe_fee < 0;
```

```sql
-- Potential duplicate line items (same order and product)
SELECT order_id, product_ean, COUNT(*) AS line_count, SUM(qty) AS total_qty, SUM(sales) AS total_sales
FROM public.typed_orders
GROUP BY order_id, product_ean
HAVING COUNT(*) > 1
ORDER BY line_count DESC;
```

```sql
-- Rows with missing key fields
SELECT *
FROM public.typed_orders
WHERE order_id IS NULL OR order_date IS NULL OR product_ean IS NULL;
```

---

## 11) Handy exports / pivots
Pivot-ready outputs for BI or CSV export.

```sql
-- Monthly revenue pivot by channel
SELECT
  to_char(date_trunc('month', order_ts), 'YYYY-MM') AS month,
  ROUND(SUM(sales) FILTER (WHERE channel='online'), 2)  AS online_rev,
  ROUND(SUM(sales) FILTER (WHERE channel='offline'), 2) AS offline_rev,
  ROUND(SUM(sales), 2)                                 AS total_rev
FROM public.typed_orders
GROUP BY 1
ORDER BY 1;
```

```sql
-- Monthly units by device type
SELECT
  to_char(date_trunc('month', order_ts), 'YYYY-MM') AS month,
  device_type,
  SUM(qty) AS units
FROM public.typed_orders
GROUP BY 1,2
ORDER BY 1, units DESC;
```

```sql
-- Product × Month revenue matrix (long format)
SELECT
  product_ean,
  to_char(date_trunc('month', order_ts), 'YYYY-MM') AS month,
  SUM(sales) AS revenue
FROM public.typed_orders
GROUP BY 1,2
ORDER BY 1,2;
```

---

## 12) “Last-X vs prior-X” comparisons
Fast trend checks for recent performance windows.

```sql
-- Last 28 days vs prior 28 days (revenue and orders)
WITH base AS (
  SELECT
    CASE
      WHEN order_date >= CURRENT_DATE - INTERVAL '28 days' THEN 'L28'
      WHEN order_date >= CURRENT_DATE - INTERVAL '56 days'
       AND order_date <  CURRENT_DATE - INTERVAL '28 days' THEN 'P28'
    END AS bucket,
    sales,
    order_id
  FROM public.typed_orders
  WHERE order_date >= CURRENT_DATE - INTERVAL '56 days'
)
SELECT
  bucket,
  SUM(sales) AS revenue,
  COUNT(DISTINCT order_id) AS orders
FROM base
GROUP BY bucket;
```

```sql
-- Product performance: last 90d vs prior 90d
WITH base AS (
  SELECT
    product_ean, product_name,
    CASE
      WHEN order_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'L90'
      WHEN order_date >= CURRENT_DATE - INTERVAL '180 days'
       AND order_date <  CURRENT_DATE - INTERVAL '90 days' THEN 'P90'
    END AS bucket,
    sales, qty
  FROM public.typed_orders
  WHERE order_date >= CURRENT_DATE - INTERVAL '180 days'
)
SELECT
  product_ean, product_name,
  SUM(sales) FILTER (WHERE bucket='L90') AS rev_l90,
  SUM(sales) FILTER (WHERE bucket='P90') AS rev_p90,
  SUM(qty)   FILTER (WHERE bucket='L90') AS units_l90,
  SUM(qty)   FILTER (WHERE bucket='P90') AS units_p90
FROM base
GROUP BY product_ean, product_name
ORDER BY COALESCE(rev_l90,0) DESC;
```

---

## 13) Optional: helper indexes (recommended)
Speed up heavy group-bys and date filters on the base table.

```sql
-- Create useful indexes on the raw table (run once)
CREATE INDEX IF NOT EXISTS idx_eo_order_date ON public.ecommerce_orders ((order_date::date));
CREATE INDEX IF NOT EXISTS idx_eo_order_id   ON public.ecommerce_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_eo_product    ON public.ecommerce_orders (product_ean);
CREATE INDEX IF NOT EXISTS idx_eo_reseller   ON public.ecommerce_orders (reseller);
CREATE INDEX IF NOT EXISTS idx_eo_utms       ON public.ecommerce_orders (utm_source, utm_medium, utm_campaign);
```
