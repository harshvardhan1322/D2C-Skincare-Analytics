import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_data
from theme import ACCENT, PALETTE, apply_theme, format_inr, kpi_card, page_header, section_header, styled_figure


apply_theme()

try:
    data = load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

page_header(
    "Customer value",
    "Customers & RFM",
    "Customer segments, acquisition-attributed revenue, and demographic geography views based on valid orders.",
)

segment = (
    data.rfm.groupby("segment", as_index=False)
    .agg(customers=("customer_id", "nunique"), avg_value=("monetary", "mean"), revenue=("monetary", "sum"))
    .sort_values("revenue", ascending=False)
)

cols = st.columns(4)
for idx, row in enumerate(segment.itertuples(index=False)):
    with cols[idx % 4]:
        kpi_card(row.segment, f"{row.customers:,}", f"Avg value {format_inr(row.avg_value)}")

left, right = st.columns([1.05, 0.95])

with left:
    section_header("RFM segment value")
    fig = px.treemap(
        segment,
        path=["segment"],
        values="customers",
        color="avg_value",
        color_continuous_scale=["#D7C8B5", "#7C8B6F", "#536044"],
        hover_data={"customers": True, "avg_value": ":,.0f", "revenue": ":,.0f"},
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(styled_figure(fig, 390), use_container_width=True)

with right:
    section_header("Revenue by acquisition channel")
    acquisition = (
        data.valid_orders.groupby("acquisition_channel", as_index=False)["gross_amount"]
        .sum()
        .rename(columns={"gross_amount": "revenue"})
        .sort_values("revenue", ascending=True)
    )
    fig = go.Figure(
        go.Bar(
            x=acquisition["revenue"],
            y=acquisition["acquisition_channel"],
            orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}<br>Revenue: ₹%{x:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Revenue", yaxis_title="")
    st.plotly_chart(styled_figure(fig, 390), use_container_width=True)

left, mid, right = st.columns(3)

with left:
    section_header("Age-group split")
    age = data.valid_orders.groupby("age_group", as_index=False)["gross_amount"].sum()
    fig = go.Figure(go.Bar(x=age["age_group"], y=age["gross_amount"], marker_color=PALETTE[: len(age)]))
    fig.update_layout(xaxis_title="", yaxis_title="Revenue")
    st.plotly_chart(styled_figure(fig, 320), use_container_width=True)

with mid:
    section_header("Gender split")
    gender = data.valid_orders.groupby("gender", as_index=False)["gross_amount"].sum()
    fig = go.Figure(
        go.Pie(
            labels=gender["gender"],
            values=gender["gross_amount"],
            hole=0.58,
            marker={"colors": ["#7C8B6F", "#D7C8B5", "#B97A5E"]},
            textinfo="label+percent",
        )
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(styled_figure(fig, 320), use_container_width=True)

with right:
    section_header("Top states")
    states = (
        data.valid_orders.groupby("state", as_index=False)["gross_amount"]
        .sum()
        .sort_values("gross_amount", ascending=True)
        .tail(8)
    )
    fig = go.Figure(
        go.Bar(
            x=states["gross_amount"],
            y=states["state"],
            orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}<br>Revenue: ₹%{x:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Revenue", yaxis_title="")
    st.plotly_chart(styled_figure(fig, 320), use_container_width=True)

section_header("Signup cohort retention")
cohort = data.cohorts.pivot(index="signup_month", columns="month_number", values="retention").fillna(0)
fig = px.imshow(
    cohort,
    aspect="auto",
    color_continuous_scale=["#FAF8F5", "#D7C8B5", "#7C8B6F", "#536044"],
    labels={"x": "Months since signup", "y": "Signup month", "color": "Retention"},
)
fig.update_traces(hovertemplate="Signup %{y}<br>Month %{x}<br>Retention %{z:.1%}<extra></extra>")
fig.update_layout(coloraxis_colorbar={"tickformat": ".0%"})
st.plotly_chart(styled_figure(fig, 460), use_container_width=True)
