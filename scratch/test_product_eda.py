"""
Test script for ProductAnalyzer.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.eda.product_analysis import ProductAnalyzer


def test_product_eda():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        analyzer = ProductAnalyzer(session=session)
        report = analyzer.analyze()

        print("Product EDA execution complete!")
        print(f"Total Products Analyzed: {report.total_products_analyzed:,}")
        print(f"Top 20 Categories Count: {len(report.category_analysis['top_20_categories'])}")
        print(f"Categories with English Translation: {report.translation_coverage['categories_with_english_translation']}")
        print(f"Translation Coverage %: {report.translation_coverage['category_translation_coverage_percent']}%")
        print(f"Freight vs Weight Correlation: {report.freight_analysis['freight_vs_product_weight_correlation']}")
        print(f"Freight vs Volume Correlation: {report.freight_analysis['freight_vs_product_volume_correlation']}")
        print(f"Execution Time: {report.execution_time_sec:.4f}s")


if __name__ == "__main__":
    test_product_eda()
