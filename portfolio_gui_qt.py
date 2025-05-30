from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFormLayout, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from datetime import date
from portfolioSimulator import PortfolioSimulator
import sys
import numpy as np

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

class PortfolioSimulatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portfolio Simulator")
        self.resize(1000, 700)
        self.sim = PortfolioSimulator(fund_url, scb_url, scb_query)
        self.sim.fetch_fund_data()
        self.sim.fetch_inflation_data()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        form_layout = QFormLayout()

        # Parameter fields
        self.start_value = QDoubleSpinBox()
        self.start_value.setMaximum(1e9)
        self.start_value.setSingleStep(100000)
        self.start_value.setValue(1500000)
        self.start_value.setDecimals(0)

        self.loan_value = QDoubleSpinBox()
        self.loan_value.setMaximum(1e9)
        self.loan_value.setSingleStep(100000)
        self.loan_value.setValue(500000)
        self.loan_value.setDecimals(0)

        self.loan_rate = QDoubleSpinBox()
        self.loan_rate.setDecimals(2)
        self.loan_rate.setSingleStep(0.1)
        self.loan_rate.setValue(2)

        self.isk_rate = QDoubleSpinBox()
        self.isk_rate.setDecimals(2)
        self.isk_rate.setSingleStep(0.1)
        self.isk_rate.setValue(1)

        self.monthly_cost = QDoubleSpinBox()
        self.monthly_cost.setMaximum(1e6)
        self.monthly_cost.setSingleStep(1000)
        self.monthly_cost.setValue(22000)
        self.monthly_cost.setDecimals(0)

        self.monthly_salary = QDoubleSpinBox()
        self.monthly_salary.setMaximum(1e6)
        self.monthly_salary.setSingleStep(1000)
        self.monthly_salary.setValue(32000)
        self.monthly_salary.setDecimals(0)

        self.house_cost = QDoubleSpinBox()
        self.house_cost.setMaximum(1e9)
        self.house_cost.setSingleStep(100000)
        self.house_cost.setValue(1000000)
        self.house_cost.setDecimals(0)

        self.start_year = QSpinBox()
        self.start_year.setRange(1985, 2025)
        self.start_year.setValue(2000)

        self.number_years = QSpinBox()
        self.number_years.setRange(1, 40)
        self.number_years.setValue(40)

        self.curr_age = QSpinBox()
        self.curr_age.setRange(0, 120)
        self.curr_age.setValue(41)

        self.buyhouse_year = QSpinBox()
        self.buyhouse_year.setRange(0, 100)
        self.buyhouse_year.setValue(5)

        self.simulate_inflation = QCheckBox("Adjust for Inflation")
        self.simulate_inflation.setChecked(True)

        self.random_start_year = QCheckBox("Random Start Year")
        self.random_start_year.setChecked(False)

        self.include_loan = QCheckBox("Include Loan for Leverage")
        self.include_loan.setChecked(True)

        self.hold_plot = QCheckBox("Hold Plot")
        self.hold_plot.setChecked(False)

        form_layout.addRow("Start Value", self.start_value)
        form_layout.addRow("Loan Value", self.loan_value)
        form_layout.addRow("Loan Rate (%)", self.loan_rate)
        form_layout.addRow("ISK Rate (%)", self.isk_rate)
        form_layout.addRow("Monthly Cost", self.monthly_cost)
        form_layout.addRow("Monthly Salary", self.monthly_salary)
        form_layout.addRow("House Cash Investment", self.house_cost)
        form_layout.addRow("Start Year", self.start_year)
        form_layout.addRow("Sim. Number of Years", self.number_years)
        form_layout.addRow("Current Age", self.curr_age)
        form_layout.addRow("Buy House After Years", self.buyhouse_year)
        form_layout.addRow(self.simulate_inflation)
        form_layout.addRow(self.include_loan)
        self.include_loan.toggled.connect(lambda: self.loan_value.setEnabled(self.include_loan.isChecked()))

        form_layout.addRow(self.hold_plot)
        form_layout.addRow(self.random_start_year)
        self.random_start_year.toggled.connect(lambda: self.start_year.setEnabled(not self.random_start_year.isChecked()))

        self.run_button = QPushButton("Run Simulation")
        self.run_button.clicked.connect(self.run_simulation)
        form_layout.addRow(self.run_button)

        self.metrics_label = QLabel("Metrics will be shown here.")
        self.metrics_label.setWordWrap(True)
        form_layout.addRow(self.metrics_label)        

        # Matplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))        

        #self.plotfund_button = QPushButton("Plot fund price")
        #self.plotfund_button.clicked.connect(lambda: self.sim.plot_fund_data(ax=None))
        #form_layout.addRow(self.plotfund_button)

        #self.plotinflation_button = QPushButton("Plot inflation")
        #self.plotinflation_button.clicked.connect(lambda: self.sim.plot_inflation_data(ax=None))
        #form_layout.addRow(self.plotinflation_button)

        left_widget = QWidget()
        left_widget.setLayout(form_layout)
        main_layout.addWidget(left_widget, 0)

        self.canvas = FigureCanvas(self.fig)
        main_layout.addWidget(self.canvas, 1)



    def run_simulation(self):
        start_value = self.start_value.value()
        if self.include_loan.isChecked():
            loan_value = self.loan_value.value()
        else:
            loan_value = 0
        loan_rate = self.loan_rate.value() / 100
        isk_rate = self.isk_rate.value() / 100
        monthly_cost = self.monthly_cost.value()
        monthly_salary = self.monthly_salary.value()
        if self.random_start_year.isChecked():
            start_year = np.random.randint(1985, 2016)
            self.start_year.setValue(start_year)
        else:
            start_year = self.start_year.value()
        # Calculate end date based on start year and number of years
        end_year = start_year + self.number_years.value()
        end_date = date(end_year, 1, 1) if end_year <= 2025 else None
        curr_age = self.curr_age.value()
        simulate_inflation = self.simulate_inflation.isChecked()

        monthly_withdrawal = monthly_cost - monthly_salary
        start_date = date(start_year, 1, 1)

        investments = {
            date(1985, 1, 1): 0,
            date(2000, 1, 1): 0,
            date(2001, 1, 1): 0,
        }
        if self.buyhouse_year.value() > 0:
            house_investments = {
                date(start_year + self.buyhouse_year.value(), 1, 1): self.house_cost.value(),
            }
        else:
            house_investments = {}

        sim_data = self.sim.simulate_portfolio(
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

        # Plot the simulation results
        portfolio_value, debt_value, equity_value = sim_data

        # Show metrics in the label
        metrics = self.sim.calculate_performance_metrics(equity_value)
        metrics_text = (
            f"CAGR: {metrics['CAGR']:.2%}\n"
            f"Max Drawdown: {metrics['Max Drawdown']:.2%}\n"
            f"Volatility: {metrics['Volatility']:.2%}\n"
            f"Total Return: {metrics['Tot. return']:.2%}"
        )
        self.metrics_label.setText(metrics_text)

        # Convert to millions
        portfolio_value *= 1e-6
        debt_value *= 1e-6
        equity_value *= 1e-6

        port_val = portfolio_value.to_numpy()
        debt_val = debt_value.to_numpy()
        equity_val = equity_value.to_numpy()
        x_years = curr_age + np.arange(port_val.shape[0])/12

        if not self.hold_plot.isChecked():
            self.ax.clear()
        linestyle = '-' if not self.hold_plot.isChecked() else '--'
        self.ax.plot(x_years, port_val, label="Portfolio value", linestyle=linestyle, color='black')
        self.ax.plot(x_years, debt_val, label="Debt value", linestyle=linestyle, color='red')
        if self.hold_plot.isChecked():
            self.ax.plot(x_years, equity_val, label="Equity value", linestyle=linestyle, color='orange')
        else:
            self.ax.plot(x_years, equity_val, label="Equity value", linestyle=linestyle, color='green')
        self.ax.set_xlabel("Age")
        self.ax.set_ylabel("Balance (MSEK)")
        self.ax.set_title("Liquid Equity")
        self.ax.grid("both")
        self.ax.set_ylim(min(0, equity_val.min()), 1.1 * port_val.max())
        self.ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PortfolioSimulatorGUI()
    gui.show()
    sys.exit(app.exec())