"""
Reusable data visualization helper functions for analytical reports and plots.
"""

from typing import List, Optional, Tuple
from loguru import logger
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class AnalyticsVisualizer:
    """
    Visualization helper providing reusable plotting utilities for EDA and analytics.
    """

    @staticmethod
    def set_theme() -> None:
        """
        Apply standard seaborn/matplotlib design theme.
        """
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["figure.dpi"] = 120

    @staticmethod
    def plot_distribution(
        df: pd.DataFrame,
        column: str,
        bins: int = 30,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (8, 4),
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot histogram and KDE distribution curve for a numeric column.
        """
        AnalyticsVisualizer.set_theme()
        fig, ax = plt.subplots(figsize=figsize)
        sns.histplot(df[column].dropna(), bins=bins, kde=True, ax=ax, color="#2b5c8f")
        ax.set_title(title or f"Distribution of {column}", fontsize=12, fontweight="bold")
        ax.set_xlabel(column)
        ax.set_ylabel("Frequency")
        plt.tight_layout()
        return fig, ax

    @staticmethod
    def plot_categorical_count(
        df: pd.DataFrame,
        column: str,
        top_n: int = 10,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (8, 4),
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot bar chart for top N frequent categories in a column.
        """
        AnalyticsVisualizer.set_theme()
        fig, ax = plt.subplots(figsize=figsize)
        top_series = df[column].value_counts().head(top_n)
        sns.barplot(x=top_series.values, y=top_series.index, ax=ax, palette="Blues_r")
        ax.set_title(title or f"Top {top_n} Categories in {column}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Count")
        ax.set_ylabel(column)
        plt.tight_layout()
        return fig, ax

    @staticmethod
    def plot_correlation_heatmap(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        figsize: Tuple[int, int] = (8, 6),
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot correlation heatmap across numeric columns.
        """
        AnalyticsVisualizer.set_theme()
        target_df = df[columns] if columns else df.select_dtypes(include=["number"])
        corr = target_df.corr()

        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax, square=True)
        ax.set_title("Correlation Matrix", fontsize=12, fontweight="bold")
        plt.tight_layout()
        return fig, ax

    @staticmethod
    def plot_time_series(
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        freq: str = "D",
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 4),
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot aggregated line chart over time for a numeric metric.
        """
        AnalyticsVisualizer.set_theme()
        ts_df = df.copy()
        ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors="coerce")
        resampled = ts_df.set_index(date_col).resample(freq)[value_col].sum()

        fig, ax = plt.subplots(figsize=figsize)
        resampled.plot(ax=ax, color="#1f77b4", linewidth=2)
        ax.set_title(title or f"{value_col} over Time ({freq})", fontsize=12, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel(value_col)
        plt.tight_layout()
        return fig, ax
