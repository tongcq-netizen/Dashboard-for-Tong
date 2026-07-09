import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# ------------------------------------
# 1. PAGE CONFIGURATION
# ------------------------------------
st.set_page_config(
    page_title="Retail Sales Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------
# 2. DATA LOADING AND PREPROCESSING
# ------------------------------------
@st.cache_data
def load_and_preprocess_data(file_path):
    # Read CSV
    df = pd.read_csv(file_path)
    
    # Text Cleaning (Fix spacing/trimming issues discovered during EDA)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    # Mixed Date Format Parser (Handles both standard strings and Excel date codes)
    def parse_mixed_date(val):
        val_str = str(val).strip()
        if val_str.isdigit():
            return pd.to_datetime(int(val_str), unit='D', origin='1899-12-30')
        else:
            return pd.to_datetime(val_str, errors='coerce')
            
    df['Order Date'] = df['Order Date'].apply(parse_mixed_date)
    df['Ship Date'] = df['Ship Date'].apply(parse_mixed_date)
    
    # Missing Value Imputation
    if 'Product Base Margin' in df.columns:
        median_margin = df['Product Base Margin'].median()
        df['Product Base Margin'] = df['Product Base Margin'].fillna(median_margin)
        
    # Calculate extra metrics
    df['Year-Month'] = df['Order Date'].dt.to_period('M').astype(str)
    
    return df

# Load the file
try:
    df = load_and_preprocess_data('mock_dataset.csv')
except FileNotFoundError:
    st.error("⚠️ 'mock_dataset.csv' not found in the current directory.")
    uploaded_file = st.file_uploader("Please upload the 'mock_dataset.csv' file manually:", type=["csv"])
    if uploaded_file is not None:
        df = load_and_preprocess_data(uploaded_file)
    else:
        st.stop()

# ------------------------------------
# 3. SIDEBAR FILTERS
# ------------------------------------
st.sidebar.header("🔍 Global Filters")

# Region Filter
all_regions = sorted(df['Region'].unique())
selected_regions = st.sidebar.multiselect("Select Region(s)", options=all_regions, default=all_regions)

# Customer Segment Filter
all_segments = sorted(df['Customer Segment'].unique())
selected_segments = st.sidebar.multiselect("Select Customer Segment(s)", options=all_segments, default=all_segments)

# Product Category Filter
all_categories = sorted(df['Product Category'].unique())
selected_categories = st.sidebar.multiselect("Select Product Category(ies)", options=all_categories, default=all_categories)

# Order Priority Filter
all_priorities = sorted(df['Order Priority'].unique())
selected_priorities = st.sidebar.multiselect("Select Order Priority", options=all_priorities, default=all_priorities)

# Filter Dataset based on selections
filtered_df = df[
    (df['Region'].isin(selected_regions)) &
    (df['Customer Segment'].isin(selected_segments)) &
    (df['Product Category'].isin(selected_categories)) &
    (df['Order Priority'].isin(selected_priorities))
]

# ------------------------------------
# 4. MAIN DASHBOARD INTERFACE
# ------------------------------------
st.title("📊 Retail Sales & Operations Dashboard")
st.markdown("An interactive app highlighting business performance, financial tracking, and data profiling metrics.")

# Top-level Metric Cards
total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Profit'].sum()
total_qty = filtered_df['Quantity ordered new'].sum()
unique_orders = filtered_df['Order ID'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="💰 Total Sales", value=f"${total_sales:,.2f}")
col2.metric(label="📈 Total Profit", value=f"${total_profit:,.2f}", delta=f"${total_profit:,.2f}", delta_color="normal")
col3.metric(label="📦 Quantity Ordered", value=f"{total_qty:,}")
col4.metric(label="🛒 Unique Orders", value=f"{unique_orders:,}")

st.markdown("---")

# Layout Tabs
tab1, tab2, tab3 = st.tabs(["📉 Sales Performance", "📦 Product & Logistics Analysis", "⚙️ Data Integrity & Explorer"])

with tab1:
    st.subheader("Time Series & Financial Breakdowns")
    
    # 1. Timeline Chart
    timeline_data = filtered_df.groupby('Year-Month')[['Sales', 'Profit']].sum().reset_index().sort_values('Year-Month')
    fig_time = px.line(
        timeline_data, x='Year-Month', y=['Sales', 'Profit'],
        title="Monthly Sales & Profit Performance Trend",
        labels={"value": "Amount ($)", "Year-Month": "Period"},
        markers=True, color_discrete_sequence=["#1f77b4", "#2ca02c"]
    )
    st.plotly_chart(fig_time, use_container_width=True)
    
    # 2. Columns for Regional and Segment Analysis
    c1, c2 = st.columns(2)
    with c1:
        segment_sales = filtered_df.groupby('Customer Segment')['Sales'].sum().reset_index()
        fig_seg = px.pie(segment_sales, values='Sales', names='Customer Segment', title='Sales Share by Customer Segment', hole=0.4)
        st.plotly_chart(fig_seg, use_container_width=True)
    with c2:
        region_profit = filtered_df.groupby('Region')['Profit'].sum().reset_index().sort_values(by='Profit', ascending=False)
        fig_reg = px.bar(region_profit, x='Region', y='Profit', color='Region', title='Net Profit Contribution by Region')
        st.plotly_chart(fig_reg, use_container_width=True)

with tab2:
    st.subheader("Category Performance & Operations")
    
    # 1. Product Category Hierarchical View
    cat_sub_perf = filtered_df.groupby(['Product Category', 'Product Sub-Category'])['Sales'].sum().reset_index()
    fig_sun = px.sunburst(cat_sub_perf, path=['Product Category', 'Product Sub-Category'], values='Sales', title='Product Sales Hierarchy')
    st.plotly_chart(fig_sun, use_container_width=True)
    
    # 2. Correlation between Unit Price, Shipping Cost & Quantity
    fig_scatter = px.scatter(
        filtered_df, x='UnitPrice', y='Shipping Cost', size='Quantity ordered new', color='Product Category',
        hover_name='Product Sub-Category', log_x=True, title='Shipping Cost vs Unit Price Dynamics (Log Scale Axis)'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    st.subheader("Data Inspector & Quality Overview")
    
    # Data Quality Stats Displayed inside App
    st.markdown("#### 🔍 Snapshot Verification Details")
    qc1, qc2, qc3 = st.columns(3)
    qc1.write(f"**Total Records Loaded:** {len(filtered_df)}")
    qc2.write(f"**Data Dimensions (Rows × Cols):** {filtered_df.shape}")
    qc3.write(f"**Auto-Handled Null Values (Product Base Margin):** Filled with median ($0.52$)")

    st.markdown("---")
    st.markdown("#### 📑 View/Filter Data Records")
    st.dataframe(filtered_df.head(200), use_container_width=True)
    
    # Export capability
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download current filtered slice as CSV",
        data=csv,
        file_name='filtered_retail_sales.csv',
        mime='text/csv',
    )