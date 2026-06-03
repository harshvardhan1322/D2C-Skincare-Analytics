# D2C Skincare Analytics Dashboard

A minimal multi-page Streamlit dashboard for a synthetic D2C skincare e-commerce dataset.

## Setup

```bash
cd skincare-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Data

Place these six CSVs in `data/`:

- `Customers.csv`
- `Products.csv`
- `Orders.csv`
- `Order_Items.csv`
- `Returns.csv`
- `Reviews.csv`

The project already includes copies of the provided CSVs in `data/`.

## Pages

- Revenue Overview
- Product Profitability
- Returns & Product Quality
- Customers & RFM

## Data Rules

- Cancelled orders are excluded from revenue, profit, AOV, order-count, and RFM metrics.
- `gross_amount` is treated as net merchandise value after item-level discounts.
- Gross profit is calculated at order-item level as `item_total - cost_price * quantity`.
- `delivered_date` blanks are expected for cancelled and in-transit orders.
- Acquisition-channel charts show revenue attribution only, not CAC or ROAS.

## Sanity Checks

The pipeline is expected to produce:

- Net revenue: `₹10,95,078`
- Gross profit: `₹5,69,318`
- Blended margin: `52.0%`
- Valid orders: `1,164`
- AOV: `₹941`
- Repeat-purchase rate: `74.7%`
- Return rate: `6.8%`
- Average review rating: `3.91`
