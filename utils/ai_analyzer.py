"""
DataForge - AI Analyzer
========================
LLM-powered data analysis engine. Generates insights,
anomaly detection, summaries, and recommendations from data.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from loguru import logger

from config import OPENAI_API_KEY, AI


class AIAnalyzer:
    """
    AI-powered data analysis using OpenAI GPT models.

    Usage:
        analyzer = AIAnalyzer()
        insights = analyzer.analyze(df, context="Monthly sales data for Q1 2026")
        anomalies = analyzer.detect_anomalies(df)
        summary = analyzer.summarize(df)
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or OPENAI_API_KEY
        self._client = None

        if not self._api_key:
            logger.warning("No OpenAI API key – AI analysis unavailable. Set OPENAI_API_KEY.")
        else:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
                logger.info("AI Analyzer initialized with OpenAI")
            except ImportError:
                logger.error("openai package not installed")

    @property
    def available(self) -> bool:
        return self._client is not None

    # ── Core Analysis ────────────────────────────────────────

    def analyze(
        self,
        df: pd.DataFrame,
        context: str = "",
        focus: str = "general",
    ) -> dict[str, Any]:
        """
        Generate comprehensive AI-powered analysis of data.

        Args:
            df: Input DataFrame
            context: Business context description
            focus: Analysis focus – general | trends | anomalies | recommendations

        Returns:
            Dictionary with structured analysis results
        """
        if not self.available:
            return self._fallback_analysis(df)

        data_summary = self._create_data_summary(df)

        prompt = f"""You are a senior data analyst. Analyze this dataset and provide actionable insights.

## Business Context
{context or 'No specific context provided. Analyze based on the data patterns.'}

## Analysis Focus
{focus}

## Dataset Summary
{data_summary}

## Sample Data (first 10 rows)
{df.head(10).to_markdown(index=False)}

Provide your analysis as valid JSON with these keys:
{{
    "executive_summary": "2-3 sentence high-level summary",
    "key_insights": ["insight 1", "insight 2", ...],
    "data_quality_issues": ["issue 1", ...],
    "trends": ["trend 1", ...],
    "anomalies": ["anomaly 1", ...],
    "recommendations": ["recommendation 1", ...],
    "metrics": {{
        "metric_name": "metric_value"
    }}
}}"""

        try:
            response = self._client.chat.completions.create(
                model=AI.model,
                messages=[
                    {"role": "system", "content": "You are a data analysis expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=AI.max_tokens,
                temperature=AI.temperature,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            logger.info("AI analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(df)

    def detect_anomalies(self, df: pd.DataFrame) -> list[dict]:
        """Detect anomalies in numeric columns using statistical + AI methods."""
        anomalies = []

        # Statistical detection (IQR method)
        numeric_cols = df.select_dtypes(include=["number"]).columns
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outliers = df[(df[col] < lower) | (df[col] > upper)]
            if not outliers.empty:
                anomalies.append({
                    "column": col,
                    "type": "outlier",
                    "count": len(outliers),
                    "threshold": {"lower": round(lower, 2), "upper": round(upper, 2)},
                    "sample_values": outliers[col].head(5).tolist(),
                })

        logger.info(f"Found {len(anomalies)} anomaly groups across {len(numeric_cols)} numeric columns")
        return anomalies

    def summarize(
        self, df: pd.DataFrame, style: str = "executive"
    ) -> str:
        """Generate a human-readable summary of the data."""
        if not self.available:
            return self._fallback_summary(df)

        data_summary = self._create_data_summary(df)

        styles = {
            "executive": "Write a concise executive summary (3-5 sentences) suitable for C-level stakeholders.",
            "technical": "Write a technical data summary with statistics and data quality notes.",
            "client": "Write a client-friendly summary explaining the key findings in simple language.",
        }

        prompt = f"""{styles.get(style, styles['executive'])}

Dataset Summary:
{data_summary}

Sample Data:
{df.head(5).to_markdown(index=False)}"""

        try:
            response = self._client.chat.completions.create(
                model=AI.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            return self._fallback_summary(df)

    def generate_cleaning_rules(self, df: pd.DataFrame) -> dict[str, str]:
        """AI-suggested cleaning rules based on data inspection."""
        if not self.available:
            return {"note": "AI unavailable – using default cleaning rules"}

        data_info = self._create_data_summary(df)
        sample = df.head(10).to_markdown(index=False)

        prompt = f"""Analyze this dataset and suggest data cleaning rules.

Dataset Info:
{data_info}

Sample:
{sample}

Return valid JSON with column names as keys and cleaning actions as values.
Example: {{"date_column": "normalize to YYYY-MM-DD", "phone": "standardize to (XXX) XXX-XXXX"}}"""

        try:
            response = self._client.chat.completions.create(
                model=AI.model,
                messages=[
                    {"role": "system", "content": "Respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Failed to generate cleaning rules: {e}")
            return {}

    # ── Private Helpers ──────────────────────────────────────

    def _create_data_summary(self, df: pd.DataFrame) -> str:
        """Create a concise text summary of DataFrame structure and stats."""
        lines = [
            f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
            f"Columns: {', '.join(df.columns)}",
            f"Dtypes: {dict(df.dtypes.value_counts())}",
            f"Missing values: {int(df.isna().sum().sum())} total",
            "",
            "Column details:",
        ]

        for col in df.columns:
            info = f"  - {col} ({df[col].dtype})"
            if pd.api.types.is_numeric_dtype(df[col]):
                info += f": min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}"
            elif pd.api.types.is_object_dtype(df[col]):
                nunique = df[col].nunique()
                info += f": {nunique} unique values"
                if nunique <= 10:
                    top = df[col].value_counts().head(3).to_dict()
                    info += f", top: {top}"
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                info += f" [{null_count} nulls]"
            lines.append(info)

        return "\n".join(lines)

    def _fallback_analysis(self, df: pd.DataFrame) -> dict[str, Any]:
        """Statistical fallback when AI is unavailable."""
        logger.info("Using statistical fallback analysis (no AI)")
        numeric_stats = {}
        for col in df.select_dtypes(include=["number"]).columns:
            numeric_stats[col] = {
                "mean": round(float(df[col].mean()), 2),
                "median": round(float(df[col].median()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
            }

        return {
            "executive_summary": f"Dataset contains {len(df)} rows and {len(df.columns)} columns.",
            "key_insights": [
                f"{len(df.columns)} columns analyzed",
                f"{int(df.isna().sum().sum())} missing values detected",
                f"{len(df) - len(df.drop_duplicates())} duplicate rows found",
            ],
            "data_quality_issues": [
                f"Column '{col}' has {int(df[col].isna().sum())} missing values"
                for col in df.columns if df[col].isna().sum() > 0
            ],
            "trends": ["AI-powered trend analysis requires OPENAI_API_KEY"],
            "anomalies": [
                f"Potential outliers in '{col}'" for col in df.select_dtypes(include=["number"]).columns
                if df[col].std() > df[col].mean() * 2
            ],
            "recommendations": ["Set OPENAI_API_KEY for deeper AI-powered analysis"],
            "metrics": numeric_stats,
        }

    def _fallback_summary(self, df: pd.DataFrame) -> str:
        """Fallback summary without AI."""
        return (
            f"Dataset: {len(df)} rows × {len(df.columns)} columns. "
            f"Missing values: {int(df.isna().sum().sum())}. "
            f"Numeric columns: {list(df.select_dtypes(include=['number']).columns)}. "
            f"Set OPENAI_API_KEY for AI-powered summaries."
        )
