"""
Test script for DeliveryAnalyzer.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.eda.delivery_analysis import DeliveryAnalyzer


def test_delivery_eda():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        analyzer = DeliveryAnalyzer(session=session)
        report = analyzer.analyze()

        print("Delivery EDA execution complete!")
        print(f"Total Orders Analyzed: {report.total_orders_analyzed:,}")
        print(f"Total Delivered Orders: {report.total_delivered_orders:,}")
        print(f"Average Delivery Days: {report.delivery_time_analysis['average_delivery_days']} days")
        print(f"Median Delivery Days: {report.delivery_time_analysis['median_delivery_days']} days")
        print(f"Delivery SLA Achievement Rate: {report.operational_metrics['delivery_sla_achievement_rate_percent']}%")
        print(f"Percentage of Late Deliveries: {report.delivery_delay_analysis['percentage_of_late_deliveries']}%")
        print(f"Average Processing Time: {report.operational_metrics['average_order_processing_time_days']} days")
        print(f"Average Transit Time: {report.operational_metrics['average_shipping_time_days']} days")
        print(f"Freight vs Delivery Time Correlation: {report.freight_and_logistics['freight_vs_delivery_time_correlation']}")
        print(f"Execution Time: {report.execution_time_sec:.4f}s")


if __name__ == "__main__":
    test_delivery_eda()
