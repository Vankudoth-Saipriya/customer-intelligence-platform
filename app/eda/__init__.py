"""
Exploratory Data Analysis (EDA) Package.

Provides customer, order, product, payment, and review analytical profiling engines.
"""

from app.eda.customer_analysis import CustomerAnalyzer
from app.eda.report import CustomerAnalysisReport

__all__ = [
    "CustomerAnalyzer",
    "CustomerAnalysisReport",
]
