"""
Test script for CustomerAnalyzer.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.base import Base
from app.eda.customer_analysis import CustomerAnalyzer
from app.etl.pipeline import ETLPipeline

def test_customer_eda():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    
    with Session(engine) as session:
        analyzer = CustomerAnalyzer(session=session)
        report = analyzer.analyze()
        
        print("Customer EDA execution complete!")
        print(f"Total Customers Analyzed: {report.total_customers_analyzed:,}")
        print(f"Unique Customers: {report.repeat_analysis['total_unique_customers']:,}")
        print(f"Repeat Customers: {report.repeat_analysis['repeat_customers']:,} ({report.repeat_analysis['repeat_purchase_rate_percent']}%)")
        print(f"Total Spent: ${report.spending_overview['total_spent_overall']:,.2f}")
        print(f"Average Spending per Customer: ${report.spending_overview['average_spending_per_customer']:,.2f}")

if __name__ == "__main__":
    test_customer_eda()
