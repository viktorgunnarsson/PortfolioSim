from flask import Flask, request, jsonify, send_from_directory
from portfolioSimulator import PortfolioSimulator
from datetime import date
import pandas as pd

app = Flask(__name__)

# Default URLs and query for the simulator
fund_url = "https://www.avanza.se/_api/fund-guide/chart/1983/1985-01-01/2025-12-31?raw=true"
scb_url = "https://api.scb.se/OV0104/v1/doris/sv/ssd/START/PR/PR0101/PR0101A/KPItotM"
scb_query = {
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

sim = PortfolioSimulator(fund_url, scb_url, scb_query)
sim.fetch_fund_data()
sim.fetch_inflation_data()

def parse_date(d):
    if isinstance(d, str):
        return pd.to_datetime(d).date()
    if isinstance(d, list) and len(d) == 3:
        return date(*d)
    return d

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')    

@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.json

    # Parse parameters with defaults
    start_value = float(data.get("start_value", 1500000))
    loan_value = float(data.get("loan_value", 500000))
    loan_rate = float(data.get("loan_rate", 0.02))
    isk_rate = float(data.get("isk_rate", 0.01))
    monthly_withdrawal = float(data.get("monthly_withdrawal", 0))
    simulate_inflation = bool(data.get("simulate_inflation", True))

    start_date = parse_date(data.get("start_date", "2000-01-01"))
    end_date = data.get("end_date")
    if end_date:
        end_date = parse_date(end_date)
    else:
        end_date = None

    investments = data.get("investments", {})
    house_investments = data.get("house_investments", {})

    # Convert investment keys to date objects
    investments = {parse_date(k): v for k, v in investments.items()}
    house_investments = {parse_date(k): v for k, v in house_investments.items()}

    # Run simulation
    portfolio_value, debt_value, equity_value = sim.simulate_portfolio(
        start_value,
        loan_value,
        loan_rate,
        start_date,
        end_date,
        investments,
        house_investments,
        isk_rate,
        monthly_withdrawal,
        simulate_inflation
    )

    # Prepare response
    result = {
        "portfolio_value": portfolio_value.tolist(),
        "debt_value": debt_value.tolist(),
        "equity_value": equity_value.tolist(),
        "dates": [str(d.date()) for d in portfolio_value.index],
    }

    # Metrics (on equity value)
    metrics = sim.calculate_performance_metrics(equity_value)
    result["metrics"] = metrics

    return jsonify(result)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
    #app.run(debug=True)