# src/app.py (only the key parts)
import streamlit as st
import pandas as pd
import os
from compendium_loader import load_from_uploaded_files
from rules_engine import interpret_sample
from report_builder import generate_word_report, generate_pdf_report
from llm_agent import generate_soil_summary

st.set_page_config(page_title="SOL Research AI Reporter", layout="wide")
st.title(" SOL Research AI Soil Report Generator")

st.sidebar.header("⚙ Client Info")
client_name = st.sidebar.text_input("Client Name", "Demo Client")
crop = st.sidebar.text_input("Crop", "Maize")
location = st.sidebar.text_input("Farm/Location", "Attakrom")

st.sidebar.header(" Upload Compendiums (Required)")
macro_up = st.sidebar.file_uploader("Macro Nutrient Compendium (.xlsx)", type=["xlsx"], key="macro")
micro_up = st.sidebar.file_uploader("Micronutrient Compendium (.xlsx)", type=["xlsx"], key="micro")

@st.cache_data(show_spinner=False)
def parse_compendiums(macro_file, micro_file):
    return load_from_uploaded_files(macro_file, micro_file)

uploaded_file = st.file_uploader(" Upload soil test data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file and macro_up and micro_up:
    compendium = parse_compendiums(macro_up, micro_up)

    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    st.subheader(" Data Preview")
    st.dataframe(df.head())

    if st.button(" Generate AI Report"):
        samples = df.to_dict(orient="records")
        results = []
        for sample in samples:
            interpreted = interpret_sample(sample, crop=crop, compendium=compendium)
            interpreted["llm_summary"] = generate_soil_summary(interpreted, crop=crop, location=location)
            results.append(interpreted)

        os.makedirs("reports", exist_ok=True)
        safe = location.replace(" ", "_")
        word_path = f"reports/{safe}_Soil_Report.docx"
        pdf_path = f"reports/{safe}_Soil_Report.pdf"

        doc = generate_word_report(client_name, crop, results, location)
        doc.save(word_path)
        pdf_buf = generate_pdf_report(client_name, crop, results, location)
        with open(pdf_path, "wb") as f: f.write(pdf_buf.read())

        st.success(" Reports generated.")
        with open(word_path, "rb") as f:
            st.download_button("⬇ Download Word", f, file_name=os.path.basename(word_path))
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download PDF", f, file_name=os.path.basename(pdf_path))
else:
    st.info("↖ Upload both compendiums and a data file to proceed.")
