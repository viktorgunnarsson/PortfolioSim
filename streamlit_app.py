# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date
from portfolioSimulator import PortfolioSimulator

# Streamlit setup
st.set_page_config(page_title="Portfolio Simulator", layout="wide")
st.title("📈 Portfolio Simulator")

# Default URLs and query for fund and inflation data
FUND_URL = "https://www.avanza.se/_api/fund-guide/chart/1983/1985-01-01/2025-12-31?raw=true"
SCB_URL = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/PR/PR0101/PR0101A/KPItotM"
SCB_QUERY = {
    "query": [
        {
            "code": "ContentsCode",
            "selection": {
                "filter": "item",
                "values": [
                    "000004VW"
                ]
            }
        }
    ],
    "response": {
        "format": "json"
    }
}
    
# Inputs
st.sidebar.header("Input Parameters")
fund_url = st.sidebar.text_input("Fund Data URL", value=FUND_URL)
scb_url = st.sidebar.text_input("SCB Inflation API URL", value=SCB_URL)
scb_query = st.sidebar.text_area("SCB Query (JSON)", value=str(SCB_QUERY))
start_value = st.sidebar.number_input("Initial Investment", value=1500000.0)
loan_value = st.sidebar.number_input("Loan Amount", value=500000.0)
house_cost = st.sidebar.number_input("House Cash Investment", value=1000000, step=100000)
buyhouse_year = st.sidebar.slider("Buy House After Years", min_value=0, max_value=40, value=5)
loan_rate = st.sidebar.slider("Loan Interest Rate (%)", 0.0, 10.0, value=2.0) / 100
isk_rate = st.sidebar.slider("ISK Tax Rate (%)", 0.0, 2.0, value=1.0) / 100
monthly_withdrawal = st.sidebar.number_input("Monthly Withdrawal", value=0.0)

start_date = st.sidebar.date_input("Simulation Start Date", value=date(2010, 1, 1))
end_date = st.sidebar.date_input("Simulation End Date", value=date.today())
random_start_year = st.sidebar.checkbox("Random Start Year", value=False)
curr_age = st.sidebar.slider("Current Age", min_value=0, max_value=100, value=40)

if st.sidebar.button("Run Simulation"):

    with st.spinner("Fetching data and simulating..."):
        # Setup simulator. Avoid re-initializing if already done.
        try:
            sim
        except NameError:
            sim = PortfolioSimulator(fund_url, scb_url, eval(scb_query))
            try:
                sim.fetch_fund_data()
                sim.fetch_inflation_data()
            except Exception as e:
                st.error(f"Error fetching data: {e}")
                st.stop()

        house_investments = {
            date(start_date.year + buyhouse_year, 1, 1): house_cost
        } if buyhouse_year > 0 else {}

        if random_start_year:
            start_year = np.random.randint(1985, 2016)
            end_year = start_year + 15
            end_date = date(end_year, 1, 1) if end_year <= 2025 else None
            start_date = date(start_year, 1, 1)

        # Run simulation
        portfolio, debt, equity = sim.simulate_portfolio(
            start_value=start_value,
            loan_value=loan_value,
            loan_rate=loan_rate,
            start_date=start_date,
            end_date=end_date,
            house_investments=house_investments,
            isk_rate=isk_rate,
            monthly_withdrawal=monthly_withdrawal,
        )

        # Plotting
        #st.subheader("📊 Portfolio Performance")

        # Convert to millions for better readability
        portfolio *= 1e-6
        debt *= 1e-6
        equity *= 1e-6

        x_years = curr_age + np.arange(len(portfolio)) / 12

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(x_years, portfolio, label="Portfolio")
        ax.plot(x_years, debt, label="Debt")
        ax.plot(x_years, equity, label="Equity")
        ax.set_title("Portfolio Simulation")
        ax.set_ylabel("Value, MSEK")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        # Metrics
        metrics = sim.calculate_performance_metrics(equity)
        st.subheader("📈 Performance Metrics (equity)")
        st.write({
            "CAGR": f"{metrics['CAGR']:.2%}",
            "Max Drawdown": f"{metrics['Max Drawdown']:.2%}",
            "Volatility": f"{metrics['Volatility']:.2%}",
            "Total Return": f"{metrics['Tot. return']:.2%}",
        })

