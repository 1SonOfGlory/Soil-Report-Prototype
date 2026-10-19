# src/compendium_loader.py
from __future__ import annotations
import io, os, re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union

Band = Dict[str, Any]
RuleRow = Dict[str, Any]
Compendium = Dict[str, Dict[str, List[RuleRow]]]

# Regex-driven, NOT fixed column names
BAND_LABELS = ["very low", "low", "medium", "high", "very high"]
BAND_REGEXES = [
    (re.compile(r"\bvery\s*low\b", re.I), "Very Low"),
    (re.compile(r"\blow\b", re.I), "Low"),
    (re.compile(r"\bmedium\b", re.I), "Medium"),
    (re.compile(r"\bhigh\b", re.I), "High"),
    (re.compile(r"\bvery\s*high\b", re.I), "Very High"),
]
UNIT_RE = re.compile(r"\bunit(s)?\b", re.I)
CROP_RE = re.compile(r"\bcrop(\s*group)?\b", re.I)
ANALYTE_RE = re.compile(r"\b(analyte|parameter|nutrient|element|name)\b", re.I)
MIN_RE = re.compile(r"\bmin(imum)?\b", re.I)
MAX_RE = re.compile(r"\bmax(imum)?\b", re.I)

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def _match_col(cols: List[str], pattern: re.Pattern) -> Optional[str]:
    for c in cols:
        if pattern.search(c):
            return c
    return None

def _find_role_columns(df: pd.DataFrame) -> Dict[str, str]:
    cols_norm = [_norm(c) for c in df.columns]
    map_norm_to_orig = dict(zip(cols_norm, df.columns))
    analyte = _match_col(cols_norm, ANALYTE_RE)
    unit = _match_col(cols_norm, UNIT_RE)
    crop = _match_col(cols_norm, CROP_RE)

    out = {}
    if analyte: out["analyte"] = map_norm_to_orig[analyte]
    if unit: out["unit"] = map_norm_to_orig[unit]
    if crop: out["crop"] = map_norm_to_orig[crop]
    return out

def _detect_band_columns(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Returns mapping:
    {
      "Very Low": {"max": "Very Low Max Col" or "min": "..."},
      "Low": {"max": "..."},
      ...
    }
    We accept any header containing band label + (min/max) OR single bound columns per band.
    """
    cols_norm = {_norm(c): c for c in df.columns}
    bands: Dict[str, Dict[str, str]] = {}

    for norm, orig in cols_norm.items():
        for rx, band_label in BAND_REGEXES:
            if rx.search(norm):
                b = bands.setdefault(band_label, {})
                if MIN_RE.search(norm):
                    b["min"] = orig
                elif MAX_RE.search(norm):
                    b["max"] = orig
                else:
                    # If the sheet uses a single number per band (e.g., "Low" meaning <= value),
                    # treat it as "max" by default.
                    if "max" not in b and "min" not in b:
                        b["max"] = orig
    return bands

def _coerce_float(x) -> Optional[float]:
    try:
        if pd.isna(x): return None
        return float(x)
    except Exception:
        return None

def _row_to_ranges(row: pd.Series, band_cols: Dict[str, Dict[str, str]]) -> List[Band]:
    ranges: List[Band] = []
    # Preserve a consistent order
    for label in ["Very Low", "Low", "Medium", "High", "Very High"]:
        cols = band_cols.get(label)
        if not cols: 
            continue
        b: Band = {"label": label}
        if "min" in cols:
            val = _coerce_float(row.get(cols["min"]))
            if val is not None: b["min"] = val
        if "max" in cols:
            val = _coerce_float(row.get(cols["max"]))
            if val is not None: b["max"] = val
        if len(b) > 1:
            ranges.append(b)
    return ranges

def _normalize_sheet(df: pd.DataFrame) -> List[RuleRow]:
    roles = _find_role_columns(df)
    band_cols = _detect_band_columns(df)
    out: List[RuleRow] = []

    for _, r in df.iterrows():
        analyte = str(r.get(roles.get("analyte", ""), "")).strip()
        if not analyte:
            continue
        unit = str(r.get(roles.get("unit", ""), "")).strip() or None
        crop = str(r.get(roles.get("crop", ""), "")).strip() or None

        ranges = _row_to_ranges(r, band_cols)
        if not ranges:
            continue

        out.append({
            "analyte": analyte,
            "unit": unit,
            "crop": crop,
            "interpretation": ranges,
        })
    return out

def _load_one_excel(file_or_path: Union[str, bytes, io.BytesIO]) -> Dict[str, List[RuleRow]]:
    xls = pd.ExcelFile(file_or_path)
    data: Dict[str, List[RuleRow]] = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        rows = _normalize_sheet(df)
        if rows:
            data[sheet] = rows
    return data

def combine_compendiums(macro: Dict[str, List[RuleRow]], micro: Dict[str, List[RuleRow]]) -> Compendium:
    return {"macro": macro, "micro": micro}

def load_from_uploaded_files(macro_file, micro_file) -> Compendium:
    # macro_file/micro_file can be Streamlit UploadedFile (has .read()) or a path
    def to_buffer(f):
        if hasattr(f, "read"):
            return io.BytesIO(f.read())
        return f  # assume path
    macro = _load_one_excel(to_buffer(macro_file))
    micro = _load_one_excel(to_buffer(micro_file))
    return combine_compendiums(macro, micro)
