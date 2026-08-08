"""
Test script for SalesAnalyzer.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.eda.sales_analysis import SalesAnalyzer


def test_sales_eda():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        analyzer = SalesAnalyzer(session=session)
        report = analyzer.analyze()

        print("Sales EDA execution complete!")
        print(f"Total Orders Analyzed: {report.total_orders_analyzed:,}")
        print(f"Total Overall Revenue: ${report.revenue_analysis['total_revenue']:,.2f}")
        print(f"Average Order Value: ${report.order_analysis['average_order_value']:,.2f}")
        print(f"Top Spike Days Detected: {len(report.seasonality['holiday_spike_detection']['top_revenue_spike_days'])}")
        print(f"Top 20% Product Revenue Share: {report.sales_performance['revenue_concentration']['top_20_percent_products_revenue_share']}%")
        print(f"Freight Percentage of Revenue: {report.operational_metrics['freight_percentage_of_total_revenue']}%")
        print(f"Execution Time: {report.execution_time_sec:.4f}s")


if __name__ == "__main__":
    test_sales_eda()
