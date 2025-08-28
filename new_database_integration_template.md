# New Database Integration Template

Please fill out this template with information about your new table so I can integrate it seamlessly into the chat system.

## 1. Basic Table Information

### Table Name
**Table name:** `[ecommerce_orders]`

### Location
- [x] Same Supabase database as current system
- [ ] Different database (specify): ________________
- [ ] Different schema: ________________

## 2. Table Schema

### Columns
create table public.ecommerce_orders (
  id uuid not null default gen_random_uuid (),
  order_id text null,
  product_ean text null,
  order_date date null,
  quantity numeric null,
  sales_eur numeric null,
  country text null default 'WooCommerce'::text,
  functional_name text null,
  is_gift boolean null,
  customer_ip text null,
  city text null,
  utm_source text null,
  utm_medium text null,
  utm_campaign text null,
  session_pages text null,
  session_count text null,
  device_type text null,
  stripe_fee numeric null,
  product_name text null,
  cost_of_goods numeric null,
  reseller text null default 'Online'::text,
  constraint ecommerce_orders_pkey primary key (id),
  constraint ecommerce_orders_product_ean_fkey foreign KEY (product_ean) references products (ean)
) TABLESPACE pg_default;

### Primary Key
**Primary key column(s):** `[id]`


```

## 4. Relationship to Existing Data

### Connection to `sellout_entries2`
- [ ] This table should be joined with `sellout_entries2`
- [ ] This table is independent but related
- [x] This table is completely separate


## 5. Business Context

### Data Type
What type of data does this table contain?
- [ ] Sales/transaction data
- [ ] Product information
- [ ] Inventory/stock data
- [x| Customer/reseller data
- [ ] Financial data
- [ ] Operational data
- [ ] Other: ________________

### Business Purpose
Describe what this data represents:
```
[Describe the business purpose and what this table tracks]
```

## 6. Chat Integration Requirements

### Query Scenarios
When should the chat system query this table? Check all that apply:

- [ ] When users ask about sales performance
- [ ] When users ask about inventory/stock
- [ ] When users ask about products
- [ ] When users ask about customers/resellers
- [ ] When users ask about financial metrics
- [ ] When users ask about time-based trends
- [ ] When specific keywords are mentioned: ________________
- [x] Other scenarios: when user is using the chat
