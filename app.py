import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from io import StringIO

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Truth Social ETF Holdings",
    page_icon="🇺🇸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration for funds
FUNDS = {
    "TSSD": {
        "url": "https://docs.google.com/spreadsheets/export?id=1D13IyCB3v2_lWm9sq5BDd6Ns5vg1-vhfP_G4pYYzTO0&exportFormat=csv",
        "name": "Truth Social American Security & Defense ETF",
        "color": "#b91c1c", # Red
        "badge": "🦅"
    },
    "TSIC": {
        "url": "https://docs.google.com/spreadsheets/export?id=1j-Oe_ySv_nafdf6Ku1IWnPYqUy8RbnK7pyXM7YzPorQ&exportFormat=csv",
        "name": "Truth Social American Icons ETF",
        "color": "#eab308", # Yellow/Gold
        "badge": "🗽"
    },
    "TSRS": {
        "url": "https://docs.google.com/spreadsheets/export?id=1uldRmdGtQDS-U9okf-jVRoCP6EYlD48ct9Vk5JP-LEo&exportFormat=csv",
        "name": "Truth Social American Red State REITs ETF",
        "color": "#9f1239", # Rose/Brick
        "badge": "🏘️"
    },
    "TSES": {
        "url": "https://docs.google.com/spreadsheets/export?id=1ZD51az6CmBnxuLU4WvzjCmWgiP7b612FKrCm2LIriF0&exportFormat=csv",
        "name": "Truth Social American Energy Security ETF",
        "color": "#f97316", # Orange
        "badge": "🛢️"
    },
    "TSNF": {
        "url": "https://docs.google.com/spreadsheets/export?id=1ZxBouTG4aWPMPf7mbxu_qo9AHiOh7uuNEFekrCC1Ym0&exportFormat=csv",
        "name": "Truth Social American Next Frontiers ETF",
        "color": "#3b82f6", # Blue
        "badge": "🚀"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #172554 100%);
        color: #e2e8f0;
    }
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #ef4444, #f8fafc, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
    }
    .sub-header {
        text-align: center;
        color: #94a3b8;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 3rem;
        letter-spacing: 1px;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #94a3b8;
        font-weight: 500;
    }
    .stDataFrame {
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900) # Cache for 15 minutes
def fetch_holdings(fund_key: str) -> pd.DataFrame:
    """Download and parse holdings CSV."""
    config = FUNDS.get(fund_key)
    if not config:
        return pd.DataFrame()

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(config["url"], headers=headers, timeout=15)
        if response.status_code != 200:
            st.error(f"Failed to download data: Status {response.status_code}")
            return pd.DataFrame()
        
        # Parse CSV
        # Expected columns: Date, Account, Stock Ticker, CUSIP, Security Name, Shares, Price, Market Value, Weightings, Net Assets
        df = pd.read_csv(StringIO(response.text))
        
        # Rename columns to standard format
        rename_map = {
            'Stock Ticker': 'Ticker',
            'Security Name': 'Name',
            'Weightings': 'Weight',
            'Market Value': 'MarketValue',
            'Shares': 'Shares'
        }
        df = df.rename(columns=rename_map)
        
        # Clean data
        if 'Weight' in df.columns:
            # Handle string percentages if present
            if df['Weight'].dtype == object:
                df['Weight'] = df['Weight'].astype(str).str.replace('%', '', regex=False).str.strip().replace('', '0')
                df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce').fillna(0.0)
        
        if 'MarketValue' in df.columns:
             # Ensure numeric, remove commas if any
             if df['MarketValue'].dtype == object:
                 df['MarketValue'] = df['MarketValue'].astype(str).str.replace(',', '', regex=False)
             df['MarketValue'] = pd.to_numeric(df['MarketValue'], errors='coerce').fillna(0.0)

        # Filter out cash/other if desired, or keep them. 
        # Usually valid tickers are best.
        # Let's keep everything but ensure Ticker is present for core holdings logic
        # df = df.dropna(subset=['Ticker']) 
        
        # Filter out "silly" holdings (Cash, Money Markets)
        if 'Ticker' in df.columns and 'Name' in df.columns:
            # Remove explicit "Cash&Other"
            df = df[df['Ticker'] != 'Cash&Other']
            
            # Remove Money Market funds and Deposit Accounts
            # We treat these as cash equivalents, not things to "buy"
            silly_patterns = ['Money Market', 'Deposit Account', 'Liquidity Fund', 'Cash Offset']
            mask = df['Name'].astype(str).apply(lambda x: any(p.lower() in x.lower() for p in silly_patterns))
            df = df[~mask]

        return df
        
    except Exception as e:
        st.error(f"Error parsing data: {str(e)}")
        return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

# Sidebar Selection
with st.sidebar:
    st.markdown("### Select ETF")
    
    # Add Overlap to options
    options = list(FUNDS.keys()) + ["OVERLAP"]
    
    selected_fund_key = st.selectbox(
        "Choose a Fund",
        options=options,
        format_func=lambda x: "📊 Multi-Fund View" if x == "OVERLAP" else f"{FUNDS[x]['badge']} {x}"
    )
    
    st.markdown("---")
    if selected_fund_key != "OVERLAP":
        st.info(f"**{FUNDS[selected_fund_key]['name']}**")
    else:
        st.info("**Consolidated view of all Truth Social ETFs**")
        
    st.caption("Data source: Truth Social Funds")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

if selected_fund_key == "OVERLAP":
    # ─────────────────────────────────────────────────────────────────────────────
    # OVERLAP MODE
    # ─────────────────────────────────────────────────────────────────────────────
    st.markdown('<div class="main-header">AMERICA FIRST ETF</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Fund Consolidated View</div>', unsafe_allow_html=True)
    
    all_data = []
    
    # Fetch all funds
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, key in enumerate(FUNDS.keys()):
        status_text.text(f"Fetching {key}...")
        df = fetch_holdings(key)
        if not df.empty:
            df['Fund'] = key
            all_data.append(df)
        progress_bar.progress((i + 1) / len(FUNDS))
            
    status_text.empty()
    progress_bar.empty()
    
    if not all_data:
        st.warning("Could not load fund data.")
        st.stop()
        
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Analyze overlaps
    # Count how many funds hold each ticker
    overlap_counts = combined_df.groupby(['Ticker', 'Name'])['Fund'].nunique().reset_index()
    overlap_counts.columns = ['Ticker', 'Name', 'FundCount']
    
    # Sort by overlap count
    # overlaps = overlap_counts[overlap_counts['FundCount'] > 1].sort_values('FundCount', ascending=False)
    # USER REQUEST: Show ALL holdings, not just overlaps
    overlaps = overlap_counts.sort_values('FundCount', ascending=False)
    
    if overlaps.empty:
        st.info("No holdings found.")
    else:
        # Create Pivot Table for weights
        pivot_df = combined_df.pivot_table(
            index=['Ticker', 'Name'], 
            columns='Fund', 
            values='Weight', 
            aggfunc='sum'
        ).reset_index()
        
        # Merge with counts to filter and sort
        final_df = overlaps.merge(pivot_df, on=['Ticker', 'Name'])
        final_df = final_df.sort_values(['FundCount', 'Ticker'], ascending=[False, True])
        
        # Metrics
        total_combined_assets = combined_df['MarketValue'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
             st.metric("Total Net Assets (Combined)", f"${total_combined_assets:,.0f}")
        with col2:
            st.metric("Total Unique Holdings", len(final_df))
        with col3:
            overlap_kount = len(final_df[final_df['FundCount'] > 1])
            st.metric("Overlapping Assets", overlap_kount)
            
        st.markdown("### 🔗 Consolidated Holdings Matrix")
        
        # Configure columns dynamically
        column_config = {
            "Ticker": st.column_config.TextColumn("Symbol", width="small"),
            "Name": st.column_config.TextColumn("Company Name", width="large"),
            "FundCount": st.column_config.NumberColumn("Funds", format="%d 🏢"),
        }
        
        # Add color-coded columns for each fund
        for fund in FUNDS:
            if fund in final_df.columns:
                column_config[fund] = st.column_config.NumberColumn(
                    f"{fund}", 
                    format="%.2f%%",
                )
        
        # Show the table
        st.dataframe(
            final_df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        # Visualization: Stacked Bar of Weights for Top Overlaps
        st.markdown("### 🏆 Top Consensus Holdings (By Total Weight)")
        
        # Calculate total weight across all funds for sorting
        final_df['TotalWeight'] = final_df[list(FUNDS.keys())].sum(axis=1, numeric_only=True)
        top_consensus = final_df.sort_values('TotalWeight', ascending=False).head(20)
        
        # Melt for plotting
        melted = top_consensus.melt(
            id_vars=['Ticker', 'Name'], 
            value_vars=[f for f in FUNDS.keys() if f in top_consensus.columns],
            var_name='Fund', 
            value_name='Weight'
        )
        melted = melted[melted['Weight'] > 0] # Remove 0 weights
        
        # Custom color map
        color_map = {k: v['color'] for k, v in FUNDS.items()}
        
        fig = px.bar(
            melted,
            x='Weight',
            y='Ticker',
            color='Fund',
            orientation='h',
            title="Combined Weight of Top Assets",
            color_discrete_map=color_map,
            hover_data=['Name']
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            xaxis_title="Total Weight (%)",
            yaxis_title="Ticker",
            legend_title="Fund"
        )
        
        st.plotly_chart(fig, use_container_width=True)


else:
    # ─────────────────────────────────────────────────────────────────────────────
    # SINGLE FUND MODE
    # ─────────────────────────────────────────────────────────────────────────────
    
    # Header
    st.markdown('<div class="main-header">AMERICA FIRST ETF</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{FUNDS[selected_fund_key]["name"]} (${selected_fund_key})</div>', unsafe_allow_html=True)
    
    # Load Data
    with st.spinner(f"Retrieving latest holdings for {selected_fund_key}..."):
        df = fetch_holdings(selected_fund_key)

    if df.empty:
        st.warning("No data available. Please try again later.")
        st.stop()
    
    # Metrics, Chart, and Table (Existing Logic)
    # Calculate high-level stats
    total_assets = df['MarketValue'].sum()
    total_holdings = len(df)
    top_holding = df.loc[df['Weight'].idxmax()] if not df.empty else None

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Net Assets", f"${total_assets:,.0f}")

    with col2:
        st.metric("Total Holdings", total_holdings)

    with col3:
        if top_holding is not None:
            st.metric("Top Holding", top_holding['Ticker'], f"{top_holding['Weight']:.2f}%")
        else:
            st.metric("Top Holding", "-")

    with col4:
        # Just a spacer or another metric if we had sector data
        avg_weight = df['Weight'].mean()
        st.metric("Avg Weight", f"{avg_weight:.2f}%")


    st.markdown("---")

    # Layout: Chart on Left, Table on Right
    col_chart, col_list = st.columns([1, 1])

    with col_chart:
        st.subheader("Top 15 Holdings by Weight")
        top_15 = df.nlargest(15, 'Weight').sort_values('Weight', ascending=True)
        
        # Use specific color for the chart based on fund
        fund_color = FUNDS[selected_fund_key]["color"]
        
        fig = px.bar(
            top_15,
            x='Weight',
            y='Name',
            orientation='h',
            text_auto='.2f',
        )
        
        # Update traces to use the fund color
        fig.update_traces(
            marker_color=fund_color,
            textposition="outside", 
            cliponaxis=False
        )
        
        fig.update_layout(
            xaxis_title="Weight (%)",
            yaxis_title=None,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            height=600,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)'),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_list:
        st.subheader("Holdings Detail")
        
        # Search box
        search = st.text_input("Find a company...", placeholder="Search ticker or name")
        
        if search:
            mask = df['Ticker'].astype(str).str.contains(search, case=False, na=False) | \
                   df['Name'].astype(str).str.contains(search, case=False, na=False)
            display_df = df[mask]
        else:
            display_df = df

        # Configure columns for clean display
        # Ticker, Name, Shares, Market Value, Weight
        
        st.dataframe(
            display_df[['Ticker', 'Name', 'Shares', 'MarketValue', 'Weight']],
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "Ticker": st.column_config.TextColumn("Symbol", width="small"),
                "Name": st.column_config.TextColumn("Company Name", width="large"),
                "Shares": st.column_config.NumberColumn("Shares", format="%d"),
                "MarketValue": st.column_config.NumberColumn("Market Value", format="$%.2f"),
                "Weight": st.column_config.ProgressColumn(
                    "Weight",
                    format="%.2f%%",
                    min_value=0,
                    max_value=10, 
                ),
            }
        )
