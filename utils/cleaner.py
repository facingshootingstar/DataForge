"""
DataForge - Data Cleaner
=========================
Intelligent data cleaning & transformation engine.
Handles messy Excel/CSV data: duplicates, inconsistent formats,
missing values, phone numbers, emails, currencies, dates.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from loguru import logger

from config import CLEANING


class DataCleaner:
    """
    Production-grade data cleaning pipeline.

    Usage:
        cleaner = DataCleaner(df)
        clean_df = (
            cleaner
            .strip_whitespace()
            .remove_duplicates()
            .normalize_dates(columns=["order_date"])
            .normalize_currency(columns=["amount"])
            .standardize_phone(columns=["phone"])
            .validate_emails(columns=["email"])
            .fill_missing()
            .get()
        )
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._original = df.copy()
        self._df = df.copy()
        self._log: list[str] = []
        logger.info(f"DataCleaner initialized with {len(df)} rows, {len(df.columns)} columns")

    # ── Chainable API ────────────────────────────────────────

    def strip_whitespace(self) -> DataCleaner:
        """Remove leading/trailing whitespace from all string columns."""
        str_cols = self._df.select_dtypes(include=["object"]).columns
        for col in str_cols:
            self._df[col] = self._df[col].astype(str).str.strip()
            # Replace 'nan' strings back to NaN
            self._df[col] = self._df[col].replace("nan", pd.NA)
        self._log.append(f"Stripped whitespace from {len(str_cols)} columns")
        logger.debug(f"Stripped whitespace from columns: {list(str_cols)}")
        return self

    def remove_duplicates(
        self, subset: list[str] | None = None, keep: str = "first"
    ) -> DataCleaner:
        """Remove duplicate rows."""
        before = len(self._df)
        self._df = self._df.drop_duplicates(subset=subset, keep=keep)
        removed = before - len(self._df)
        self._log.append(f"Removed {removed} duplicate rows")
        logger.info(f"Removed {removed} duplicates ({before} → {len(self._df)} rows)")
        return self

    def normalize_dates(
        self,
        columns: list[str] | None = None,
        output_format: str | None = None,
    ) -> DataCleaner:
        """Parse messy date strings into a consistent format."""
        fmt = output_format or CLEANING.date_format
        target_cols = columns or self._detect_date_columns()

        for col in target_cols:
            if col not in self._df.columns:
                logger.warning(f"Date column '{col}' not found – skipping")
                continue
            try:
                self._df[col] = pd.to_datetime(
                    self._df[col], infer_datetime_format=True, errors="coerce"
                ).dt.strftime(fmt)
                self._log.append(f"Normalized dates in '{col}' → {fmt}")
            except Exception as e:
                logger.error(f"Failed to normalize dates in '{col}': {e}")

        return self

    def normalize_currency(
        self, columns: list[str] | None = None
    ) -> DataCleaner:
        """Strip currency symbols and convert to float."""
        target_cols = columns or self._detect_currency_columns()

        for col in target_cols:
            if col not in self._df.columns:
                continue
            self._df[col] = (
                self._df[col]
                .astype(str)
                .str.replace(r"[^\d.\-]", "", regex=True)
            )
            self._df[col] = pd.to_numeric(self._df[col], errors="coerce")
            self._log.append(f"Normalized currency in '{col}'")

        return self

    def standardize_phone(
        self, columns: list[str] | None = None
    ) -> DataCleaner:
        """Standardize phone numbers to a consistent format."""
        target_cols = columns or self._detect_phone_columns()

        for col in target_cols:
            if col not in self._df.columns:
                continue
            self._df[col] = self._df[col].apply(self._clean_phone)
            self._log.append(f"Standardized phone numbers in '{col}'")

        return self

    def validate_emails(
        self, columns: list[str] | None = None, fix: bool = True
    ) -> DataCleaner:
        """Validate and optionally fix email addresses."""
        target_cols = columns or self._detect_email_columns()
        email_re = re.compile(
            r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        )

        for col in target_cols:
            if col not in self._df.columns:
                continue
            mask = self._df[col].notna()
            if fix:
                self._df.loc[mask, col] = (
                    self._df.loc[mask, col]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .str.replace(r"\s+", "", regex=True)
                )
            invalid = self._df.loc[mask, col].apply(
                lambda x: not bool(email_re.match(str(x)))
            )
            invalid_count = invalid.sum()
            self._df.loc[mask & invalid, col] = pd.NA
            self._log.append(
                f"Validated emails in '{col}': {invalid_count} invalid → set to NA"
            )

        return self

    def normalize_case(
        self, columns: list[str] | None = None, case: str | None = None
    ) -> DataCleaner:
        """Normalize string case: lower, upper, or title."""
        mode = case or CLEANING.case_normalization
        if mode == "none":
            return self
        target_cols = columns or self._df.select_dtypes(include=["object"]).columns.tolist()

        for col in target_cols:
            if col not in self._df.columns:
                continue
            if mode == "lower":
                self._df[col] = self._df[col].astype(str).str.lower()
            elif mode == "upper":
                self._df[col] = self._df[col].astype(str).str.upper()
            elif mode == "title":
                self._df[col] = self._df[col].astype(str).str.title()
            self._df[col] = self._df[col].replace("nan", pd.NA)

        self._log.append(f"Normalized case to '{mode}' for {len(target_cols)} columns")
        return self

    def fill_missing(
        self, strategy: str | None = None, value: Any = None
    ) -> DataCleaner:
        """Fill missing values with the chosen strategy."""
        strat = strategy or CLEANING.fill_missing_strategy
        fill_val = value if value is not None else CLEANING.fill_value
        missing_before = int(self._df.isna().sum().sum())

        if strat == "drop":
            self._df = self._df.dropna()
        elif strat == "ffill":
            self._df = self._df.ffill()
        elif strat == "bfill":
            self._df = self._df.bfill()
        elif strat == "value":
            self._df = self._df.fillna(fill_val or "")
        elif strat == "smart":
            # Numeric → median, String → mode, Date → forward-fill
            for col in self._df.columns:
                if self._df[col].isna().sum() == 0:
                    continue
                if pd.api.types.is_numeric_dtype(self._df[col]):
                    self._df[col] = self._df[col].fillna(self._df[col].median())
                elif pd.api.types.is_datetime64_any_dtype(self._df[col]):
                    self._df[col] = self._df[col].ffill()
                else:
                    mode = self._df[col].mode()
                    if not mode.empty:
                        self._df[col] = self._df[col].fillna(mode.iloc[0])
        else:
            logger.warning(f"Unknown fill strategy: {strat}")

        missing_after = int(self._df.isna().sum().sum())
        self._log.append(f"Filled missing: {missing_before} → {missing_after} NaN values (strategy={strat})")
        return self

    def apply_custom_rules(self, rules: dict[str, callable]) -> DataCleaner:
        """
        Apply custom transformation rules.

        Args:
            rules: dict mapping column names to transformation functions.
                   e.g. {"price": lambda x: round(x, 2)}
        """
        for col, func in rules.items():
            if col in self._df.columns:
                self._df[col] = self._df[col].apply(func)
                self._log.append(f"Applied custom rule to '{col}'")
        return self

    def rename_columns(self, mapping: dict[str, str] | None = None) -> DataCleaner:
        """Rename columns. If no mapping, auto-clean column names."""
        if mapping:
            self._df = self._df.rename(columns=mapping)
        else:
            # Auto-clean: lowercase, replace spaces with underscores
            self._df.columns = [
                re.sub(r"[^\w]", "_", col.strip().lower()).strip("_")
                for col in self._df.columns
            ]
        self._log.append("Renamed/cleaned column names")
        return self

    # ── Output ───────────────────────────────────────────────

    def get(self) -> pd.DataFrame:
        """Return the cleaned DataFrame."""
        return self._df.copy()

    def get_report(self) -> dict:
        """Return a summary report of all cleaning operations."""
        return {
            "original_shape": self._original.shape,
            "cleaned_shape": self._df.shape,
            "rows_removed": self._original.shape[0] - self._df.shape[0],
            "operations": self._log.copy(),
            "remaining_nulls": int(self._df.isna().sum().sum()),
            "columns": list(self._df.columns),
        }

    # ── Auto-detection helpers ───────────────────────────────

    def _detect_date_columns(self) -> list[str]:
        """Heuristically detect columns that look like dates."""
        candidates = []
        for col in self._df.select_dtypes(include=["object"]).columns:
            sample = self._df[col].dropna().head(20)
            date_like = sample.apply(self._looks_like_date)
            if date_like.mean() > 0.6:
                candidates.append(col)
        return candidates

    def _detect_currency_columns(self) -> list[str]:
        currency_re = re.compile(r"^\s*[\$€£¥₹]?\s*[\d,]+\.?\d*\s*$")
        candidates = []
        for col in self._df.select_dtypes(include=["object"]).columns:
            sample = self._df[col].dropna().astype(str).head(20)
            if sample.str.contains(r"[\$€£¥₹]", regex=True).mean() > 0.3:
                candidates.append(col)
        return candidates

    def _detect_phone_columns(self) -> list[str]:
        phone_re = re.compile(r"[\d\-\(\)\+\s]{7,}")
        candidates = []
        for col in self._df.select_dtypes(include=["object"]).columns:
            if any(kw in col.lower() for kw in ("phone", "tel", "mobile", "cell", "fax")):
                candidates.append(col)
        return candidates

    def _detect_email_columns(self) -> list[str]:
        candidates = []
        for col in self._df.select_dtypes(include=["object"]).columns:
            if "email" in col.lower() or "e_mail" in col.lower():
                candidates.append(col)
                continue
            sample = self._df[col].dropna().astype(str).head(20)
            if sample.str.contains("@").mean() > 0.5:
                candidates.append(col)
        return candidates

    @staticmethod
    def _looks_like_date(val: Any) -> bool:
        try:
            pd.to_datetime(str(val))
            return True
        except Exception:
            return False

    @staticmethod
    def _clean_phone(val: Any) -> str | None:
        if pd.isna(val):
            return None
        digits = re.sub(r"\D", "", str(val))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif len(digits) >= 7:
            return digits
        return str(val)
