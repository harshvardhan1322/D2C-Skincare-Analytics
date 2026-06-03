import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_data
from theme import ACCENT, TERRACOTTA, apply_theme, format_inr, page_header, section_header, styled_figure


apply_theme()

try:
    data = load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

page_header(
    "Assortment economics",
    "Product Profitability",
    "The product view separates volume winners from richer-margin opportunities using item-level gross profit.",
)

categories = sorted(data.product_metrics["category"].unique())
selected = st.sidebar.multiselect("Category", categories, default=categories)
products = data.product_metrics[data.product_metrics["category"].isin(selected)].copy()

section_header("Revenue vs margin")
x_mid = products["revenue"].median()
y_mid = products["margin_pct"].median()
fig = px.scatter(
    products,
    x="revenue",
    y="margin_pct",
    size="units",
    color="category",
    hover_name="product_name",
    hover_data={"revenue": ":,.0f", "margin_pct": ":.1f", "units": ":,.0f", "category": True},
    color_discrete_sequence=["#7C8B6F", "#AEB89C", "#D7C8B5", "#B97A5E", "#8C8378", "#C7B7A3", "#5F6C54", "#A49383", "#DCCFC0"],
)
fig.add_vline(x=x_mid, line_dash="dot", line_color="#C9BFB4")
fig.add_hline(y=y_mid, line_dash="dot", line_color="#C9BFB4")
fig.add_annotation(x=products["revenue"].max(), y=products["margin_pct"].max(), text="Scale + margin", showarrow=False, xanchor="right")
fig.add_annotation(x=products["revenue"].max(), y=products["margin_pct"].min(), text="Volume, thinner margin", showarrow=False, xanchor="right")
fig.add_annotation(x=products["revenue"].min(), y=products["margin_pct"].max(), text="Niche profit", showarrow=False, xanchor="left")
fig.add_annotation(x=products["revenue"].min(), y=products["margin_pct"].min(), text="Watchlist", showarrow=False, xanchor="left")
fig.update_layout(xaxis_title="Revenue", yaxis_title="Margin %")
st.plotly_chart(styled_figure(fig, 520), use_container_width=True)

left, right = st.columns([0.95, 1.05])

with left:
    section_header("Margin by category")
    category = data.category_metrics[data.category_metrics["category"].isin(selected)].sort_values("margin_pct")
    fig = go.Figure(
        go.Bar(
            x=category["margin_pct"],
            y=category["category"],
            orientation="h",
            marker_color=[ACCENT if value < 53 else TERRACOTTA for value in category["margin_pct"]],
            hovertemplate="%{y}<br>Margin: %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Gross margin %", yaxis_title="")
    st.plotly_chart(styled_figure(fig, 430), use_container_width=True)

with right:
    section_header("Top products")
    table = products[
        ["product_name", "category", "units", "revenue", "gross_profit", "margin_pct"]
    ].copy()
    table = table.sort_values("revenue", ascending=False)
    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "product_name": st.column_config.TextColumn("Product"),
            "category": st.column_config.TextColumn("Category"),
            "units": st.column_config.NumberColumn("Units", format="%d"),
            "revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
            "gross_profit": st.column_config.NumberColumn("Gross Profit", format="₹%d"),
            "margin_pct": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
        },
    )

st.caption(
    f"Across the selected assortment: {format_inr(products['revenue'].sum())} revenue and "
    f"{format_inr(products['gross_profit'].sum())} gross profit."
)
