import plotly.graph_objects as go
import streamlit as st

from data_loader import load_data
from theme import ACCENT, MUTED, apply_theme, format_inr, format_pct, kpi_card, page_header, section_header, styled_figure


apply_theme()

try:
    data = load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

page_header(
    "Commercial pulse",
    "Revenue Overview",
    "A focused view of valid order revenue, profit, channel mix, and monthly demand across the 2024-2025 trading window.",
)

min_date = data.valid_orders["order_date"].min().date()
max_date = data.valid_orders["order_date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

orders = data.valid_orders[
    data.valid_orders["order_date"].dt.date.between(start_date, end_date)
].copy()
items = data.valid_items[
    data.valid_items["order_date"].dt.date.between(start_date, end_date)
].copy()

net_revenue = items["item_total"].sum()
gross_profit = items["gross_profit"].sum()
valid_orders = orders["order_id"].nunique()
aov = net_revenue / valid_orders if valid_orders else 0
repeat_rate = (
    (orders.groupby("customer_id")["order_id"].nunique() > 1).mean() * 100 if valid_orders else 0
)
margin = gross_profit / net_revenue * 100 if net_revenue else 0

cols = st.columns(6, gap="small")
with cols[0]:
    kpi_card("Net Revenue", format_inr(net_revenue, compact=True), "Valid orders only")
with cols[1]:
    kpi_card("Gross Profit", format_inr(gross_profit, compact=True), "Item-level cost basis")
with cols[2]:
    kpi_card("Margin", format_pct(margin), "Blended")
with cols[3]:
    kpi_card("AOV", format_inr(aov), "Net merchandise value")
with cols[4]:
    kpi_card("Valid Orders", f"{valid_orders:,}", f"{data.summary['cancelled_orders']} cancelled & excluded")
with cols[5]:
    kpi_card("Repeat Rate", format_pct(repeat_rate), "Within selected range")

section_header("Monthly trajectory")
monthly = (
    orders.groupby("order_month", as_index=False)
    .agg(revenue=("gross_amount", "sum"), orders=("order_id", "nunique"))
    .sort_values("order_month")
)
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=monthly["order_month"],
        y=monthly["revenue"],
        name="Revenue",
        mode="lines+markers",
        line={"color": ACCENT, "width": 3},
        fill="tozeroy",
        fillcolor="rgba(124,139,111,.14)",
    )
)
fig.add_trace(
    go.Scatter(
        x=monthly["order_month"],
        y=monthly["orders"],
        name="Orders",
        mode="lines+markers",
        yaxis="y2",
        line={"color": MUTED, "width": 2},
    )
)
fig.update_layout(
    yaxis_title="Revenue",
    yaxis2={"title": "Orders", "overlaying": "y", "side": "right", "showgrid": False},
)
st.plotly_chart(styled_figure(fig, 430), use_container_width=True)

left, right = st.columns([1.15, 0.85])

with left:
    section_header("Revenue by category")
    category = (
        items.groupby("category", as_index=False)["item_total"]
        .sum()
        .rename(columns={"item_total": "revenue"})
        .sort_values("revenue", ascending=True)
    )
    fig = go.Figure(
        go.Bar(
            x=category["revenue"],
            y=category["category"],
            orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}<br>Revenue: ₹%{x:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Revenue", yaxis_title="")
    st.plotly_chart(styled_figure(fig, 390), use_container_width=True)

with right:
    section_header("Sales channel mix")
    channel = (
        orders.groupby("sales_channel", as_index=False)["gross_amount"]
        .sum()
        .rename(columns={"gross_amount": "revenue"})
        .sort_values("revenue", ascending=False)
    )
    fig = go.Figure(
        go.Pie(
            labels=channel["sales_channel"],
            values=channel["revenue"],
            hole=0.62,
            marker={"colors": ["#7C8B6F", "#D7C8B5", "#B97A5E"]},
            textinfo="label+percent",
        )
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(styled_figure(fig, 390), use_container_width=True)
