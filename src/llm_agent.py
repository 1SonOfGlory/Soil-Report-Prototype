# src/llm_agent.py
"""
LLM Agent for SOL Research Centre Reports (Groq version only).
This module uses Groq’s hosted models (default: llama-3.1-8b-instant)
to generate structured, Ghana-context agronomy narratives for the report.
"""

from __future__ import annotations
import os, json
from typing import Dict, Any
from groq import Groq

# -----------------------
# Setup
# -----------------------
if not os.getenv("GROQ_API_KEY"):
    raise ValueError(" GROQ_API_KEY not set. Export it before running.")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.1-8b-instant")

# -----------------------
# System Prompt
# -----------------------
SYSTEM_MSG = """
You are SOL Research Centre’s report writer.

Strictly follow this fixed outline and tone:
- Title, client, crop, location are added by the generator (do not repeat them).
- 2. Soil Assessment Summary: list concise  advantages and  constraints using the provided classified bands.
- 3. Recommendations: A–F subsections in this order:
  A. Soil pH Correction
  B. Phosphorus Management
  C. Nitrogen & Potassium Management
  D. Organic Matter Improvement
  E. Drainage / Erosion Management
  F. Cover Cropping & Soil Health
- 4. Recommended Inputs Summary (rates per hectare; give sensible ranges with units).
- 5. Agronomic Guidelines for the crop (Ghana context; concise bullets).
- 6. Monitoring & Evaluation (what to track and how often).
- 7. Conclusion (short, decisive next steps).

Rules:
- Ghana agronomy context; concise, professional tone.
- DO NOT invent lab results. Use only the provided values and bands.
- If a parameter is “Not in compendium” or “Unknown”, acknowledge briefly and avoid making up thresholds.
- Keep content scannable: short paragraphs and bullet points only.
"""

# -----------------------
# Helper
# -----------------------
def _format_classified_context(classified: Dict[str, Any]) -> str:
    """Compact the sample’s classified results into readable JSON."""
    return json.dumps({
        k: {
            "value": v.get("value"),
            "band": v.get("band"),
            "unit": v.get("unit"),
            "ranges": v.get("ranges"),
            "source": v.get("source"),
        }
        for k, v in classified.items()
    }, ensure_ascii=False, indent=2)

# -----------------------
# Generator
# -----------------------
def generate_soil_summary(interpreted_sample: Dict[str, Any], crop: str, location: str) -> str:
    """
    Uses Groq LLM to produce structured agronomic interpretation text.
    """
    comp_context = _format_classified_context(interpreted_sample.get("classified", {}))

    messages = [
        {"role": "system", "content": SYSTEM_MSG},
        {
            "role": "user",
            "content": (
                f"Crop: {crop}\n"
                f"Location: {location}\n\n"
                f"Classified parameters (JSON):\n{comp_context}\n\n"
                "Write the section content for the outline in the system message. "
                "Do not restate the title block. Keep it concise and actionable."
            ),
        },
    ]

    resp = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        temperature=0.25,
    )
    return (resp.choices[0].message.content or "").strip()





# $env:GROQ_MODEL_ID = "llama-3.1-8b-instant"   # or "llama-3.3-70b-versatile"
# streamlit run src/app.py
