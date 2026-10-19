"""
main.py
--------
Main runner for generating SOL Research soil analysis reports.
"""

import os
from rules_engine import interpret_sample
from report_builder import generate_word_report, generate_pdf_report
from llm_agent import generate_soil_summary


def main():
    # Ensure reports folder exists
    os.makedirs("reports", exist_ok=True)

    # Example test sample(s)
    samples = [
        {
            "pH": 5.2,
            "nitrogen_ppm": 8.5,
            "phosphorus_ppm": 12.0,
            "potassium_ppm": 85.0,
            "organic_matter_pct": 1.8,
            "ec_dS_m": 1.1,
        },
        {
            "pH": 6.8,
            "nitrogen_ppm": 18.0,
            "phosphorus_ppm": 25.0,
            "potassium_ppm": 150.0,
            "organic_matter_pct": 3.2,
            "ec_dS_m": 0.8,
        },
    ]

    client_name = "Demo Client"
    crop = "Maize"
    location = "Attakrom"  # Example farm name

    print("\n Interpreting soil samples...\n")

    results_with_summaries = []
    for idx, sample in enumerate(samples, start=1):
        result = interpret_sample(sample)

        # Generate LLM-based narrative for each sample
        print(f" Generating AI summary for Sample {idx}...")
        summary = generate_soil_summary(result, crop=crop, location=location)
        result["llm_summary"] = summary
        results_with_summaries.append(result)

    # Display one example summary in console
    print("\n=== Example LLM-Generated Summary ===\n")
    print(results_with_summaries[0]["llm_summary"])
    print("\n-----------------------------------\n")

    # === Generate filenames dynamically based on farm/location ===
    safe_location = location.replace(" ", "_")
    word_filename = f"reports/{safe_location}_Soil_Report.docx"
    pdf_filename = f"reports/{safe_location}_Soil_Report.pdf"

    # === Generate Word and PDF reports ===
    word_doc = generate_word_report(client_name, crop, results_with_summaries, location)
    word_doc.save(word_filename)

    pdf_buffer = generate_pdf_report(client_name, crop, results_with_summaries, location)
    with open(pdf_filename, "wb") as f:
        f.write(pdf_buffer.read())

    print(" Reports generated successfully!")
    print(f"- {word_filename}")
    print(f"- {pdf_filename}")


if __name__ == "__main__":
    main()




# cd "C:\Users\SURFACE LAPTOP\Desktop\JABESS\ML\SOL_Research" venv\Scripts\activate

# python .\src\main.py
# python .\src\app.py

