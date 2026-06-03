import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_data
from theme import ACCENT, TERRACOTTA, apply_theme, page_header, section_header, styled_figure


apply_theme()

try:
    data = load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

page_header(
    "Post-purchase signals",
    "Returns & Product Quality",
    "Returns and reviews are overlaid to surface products that deserve operational or formulation attention.",
)

returns = data.returns.merge(
    data.products[["product_id", "product_name", "category"]],
    on="product_id",
    how="left",
)
reviews = data.reviews.merge(
    data.products[["product_id", "product_name", "category"]],
    on="product_id",
    how="left",
)

left, right = st.columns([0.9, 1.1])

with left:
    section_header("Returns by reason")
    reason = returns["return_reason"].value_counts().sort_values().reset_index()
    reason.columns = ["return_reason", "returns"]
    fig = go.Figure(
        go.Bar(
            x=reason["returns"],
            y=reason["return_reason"],
            orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}<br>Returns: %{x}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Returns", yaxis_title="")
    st.plotly_chart(styled_figure(fig, 360), use_container_width=True)

with right:
    section_header("Quality-risk quadrant")
    return_counts = returns.groupby("product_id", as_index=False).agg(return_count=("return_id", "nunique"))
    rating_avg = reviews.groupby("product_id", as_index=False).agg(avg_rating=("rating", "mean"), review_count=("review_id", "nunique"))
    quality = (
        data.products[["product_id", "product_name", "category"]]
        .merge(return_counts, on="product_id", how="left")
        .merge(rating_avg, on="product_id", how="left")
        .fillna({"return_count": 0, "avg_rating": 0, "review_count": 0})
    )
    fig = px.scatter(
        quality,
        x="return_count",
        y="avg_rating",
        size="review_count",
        color="category",
        hover_name="product_name",
        hover_data={"return_count": True, "avg_rating": ":.2f", "review_count": True, "category": True},
        color_discrete_sequence=["#7C8B6F", "#AEB89C", "#D7C8B5", "#B97A5E", "#8C8378", "#C7B7A3", "#5F6C54", "#A49383", "#DCCFC0"],
    )
    fig.add_vline(x=quality["return_count"].median(), line_dash="dot", line_color="#C9BFB4")
    fig.add_hline(y=quality.loc[quality["avg_rating"] > 0, "avg_rating"].median(), line_dash="dot", line_color="#C9BFB4")
    fig.add_annotation(
        x=quality["return_count"].max(),
        y=quality.loc[quality["avg_rating"] > 0, "avg_rating"].min(),
        text="High returns + low rating",
        showarrow=False,
        xanchor="right",
    )
    fig.update_layout(xaxis_title="Return count", yaxis_title="Average rating")
    st.plotly_chart(styled_figure(fig, 360), use_container_width=True)

left, right = st.columns(2)

with left:
    section_header("Rating distribution")
    ratings = reviews["rating"].value_counts().sort_index().reset_index()
    ratings.columns = ["rating", "reviews"]
    fig = go.Figure(
        go.Bar(
            x=ratings["rating"],
            y=ratings["reviews"],
            marker_color=[TERRACOTTA if value <= 2 else ACCENT for value in ratings["rating"]],
            hovertemplate="Rating %{x}<br>Reviews: %{y}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Rating", yaxis_title="Reviews")
    st.plotly_chart(styled_figure(fig, 340), use_container_width=True)

with right:
    section_header("Refund status")
    status = returns["refund_status"].value_counts().reset_index()
    status.columns = ["refund_status", "returns"]
    fig = go.Figure(
        go.Pie(
            labels=status["refund_status"],
            values=status["returns"],
            hole=0.58,
            marker={"colors": ["#7C8B6F", "#D7C8B5", "#B97A5E"]},
            textinfo="label+percent",
        )
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(styled_figure(fig, 340), use_container_width=True)

section_header("Product watchlist")
watchlist = quality.sort_values(["return_count", "avg_rating"], ascending=[False, True]).head(10)
st.dataframe(
    watchlist[["product_name", "category", "return_count", "avg_rating", "review_count"]],
    hide_index=True,
    use_container_width=True,
    column_config={
        "product_name": st.column_config.TextColumn("Product"),
        "return_count": st.column_config.NumberColumn("Returns", format="%d"),
        "avg_rating": st.column_config.NumberColumn("Avg Rating", format="%.2f"),
        "review_count": st.column_config.NumberColumn("Reviews", format="%d"),
    },
)
