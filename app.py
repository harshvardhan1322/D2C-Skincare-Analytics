import streamlit as st

from theme import apply_theme


st.set_page_config(
    page_title="D2C Skincare Analytics",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

pages = [
    st.Page("pages/1_Revenue_Overview.py", title="Revenue Overview"),
    st.Page("pages/2_Product_Profitability.py", title="Product Profitability"),
    st.Page("pages/3_Returns_and_Quality.py", title="Returns & Quality"),
    st.Page("pages/4_Customers_and_RFM.py", title="Customers & RFM"),
]

navigation = st.navigation(pages)
navigation.run()
