"""
Test script for PaymentAnalyzer.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.eda.payment_analysis import PaymentAnalyzer


def test_payment_eda():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        analyzer = PaymentAnalyzer(session=session)
        report = analyzer.analyze()

        print("Payment EDA execution complete!")
        print(f"Total Payments Analyzed: {report.total_payments_analyzed:,}")
        print(f"Total Payment Value: ${report.payment_value_analysis['total_payment_value']:,.2f}")
        print(f"Average Payment Value: ${report.payment_value_analysis['average_payment_value']:,.2f}")
        print(f"Credit Card Share: {report.payment_behavior['credit_card_dominance']['credit_card_revenue_share_percent']}%")
        print(f"Installment Revenue Share: {report.business_metrics['installment_revenue_contribution_percent']}%")
        print(f"Average Payment per Customer: ${report.business_metrics['average_payment_per_customer']:,.2f}")
        print(f"Execution Time: {report.execution_time_sec:.4f}s")


if __name__ == "__main__":
    test_payment_eda()
