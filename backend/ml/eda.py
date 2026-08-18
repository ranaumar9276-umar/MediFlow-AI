"""
Exploratory Data Analysis (EDA) foundation for MediFlow AI (Phase 1).

Uses Matplotlib/Seaborn directly on real appointment data to generate
genuine exploratory visualizations (distribution + correlation heatmap),
returned as base64-encoded PNGs so the existing FastAPI/React architecture
can display them without adding a new rendering stack. Interactive,
day-to-day dashboard charts continue to use Recharts on the frontend (as
required) - this module is specifically the Python-side data-science EDA
layer.
"""
from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # headless rendering - required in a server environment
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#17181d", "figure.facecolor": "#17181d"})

_ACCENT = "#c8963e"
_TEXT_COLOR = "#f1efe9"


def _fig_to_base64(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _style_axes(ax):
    ax.tick_params(colors=_TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(_TEXT_COLOR)
    ax.yaxis.label.set_color(_TEXT_COLOR)
    ax.title.set_color(_TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_color("#2c2e36")


def duration_distribution_chart(df: pd.DataFrame) -> str | None:
    """Histogram of appointment duration - a classic EDA distribution plot."""
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(6, 3.6))
    sns.histplot(df["duration_minutes"], bins=15, color=_ACCENT, ax=ax, kde=True)
    ax.set_title("Appointment Duration Distribution")
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Count")
    _style_axes(ax)
    return _fig_to_base64(fig)


def weekday_hour_heatmap(df: pd.DataFrame) -> str | None:
    """Heatmap of appointment volume by weekday x hour-of-day - reveals peak
    operational periods at a glance."""
    if df.empty:
        return None
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = (
        df.groupby(["weekday", "hour_of_day"]).size().unstack(fill_value=0).reindex(order)
    )
    if pivot.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 3.6))
    sns.heatmap(pivot, cmap="YlOrBr", ax=ax, cbar_kws={"label": "Appointments"})
    ax.set_title("Appointment Volume: Weekday x Hour")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("")
    _style_axes(ax)
    return _fig_to_base64(fig)


def department_status_chart(df: pd.DataFrame) -> str | None:
    """Grouped bar chart: appointment status breakdown per department."""
    if df.empty:
        return None
    pivot = df.groupby(["department", "status"], observed=True).size().unstack(fill_value=0)
    if pivot.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 3.8))
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="copper")
    ax.set_title("Appointment Status by Department")
    ax.set_xlabel("")
    ax.set_ylabel("Count")
    ax.legend(fontsize=8, facecolor="#17181d", labelcolor=_TEXT_COLOR)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    _style_axes(ax)
    return _fig_to_base64(fig)


def build_eda_charts(df: pd.DataFrame) -> dict:
    """Returns a dict of chart_name -> base64 PNG (or None if not enough data)."""
    return {
        "duration_distribution": duration_distribution_chart(df),
        "weekday_hour_heatmap": weekday_hour_heatmap(df),
        "department_status_breakdown": department_status_chart(df),
    }
