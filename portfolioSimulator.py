from datetime import date
import requests
import pandas as pd
import matplotlib.pyplot as plt


class PortfolioSimulator:
    def __init__(self, fund_url, scb_url, scb_query):
        self.fund_url = fund_url
        self.scb_url = scb_url
        self.scb_query = scb_query
        self.price_df = None
        self.inflation_df = None

    def fetch_fund_data(self):
        response = requests.get(self.fund_url, timeout=2.5)
        df = pd.DataFrame(response.json()["dataSerie"])
        df.rename(columns={'x': 'time', 'y': 'price'}, inplace=True)
        df.set_index(pd.to_datetime(df.pop("time"), unit="ms", utc=True), inplace=True)
        self.price_df = df

    def plot_fund_data(self, ax=None):
        if self.price_df is not None:
            ax = self.price_df.plot(title="Fund price", ax=ax)
            ax.set_xlabel("date")
            ax.set_ylabel("price")
            ax.grid()
            plt.show(block=False)

    def fetch_inflation_data(self):
        x = requests.post(self.scb_url, json=self.scb_query)
        scb_response = x.json()
        inflation_raw = scb_response['data']
        inflation_list = []
        for entry in inflation_raw:
            date_str = entry['key'][0]
            value_str = entry['values'][0]
            date_parsed = pd.to_datetime(date_str, format='%YM%m')
            value = float(value_str.replace(',', '.')) if value_str != '..' else None
            inflation_list.append({'date': date_parsed, 'inflation': value})
        inflation_df = pd.DataFrame(inflation_list).set_index('date')
        self.inflation_df = inflation_df

    def plot_inflation_data(self, ax=None):
        if self.inflation_df is not None:
            ax = self.inflation_df.plot(title="Inflation Rate", y='inflation', grid=True, ax=ax)
            ax.set_xlabel("date")
            ax.set_ylabel("inflation rate")
            plt.show(block=False)

    def simulate_portfolio(self, start_value, loan_value, loan_rate, start_date=None, end_date=None,
                           investments=None, house_investments=None, isk_rate=0.01,
                           monthly_withdrawal=0, simulate_inflation=True):


        equity_price = self.price_df
        inflation_df = self.inflation_df
        investment_value = start_value + loan_value
        investment_history = []
        debt_value_history = []
        equity_value_history = []
        new_timestamps = []
        isk_rate_monthly = (1 + isk_rate) ** (1/12) - 1
        loan_rate_monthly = (1 + loan_rate) ** (1/12) - 1
        debt_value = loan_value
        property_value = 0

        first_round = True
        for timestamp in equity_price.index:
            curr_date = date(timestamp.year, timestamp.month, 1)
            if start_date is not None and curr_date < start_date:
                continue
            if end_date is not None and curr_date > end_date:
                break
            if first_round:
                investment_history.append(investment_value)
                debt_value_history.append(debt_value)
                equity_value_history.append(investment_value - debt_value)
                new_timestamps.append(timestamp)                
                first_round = False
                continue

            year_month_timestamp = pd.Timestamp(curr_date)
            inflation_rate = 0
            if simulate_inflation and inflation_df is not None and year_month_timestamp in inflation_df.index:
                inflation_rate = 0.01 * inflation_df.loc[year_month_timestamp, 'inflation']
            if investments is not None and curr_date in investments:
                investment_value += investments[curr_date]
            if house_investments is not None and curr_date in house_investments:
                investment_value -= house_investments[curr_date]
                property_value += house_investments[curr_date]
            curr_loc = equity_price.index.get_loc(timestamp)
            if curr_loc > 0:
                previous_price = equity_price.iloc[curr_loc-1].price
            else:
                previous_price = equity_price.iloc[0].price
            monthly_gain = equity_price.loc[timestamp, "price"] / previous_price
            
            investment_value *= monthly_gain
            investment_value -= monthly_withdrawal
            investment_value -= loan_value * loan_rate_monthly
            investment_value *= (1 - isk_rate_monthly - inflation_rate)
            debt_value *= (1 - inflation_rate)
            
            if investment_value < 0:
                investment_value = 0
            investment_history.append(investment_value)
            debt_value_history.append(debt_value)
            equity_value_history.append(investment_value - debt_value)
            new_timestamps.append(timestamp)

        portfolio_value = pd.Series(investment_history, index=new_timestamps, name="Portfolio Value")
        debt_value_series = pd.Series(debt_value_history, index=new_timestamps, name="Debt Value")
        equity_value_series = pd.Series(equity_value_history, index=new_timestamps, name="Equity Value")
        return portfolio_value, debt_value_series, equity_value_series

    @staticmethod
    def calculate_performance_metrics(portfolio_series):
        start_value = portfolio_series.iloc[0]
        end_value = portfolio_series.iloc[-1]
        n_years = (portfolio_series.index[-1] - portfolio_series.index[0]).days / 365.25
        cagr = (end_value / start_value) ** (1 / n_years) - 1 if start_value > 0 else float('nan')
        running_max = portfolio_series.cummax()
        drawdown = (portfolio_series - running_max) / running_max
        max_drawdown = drawdown.min()
        monthly_returns = portfolio_series.pct_change().dropna()
        volatility = monthly_returns.std() * (12 ** 0.5)
        return {
            "CAGR": cagr,
            "Max Drawdown": max_drawdown,
            "Volatility": volatility,
            "Tot. return": end_value / start_value - 1 if start_value > 0 else float('nan')
        }

