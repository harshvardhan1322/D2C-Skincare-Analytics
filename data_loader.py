from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).parent / "data"
DATE_FORMAT = "%d-%m-%Y"


@dataclass(frozen=True)
class DashboardData:
    customers: pd.DataFrame
    products: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    returns: pd.DataFrame
    reviews: pd.DataFrame
    valid_orders: pd.DataFrame
    valid_items: pd.DataFrame
    product_metrics: pd.DataFrame
    category_metrics: pd.DataFrame
    customer_metrics: pd.DataFrame
    rfm: pd.DataFrame
    cohorts: pd.DataFrame
    summary: dict


def _read_csv(name: str, date_cols: list[str]) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        expected = ", ".join(
            [
                "Customers.csv",
                "Products.csv",
                "Orders.csv",
                "Order_Items.csv",
                "Returns.csv",
                "Reviews.csv",
            ]
        )
        raise FileNotFoundError(
            f"Missing {name}. Place all six CSVs in {DATA_DIR}. Expected: {expected}."
        )

    return pd.read_csv(path, parse_dates=date_cols, date_format=DATE_FORMAT)


def _rfm_segment(row: pd.Series) -> str:
    if row["r_score"] >= 4 and row["fm_score"] >= 4:
        return "Champions"
    if row["r_score"] >= 3 and row["fm_score"] >= 3:
        return "Loyal"
    if row["r_score"] >= 3 and row["fm_score"] < 3:
        return "Promising"
    return "At Risk"


def _score_series(series: pd.Series, ascending: bool) -> pd.Series:
    percentile = series.rank(method="first", pct=True, ascending=ascending)
    return pd.cut(
        percentile,
        bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        labels=[1, 2, 3, 4, 5],
        include_lowest=True,
    ).astype(int)


@st.cache_data(show_spinner=False)
def load_data() -> DashboardData:
    customers = _read_csv("Customers.csv", ["signup_date"])
    products = _read_csv("Products.csv", ["launch_date"])
    orders = _read_csv("Orders.csv", ["order_date", "delivered_date"])
    order_items = _read_csv("Order_Items.csv", [])
    returns = _read_csv("Returns.csv", ["return_date"])
    reviews = _read_csv("Reviews.csv", ["review_date"])

    money_cols = ["gross_amount", "discount_amount", "shipping_fee", "final_amount"]
    orders[money_cols] = orders[money_cols].apply(pd.to_numeric)
    order_items[["quantity", "unit_price", "discount_pct", "item_total"]] = order_items[
        ["quantity", "unit_price", "discount_pct", "item_total"]
    ].apply(pd.to_numeric)
    products[["mrp", "cost_price", "stock_qty"]] = products[
        ["mrp", "cost_price", "stock_qty"]
    ].apply(pd.to_numeric)
    reviews["rating"] = pd.to_numeric(reviews["rating"])

    orders["is_valid_order"] = orders["order_status"] != "Cancelled"
    valid_orders = orders.loc[orders["is_valid_order"]].copy()

    # gross_amount is already net merchandise value after item-level discounts.
    # Revenue, AOV, profit, and order counts must exclude Cancelled orders.
    items = (
        order_items.merge(products, on="product_id", how="left")
        .merge(
            orders[
                [
                    "order_id",
                    "customer_id",
                    "order_date",
                    "order_status",
                    "sales_channel",
                    "payment_method",
                    "is_valid_order",
                ]
            ],
            on="order_id",
            how="left",
        )
        .merge(customers[["customer_id", "city", "state", "gender", "age_group", "acquisition_channel", "signup_date"]], on="customer_id", how="left")
    )
    items["gross_profit"] = items["item_total"] - (items["cost_price"] * items["quantity"])
    items["order_month"] = items["order_date"].dt.to_period("M").dt.to_timestamp()
    valid_items = items.loc[items["is_valid_order"]].copy()

    valid_orders = valid_orders.merge(
        customers[["customer_id", "state", "gender", "age_group", "acquisition_channel", "signup_date"]],
        on="customer_id",
        how="left",
    )
    valid_orders["order_month"] = valid_orders["order_date"].dt.to_period("M").dt.to_timestamp()

    product_metrics = (
        valid_items.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(
            units=("quantity", "sum"),
            revenue=("item_total", "sum"),
            gross_profit=("gross_profit", "sum"),
            orders=("order_id", "nunique"),
        )
        .sort_values("revenue", ascending=False)
    )
    product_metrics["margin_pct"] = product_metrics["gross_profit"] / product_metrics["revenue"] * 100

    category_metrics = (
        product_metrics.groupby("category", as_index=False)
        .agg(
            units=("units", "sum"),
            revenue=("revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )
    category_metrics["margin_pct"] = category_metrics["gross_profit"] / category_metrics["revenue"] * 100

    customer_metrics = (
        valid_orders.groupby("customer_id", as_index=False)
        .agg(
            last_order=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("gross_amount", "sum"),
            state=("state", "first"),
            gender=("gender", "first"),
            age_group=("age_group", "first"),
            acquisition_channel=("acquisition_channel", "first"),
            signup_date=("signup_date", "first"),
        )
    )

    snapshot_date = valid_orders["order_date"].max() + pd.Timedelta(days=1)
    rfm = customer_metrics.copy()
    rfm["recency"] = (snapshot_date - rfm["last_order"]).dt.days
    rfm["r_score"] = _score_series(rfm["recency"], ascending=False)
    rfm["f_score"] = _score_series(rfm["frequency"], ascending=True)
    rfm["m_score"] = _score_series(rfm["monetary"], ascending=True)
    rfm["fm_score"] = ((rfm["f_score"] + rfm["m_score"]) / 2).round().astype(int)
    rfm["segment"] = rfm.apply(_rfm_segment, axis=1)

    cohort_source = valid_orders[["customer_id", "order_date", "signup_date", "gross_amount"]].copy()
    cohort_source["signup_month"] = cohort_source["signup_date"].dt.to_period("M")
    cohort_source["order_month_period"] = cohort_source["order_date"].dt.to_period("M")
    cohort_source["month_number"] = (
        (cohort_source["order_month_period"].dt.year - cohort_source["signup_month"].dt.year) * 12
        + (cohort_source["order_month_period"].dt.month - cohort_source["signup_month"].dt.month)
    )
    cohorts = (
        cohort_source.loc[cohort_source["month_number"].between(0, 11)]
        .groupby(["signup_month", "month_number"])["customer_id"]
        .nunique()
        .reset_index()
    )
    cohort_sizes = customer_metrics.assign(signup_month=customer_metrics["signup_date"].dt.to_period("M")).groupby("signup_month")[
        "customer_id"
    ].nunique()
    cohorts["retention"] = cohorts.apply(lambda row: row["customer_id"] / cohort_sizes.loc[row["signup_month"]], axis=1)
    cohorts["signup_month"] = cohorts["signup_month"].astype(str)

    returned_valid_orders = returns[returns["order_id"].isin(valid_orders["order_id"])]
    summary = {
        "net_revenue": float(valid_items["item_total"].sum()),
        "gross_profit": float(valid_items["gross_profit"].sum()),
        "margin_pct": float(valid_items["gross_profit"].sum() / valid_items["item_total"].sum() * 100),
        "valid_orders": int(valid_orders["order_id"].nunique()),
        "cancelled_orders": int((orders["order_status"] == "Cancelled").sum()),
        "aov": float(valid_items["item_total"].sum() / valid_orders["order_id"].nunique()),
        "repeat_rate": float((customer_metrics["frequency"] > 1).mean() * 100),
        "return_rate": float(returned_valid_orders["order_id"].nunique() / valid_orders["order_id"].nunique() * 100),
        "avg_rating": float(reviews["rating"].mean()),
        "snapshot_date": snapshot_date,
    }

    return DashboardData(
        customers=customers,
        products=products,
        orders=orders,
        order_items=order_items,
        returns=returns,
        reviews=reviews,
        valid_orders=valid_orders,
        valid_items=valid_items,
        product_metrics=product_metrics,
        category_metrics=category_metrics,
        customer_metrics=customer_metrics,
        rfm=rfm,
        cohorts=cohorts,
        summary=summary,
    )


if __name__ == "__main__":
    data = load_data()
    summary = data.summary
    print(f"Net revenue: {summary['net_revenue']:.0f}")
    print(f"Gross profit: {summary['gross_profit']:.0f}")
    print(f"Blended margin: {summary['margin_pct']:.1f}%")
    print(f"Valid orders: {summary['valid_orders']}")
    print(f"AOV: {summary['aov']:.0f}")
    print(f"Repeat-purchase rate: {summary['repeat_rate']:.1f}%")
    print(f"Return rate: {summary['return_rate']:.1f}%")
    print(f"Avg review rating: {summary['avg_rating']:.2f}")
