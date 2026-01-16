# Truth Social ETF Holdings Viewer 🦅

A streamlined data visualization tool for analyzing the official **Truth Social ETFs**. 

This application pulls live holding data directly from the fund provider's published Google Sheets, offering a clean dashboard to explore portfolio composition, track sector weighting, and analyze cross-fund overlaps.

## Supported Funds

*   **TSSD**: American Security & Defense ETF (🦅)
*   **TSIC**: American Icons ETF (🗽)
*   **TSRS**: American Red State REITs ETF (🏘️)
*   **TSES**: American Energy Security ETF (🛢️)
*   **TSNF**: American Next Frontiers ETF (🚀)

## Features

*   **Live Data Integration**: Fetches the latest daily CSV exports from `truthsocialfunds.com`.
*   **Clean Filtering**: Automatically removes non-equity positions like Cash, Money Markets, and Cash Offsets to focus on purchasable assets.
*   **Multi-Fund Overlap**: "Matrix Mode" to identify high-conviction stocks held across multiple ETFs in the family.
*   **Consensus Visualization**: Stacked bar charts showing the combined weight of top shared assets.
*   **Interactive Tables**: Searchable, sortable holdings lists with market value and share counts.

## Usage

1.  A virtual environment is recommended:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  Install requirements:
    ```bash
    pip install streamlit pandas plotly requests
    ```

3.  Run the app:
    ```bash
    streamlit run app.py
    ```

## Data Source
All data is sourced directly from publicly available exports at [truthsocialfunds.com/etfs](https://www.truthsocialfunds.com/etfs).
