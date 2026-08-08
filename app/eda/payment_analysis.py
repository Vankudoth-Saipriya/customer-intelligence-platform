"""
Payment Exploratory Data Analysis (EDA) module.

Performs payment method distribution profiling, installment structure analysis,
payment value statistical modeling, payment behavior tracking, and business metrics computation.
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.analytics.data_profiler import DataProfiler
from app.eda.report import PaymentAnalysisReport


class PaymentAnalyzer:
    """
    Analyzer executing comprehensive Payment EDA and generating structured reports.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize PaymentAnalyzer with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)
        self.profiler = DataProfiler()

    def analyze(self) -> PaymentAnalysisReport:
        """
        Execute full payment exploratory data analysis.

        Returns:
            PaymentAnalysisReport containing analytical statistics.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Payment Exploratory Data Analysis (EDA)...")

        # Load domain datasets via AnalyticsDataLoader
        payments_df = self.data_loader.load_payments()
        orders_df = self.data_loader.load_orders()
        customers_df = self.data_loader.load_customers()

        total_payments = len(payments_df)
        logger.info(f"Loaded {total_payments:,} payment records for EDA.")

        # Total revenue across all payment transactions
        total_payment_val = round(float(payments_df["payment_value"].sum()), 2)

        # ---------------------------------------------------------------------
        # 1. Payment Method Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing payment method distribution, revenue, and averages...")

        pm_dist = payments_df["payment_type"].value_counts().to_dict()

        pm_rev_series = payments_df.groupby("payment_type")["payment_value"].sum().round(2)
        pm_revenue = pm_rev_series.to_dict()

        pm_orders_series = payments_df.groupby("payment_type")["order_id"].nunique()
        pm_order_counts = pm_orders_series.to_dict()

        pm_avg_val_series = payments_df.groupby("payment_type")["payment_value"].mean().round(2)
        pm_avg_value = pm_avg_val_series.to_dict()

        payment_method_analysis = {
            "payment_method_distribution": pm_dist,
            "revenue_by_payment_method": pm_revenue,
            "order_count_by_payment_method": pm_order_counts,
            "average_payment_value_by_payment_method": pm_avg_value,
        }

        # ---------------------------------------------------------------------
        # 2. Installment Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing installment distributions, revenue, and options...")

        inst_counts_series = payments_df["payment_installments"].value_counts().sort_index()
        installment_distribution = {str(int(k)): int(v) for k, v in inst_counts_series.items()}

        avg_installments = round(float(payments_df["payment_installments"].mean()), 2)

        # Credit card specific installment average
        cc_payments = payments_df[payments_df["payment_type"] == "credit_card"]
        avg_cc_installments = round(float(cc_payments["payment_installments"].mean()), 2) if len(cc_payments) > 0 else 0.0

        rev_by_installment_series = (
            payments_df.groupby("payment_installments")["payment_value"].sum().round(2).sort_index()
        )
        revenue_by_installment = {str(int(k)): float(v) for k, v in rev_by_installment_series.items()}

        # Installment (>1) vs One-time (1) payments comparison
        one_time_mask = payments_df["payment_installments"] == 1
        installment_mask = payments_df["payment_installments"] > 1

        one_time_cnt = int(one_time_mask.sum())
        installment_cnt = int(installment_mask.sum())

        one_time_rev = round(float(payments_df.loc[one_time_mask, "payment_value"].sum()), 2)
        installment_rev = round(float(payments_df.loc[installment_mask, "payment_value"].sum()), 2)

        one_time_tx_pct = round((one_time_cnt / total_payments * 100.0), 2) if total_payments > 0 else 0.0
        installment_tx_pct = round((installment_cnt / total_payments * 100.0), 2) if total_payments > 0 else 0.0

        one_time_rev_pct = round((one_time_rev / total_payment_val * 100.0), 2) if total_payment_val > 0 else 0.0
        installment_rev_pct = round((installment_rev / total_payment_val * 100.0), 2) if total_payment_val > 0 else 0.0

        installment_vs_onetime = {
            "one_time_payments": {
                "transaction_count": one_time_cnt,
                "transaction_percentage": one_time_tx_pct,
                "revenue": one_time_rev,
                "revenue_percentage": one_time_rev_pct,
            },
            "installment_payments": {
                "transaction_count": installment_cnt,
                "transaction_percentage": installment_tx_pct,
                "revenue": installment_rev,
                "revenue_percentage": installment_rev_pct,
            },
        }

        installment_analysis = {
            "installment_count_distribution": installment_distribution,
            "average_installment_count_overall": avg_installments,
            "average_installment_count_credit_card": avg_cc_installments,
            "revenue_by_installment_count": revenue_by_installment,
            "percentage_of_installment_vs_one_time_payments": installment_vs_onetime,
        }

        # ---------------------------------------------------------------------
        # 3. Payment Value Analysis
        # ---------------------------------------------------------------------
        logger.info("Evaluating payment value summary statistics and IQR outliers...")

        val_series = payments_df["payment_value"].dropna()

        mean_val = round(float(val_series.mean()), 2)
        median_val = round(float(val_series.median()), 2)
        min_val = round(float(val_series.min()), 2)
        max_val = round(float(val_series.max()), 2)

        q25_val = round(float(val_series.quantile(0.25)), 2)
        q50_val = median_val
        q75_val = round(float(val_series.quantile(0.75)), 2)

        # IQR Outlier Detection
        iqr = q75_val - q25_val
        lower_bound = round(q25_val - 1.5 * iqr, 2)
        upper_bound = round(q75_val + 1.5 * iqr, 2)

        outlier_mask = (val_series < lower_bound) | (val_series > upper_bound)
        outlier_count = int(outlier_mask.sum())
        outlier_pct = round((outlier_count / len(val_series) * 100.0), 2) if len(val_series) > 0 else 0.0

        payment_value_analysis = {
            "total_payment_value": total_payment_val,
            "average_payment_value": mean_val,
            "median_payment_value": median_val,
            "min_payment_value": min_val,
            "max_payment_value": max_val,
            "quartiles": {
                "q25": q25_val,
                "q50_median": q50_val,
                "q75": q75_val,
            },
            "outlier_detection_iqr": {
                "outlier_count": outlier_count,
                "outlier_percentage": outlier_pct,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            },
        }

        # ---------------------------------------------------------------------
        # 4. Payment Behavior
        # ---------------------------------------------------------------------
        logger.info("Analyzing payment behavior, multi-payment orders, vouchers, and trends...")

        # Orders with multiple payments
        order_pay_counts = payments_df.groupby("order_id")["payment_sequential"].count()
        total_unique_orders_in_pmts = len(order_pay_counts)

        multi_pay_orders_cnt = int((order_pay_counts > 1).sum())
        multi_pay_orders_pct = (
            round((multi_pay_orders_cnt / total_unique_orders_in_pmts * 100.0), 2)
            if total_unique_orders_in_pmts > 0
            else 0.0
        )
        pay_seq_histogram = {str(int(k)): int(v) for k, v in order_pay_counts.value_counts().sort_index().items()}

        # Voucher Usage
        voucher_pmts = payments_df[payments_df["payment_type"] == "voucher"]
        voucher_count = len(voucher_pmts)
        voucher_revenue = round(float(voucher_pmts["payment_value"].sum()), 2)
        voucher_orders_cnt = int(voucher_pmts["order_id"].nunique())
        voucher_order_pct = (
            round((voucher_orders_cnt / total_unique_orders_in_pmts * 100.0), 2)
            if total_unique_orders_in_pmts > 0
            else 0.0
        )
        avg_voucher_val = round(float(voucher_pmts["payment_value"].mean()), 2) if voucher_count > 0 else 0.0

        voucher_usage = {
            "voucher_transaction_count": voucher_count,
            "voucher_total_revenue": voucher_revenue,
            "voucher_orders_count": voucher_orders_cnt,
            "voucher_orders_percentage": voucher_order_pct,
            "average_voucher_value": avg_voucher_val,
        }

        # Credit Card Dominance
        cc_count = pm_dist.get("credit_card", 0)
        cc_rev = pm_revenue.get("credit_card", 0.0)
        cc_tx_pct = round((cc_count / total_payments * 100.0), 2) if total_payments > 0 else 0.0
        cc_rev_pct = round((cc_rev / total_payment_val * 100.0), 2) if total_payment_val > 0 else 0.0

        credit_card_dominance = {
            "credit_card_transaction_count": cc_count,
            "credit_card_revenue": cc_rev,
            "credit_card_transaction_share_percent": cc_tx_pct,
            "credit_card_revenue_share_percent": cc_rev_pct,
        }

        # Payment Type Trends Over Time
        orders_df["purchase_dt"] = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce", utc=True)
        orders_df["year_month"] = orders_df["purchase_dt"].dt.tz_localize(None).dt.to_period("M").astype(str)

        merged_pmts = payments_df.merge(orders_df[["order_id", "year_month"]], on="order_id", how="left")
        merged_pmts = merged_pmts.dropna(subset=["year_month"])

        pmt_trends_df = merged_pmts.groupby(["year_month", "payment_type"])["payment_value"].sum().unstack(fill_value=0.0).round(2)
        payment_type_trends_over_time = pmt_trends_df.to_dict(orient="index")

        payment_behavior = {
            "multiple_payment_methods_per_order": {
                "orders_with_multiple_payments": multi_pay_orders_cnt,
                "percentage_of_total_orders": multi_pay_orders_pct,
                "payment_count_per_order_histogram": pay_seq_histogram,
            },
            "voucher_usage": voucher_usage,
            "credit_card_dominance": credit_card_dominance,
            "payment_type_trends_over_time": payment_type_trends_over_time,
        }

        # ---------------------------------------------------------------------
        # 5. Business Metrics
        # ---------------------------------------------------------------------
        logger.info("Computing business metrics (contributions, per-customer, per-order)...")

        pm_contrib_pct = {
            k: round((v / total_payment_val * 100.0), 2) if total_payment_val > 0 else 0.0
            for k, v in pm_revenue.items()
        }

        total_unique_custs = int(customers_df["customer_unique_id"].nunique())
        total_unique_orders = int(orders_df["order_id"].nunique())

        avg_pmt_per_customer = round((total_payment_val / total_unique_custs), 2) if total_unique_custs > 0 else 0.0
        avg_pmt_per_order = round((total_payment_val / total_unique_orders), 2) if total_unique_orders > 0 else 0.0

        business_metrics = {
            "payment_method_contribution_percent": pm_contrib_pct,
            "installment_revenue_contribution_percent": installment_rev_pct,
            "average_payment_per_customer": avg_pmt_per_customer,
            "average_payment_per_order": avg_pmt_per_order,
            "total_unique_customers_count": total_unique_custs,
            "total_unique_orders_count": total_unique_orders,
        }

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Payment EDA in {elapsed_sec:.4f}s.")

        report = PaymentAnalysisReport(
            total_payments_analyzed=total_payments,
            payment_method_analysis=payment_method_analysis,
            installment_analysis=installment_analysis,
            payment_value_analysis=payment_value_analysis,
            payment_behavior=payment_behavior,
            business_metrics=business_metrics,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save JSON artifact to artifacts/eda/payment_analysis.json
        report.save_json()

        return report
