# src/rules_engine.py
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List

def _match_rule(compendium, analyte: str, crop: Optional[str]) -> Optional[Dict[str, Any]]:
    analyte_lc = analyte.strip().lower()
    def search(section):
        for sheet, rows in section.items():
            # crop-specific first
            if crop:
                for r in rows:
                    if r["analyte"].lower() == analyte_lc and r.get("crop") and r["crop"].lower() == crop.lower():
                        return r
            # generic
            for r in rows:
                if r["analyte"].lower() == analyte_lc and not r.get("crop"):
                    return r
        return None

    return search(compendium.get("macro", {})) or search(compendium.get("micro", {}))

def classify_value(compendium, analyte: str, value: float, crop: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    rule = _match_rule(compendium, analyte, crop)
    if not rule: 
        return ("Not in compendium", {})

    for band in rule["interpretation"]:
        min_ok = ("min" not in band) or (value > float(band["min"]))
        max_ok = ("max" not in band) or (value <= float(band["max"]))
        if min_ok and max_ok:
            return (band["label"], rule)

    return ("Unknown", rule)

def interpret_sample(sample: Dict[str, Any], crop: Optional[str], compendium) -> Dict[str, Any]:
    result = {"raw": sample, "classified": {}}
    for k, v in sample.items():
        if isinstance(v, (int, float)):
            band, rule = classify_value(compendium, k, float(v), crop)
            result["classified"][k] = {
                "value": v,
                "band": band,
                "unit": rule.get("unit"),
                "ranges": rule.get("interpretation", []),
                "source": "Uploaded Compendium",
            }
    return result
