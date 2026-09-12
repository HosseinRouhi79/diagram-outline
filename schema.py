"""
Pydantic models that define the structured chart JSON output.

The schema is intentionally flexible — it uses dynamic key/value data points
so it works with ANY kind of text (user signups, revenue, survey results,
temperature readings, etc.) without needing per-topic models.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DataPoint(BaseModel):
    label: str = Field(
        description="The category, name, time, or independent variable (x-axis label)."
    )
    value: float = Field(
        description="The numeric value for the data point (y-axis value)."
    )


class ChartPayload(BaseModel):
    """
    A chart-ready JSON payload extracted from plain text.

    This is the top-level output schema that Outlines enforces.
    The LLM *must* produce valid JSON matching this structure.
    """

    chart_type: Literal[
        "bar",
        "time_series",
        "pie",
        "line",
        "scatter",
        "histogram",
        "area",
        "table",
    ] = Field(
        description=(
            "The most appropriate chart type for visualising the data. "
            "When in doubt, use 'bar'. "
            "Pick 'bar' for categorical comparisons, 'time_series' or 'line' for data ordered over time, "
            "'pie' for proportions. Use 'scatter' ONLY for numerical correlations where both X and Y are numbers."
        )
    )

    title: str = Field(
        description="A short, descriptive title for the chart."
    )

    xAxis: str = Field(
        description=(
            "The semantic label for the x-axis / independent variable "
            "(e.g. 'month', 'country', 'product')."
        )
    )

    yAxis: str = Field(
        description=(
            "The semantic label for the y-axis / dependent variable "
            "(e.g. 'signups', 'revenue_usd', 'temperature_c')."
        )
    )

    data: list[DataPoint] = Field(
        description="A list of data points to be charted."
    )


    
