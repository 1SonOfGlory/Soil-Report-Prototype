# Soil report prototype

Python code for loading a soil-reference workbook, matching measurements to configured bands, and producing Word or PDF reports. An optional Groq adapter drafts narrative text from the classified values.

Inspect `src/compendium_loader.py` for workbook parsing, `src/rules_engine.py` for threshold matching, and `src/report_builder.py` for document generation. The Streamlit interface is `src/app.py`.

Create a Python virtual environment and install `requirements.txt`. Set `GROQ_API_KEY` only in your environment. Run `python -m streamlit run src/app.py` and provide a reference workbook you have permission to use. The original workbook, client records, generated reports, and credentials are excluded.

Classification reflects the supplied reference rules; it is not a trained agronomic model. Generated recommendations require qualified review. No agronomic validation, field trial, or outcome improvement is claimed. The legacy `src/main.py` runner has not been updated to the current rules-engine interface; use the Streamlit entry point.
