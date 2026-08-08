"""
AI Business Analyst Report Generator.

Orchestrates sample report creation and exports sample artifacts to artifacts/ai/.
"""

from pathlib import Path
from typing import Optional
from app.ai.analyst import BusinessAnalyst

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "ai"


class ReportGenerator:
    """Orchestrates report generation and artifact saving."""

    def __init__(self, analyst: Optional[BusinessAnalyst] = None):
        self.analyst = analyst or BusinessAnalyst()

    def generate_all_sample_reports(self) -> None:
        """Generate and save sample_business_report.md and sample_executive_summary.md."""
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

        exec_summary = self.analyst.generate_executive_summary()
        exec_path = ARTIFACTS_DIR / "sample_executive_summary.md"
        with open(exec_path, "w", encoding="utf-8") as f:
            f.write(exec_summary)

        biz_report = self.analyst.generate_weekly_business_report()
        biz_path = ARTIFACTS_DIR / "sample_business_report.md"
        with open(biz_path, "w", encoding="utf-8") as f:
            f.write(biz_report)

        print(f"Generated sample executive summary -> {exec_path}")
        print(f"Generated sample business report -> {biz_path}")


if __name__ == "__main__":
    rg = ReportGenerator()
    rg.generate_all_sample_reports()
