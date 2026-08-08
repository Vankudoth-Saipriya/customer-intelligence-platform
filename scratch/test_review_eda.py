"""
Test script for ReviewAnalyzer.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.eda.review_analysis import ReviewAnalyzer


def test_review_eda():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        analyzer = ReviewAnalyzer(session=session)
        report = analyzer.analyze()

        print("Review EDA execution complete!")
        print(f"Total Reviews Analyzed: {report.total_reviews_analyzed:,}")
        print(f"Average Review Score: {report.review_score_analysis['average_review_score']}")
        print(f"Positive Review %: {report.operational_metrics['positive_review_percentage']}%")
        print(f"Review Coverage %: {report.operational_metrics['review_coverage_percentage']}%")
        print(f"Review Score vs Delay Correlation: {report.business_insights['review_score_vs_delivery_delay_correlation']}")
        print(f"Execution Time: {report.execution_time_sec:.4f}s")


if __name__ == "__main__":
    test_review_eda()
