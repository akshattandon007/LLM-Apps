"""Generate sample medical records (PDF + TXT) for testing Chart."""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DATA_DIR = Path(__file__).resolve().parent / "data"


def generate_lab_results_march_2023():
    """Lab results from March 2023."""
    pdf_path = DATA_DIR / "lab_results_march_2023.pdf"
    txt_path = DATA_DIR / "lab_results_march_2023.txt"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16, spaceAfter=20)
    heading = ParagraphStyle("Heading2", parent=styles["Heading2"], fontSize=13, spaceAfter=10)
    normal = styles["Normal"]

    elements = [
        Paragraph("Lab Results — March 2023", title_style),
        Paragraph("Date: March 15, 2023", heading),
        Paragraph("Patient: John Doe", heading),
        Spacer(1, 12),
        Paragraph("Complete Metabolic Panel and Lipid Profile", heading),
        Spacer(1, 6),
    ]

    # Table data
    data = [
        ["Test", "Result", "Reference Range", "Flag"],
        ["Hemoglobin A1c (HbA1c)", "5.7 %", "4.0 - 5.6 %", "High"],
        ["LDL Cholesterol", "130 mg/dL", "< 100 mg/dL", "High"],
        ["HDL Cholesterol", "48 mg/dL", "> 40 mg/dL", "Normal"],
        ["Total Cholesterol", "205 mg/dL", "< 200 mg/dL", "High"],
        ["Triglycerides", "150 mg/dL", "< 150 mg/dL", "Normal"],
        ["Vitamin D, 25-Hydroxy", "22 ng/mL", "30 - 100 ng/mL", "Low"],
        ["Glucose, Fasting", "98 mg/dL", "70 - 99 mg/dL", "Normal"],
        ["Creatinine", "0.95 mg/dL", "0.6 - 1.2 mg/dL", "Normal"],
        ["eGFR", "> 60 mL/min", "> 60 mL/min", "Normal"],
    ]

    table = Table(data, colWidths=[200, 100, 130, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Notes: Fasting glucose and HbA1c indicate prediabetic range. Vitamin D deficiency noted. Recommend supplementation and dietary counseling.", normal))

    doc.build(elements)

    # TXT version
    txt_content = """Lab Results — March 2023
Date: March 15, 2023
Patient: John Doe

Complete Metabolic Panel and Lipid Profile

Test                    Result      Reference Range     Flag
Hemoglobin A1c (HbA1c)  5.7 %       4.0 - 5.6 %         High
LDL Cholesterol         130 mg/dL   < 100 mg/dL         High
HDL Cholesterol         48 mg/dL    > 40 mg/dL          Normal
Total Cholesterol       205 mg/dL   < 200 mg/dL         High
Triglycerides           150 mg/dL   < 150 mg/dL         Normal
Vitamin D, 25-Hydroxy   22 ng/mL    30 - 100 ng/mL      Low
Glucose, Fasting        98 mg/dL    70 - 99 mg/dL       Normal
Creatinine              0.95 mg/dL  0.6 - 1.2 mg/dL     Normal
eGFR                    > 60 mL/min > 60 mL/min         Normal

Notes: Fasting glucose and HbA1c indicate prediabetic range.
Vitamin D deficiency noted. Recommend supplementation and dietary counseling.
"""
    with open(txt_path, "w") as f:
        f.write(txt_content)

    print(f"  Created: {pdf_path.name}")
    print(f"  Created: {txt_path.name}")


def generate_lab_results_september_2023():
    """Follow-up lab results from September 2023."""
    pdf_path = DATA_DIR / "lab_results_september_2023.pdf"
    txt_path = DATA_DIR / "lab_results_september_2023.txt"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16, spaceAfter=20)
    heading = ParagraphStyle("Heading2", parent=styles["Heading2"], fontSize=13, spaceAfter=10)
    normal = styles["Normal"]

    elements = [
        Paragraph("Lab Results — September 2023 (Follow-up)", title_style),
        Paragraph("Date: September 22, 2023", heading),
        Paragraph("Patient: John Doe", heading),
        Spacer(1, 12),
        Paragraph("Follow-up Metabolic Panel and Lipid Profile", heading),
        Spacer(1, 6),
    ]

    data = [
        ["Test", "Result", "Reference Range", "Flag"],
        ["Hemoglobin A1c (HbA1c)", "5.4 %", "4.0 - 5.6 %", "Normal"],
        ["LDL Cholesterol", "115 mg/dL", "< 100 mg/dL", "High"],
        ["HDL Cholesterol", "52 mg/dL", "> 40 mg/dL", "Normal"],
        ["Total Cholesterol", "190 mg/dL", "< 200 mg/dL", "Normal"],
        ["Triglycerides", "135 mg/dL", "< 150 mg/dL", "Normal"],
        ["Vitamin D, 25-Hydroxy", "35 ng/mL", "30 - 100 ng/mL", "Normal"],
        ["Glucose, Fasting", "92 mg/dL", "70 - 99 mg/dL", "Normal"],
        ["Creatinine", "0.92 mg/dL", "0.6 - 1.2 mg/dL", "Normal"],
        ["eGFR", "> 60 mL/min", "> 60 mL/min", "Normal"],
    ]

    table = Table(data, colWidths=[200, 100, 130, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Notes: Improvement in HbA1c (5.7% -> 5.4%), now within normal range. LDL decreased from 130 to 115 mg/dL. Vitamin D normalized with supplementation (22 -> 35 ng/mL). Continue current management.", normal))

    doc.build(elements)

    txt_content = """Lab Results — September 2023 (Follow-up)
Date: September 22, 2023
Patient: John Doe

Follow-up Metabolic Panel and Lipid Profile

Test                    Result      Reference Range     Flag
Hemoglobin A1c (HbA1c)  5.4 %       4.0 - 5.6 %         Normal
LDL Cholesterol         115 mg/dL   < 100 mg/dL         High
HDL Cholesterol         52 mg/dL    > 40 mg/dL          Normal
Total Cholesterol       190 mg/dL   < 200 mg/dL         Normal
Triglycerides           135 mg/dL   < 150 mg/dL         Normal
Vitamin D, 25-Hydroxy   35 ng/mL    30 - 100 ng/mL      Normal
Glucose, Fasting        92 mg/dL    70 - 99 mg/dL       Normal
Creatinine              0.92 mg/dL  0.6 - 1.2 mg/dL     Normal
eGFR                    > 60 mL/min > 60 mL/min         Normal

Notes: Improvement in HbA1c (5.7% -> 5.4%), now within normal range.
LDL decreased from 130 to 115 mg/dL. Vitamin D normalized with
supplementation (22 -> 35 ng/mL). Continue current management.
"""
    with open(txt_path, "w") as f:
        f.write(txt_content)

    print(f"  Created: {pdf_path.name}")
    print(f"  Created: {txt_path.name}")


def generate_doctor_note_annual_physical():
    """Doctor's note — annual physical summary."""
    pdf_path = DATA_DIR / "doctor_note_annual_physical_2022.pdf"
    txt_path = DATA_DIR / "doctor_note_annual_physical_2022.txt"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16, spaceAfter=20)
    heading = ParagraphStyle("Heading2", parent=styles["Heading2"], fontSize=13, spaceAfter=10)
    normal = styles["Normal"]

    elements = [
        Paragraph("Annual Physical Summary", title_style),
        Paragraph("Date of Visit: November 15, 2022", heading),
        Paragraph("Patient: John Doe", heading),
        Paragraph("Provider: Dr. Sarah Chen, MD", heading),
        Spacer(1, 12),
        Paragraph("History", heading),
        Paragraph("Patient presents for annual physical. No acute complaints. "
                  "Reports seasonal allergies in spring and fall, managed with over-the-counter "
                  "cetirizine 10mg daily as needed. No new symptoms. "
                  "Family history: father with type 2 diabetes, mother with hypertension.", normal),
        Spacer(1, 8),
        Paragraph("Physical Exam", heading),
        Paragraph("Vitals: BP 128/78, HR 72, Temp 98.6F, BMI 27.2. "
                  "General: well-appearing, no distress. HEENT: normal. "
                  "Cardiovascular: regular rate and rhythm, no murmurs. "
                  "Respiratory: clear to auscultation bilaterally. "
                  "Abdomen: soft, non-tender, no masses.", normal),
        Spacer(1, 8),
        Paragraph("Immunizations", heading),
        Paragraph("Tetanus, diphtheria, pertussis (Tdap) booster administered on November 15, 2022. "
                  "Influenza vaccine administered on November 15, 2022. "
                  "Patient is up to date on all routine vaccinations.", normal),
        Spacer(1, 8),
        Paragraph("Assessment", heading),
        Paragraph("1. Seasonal allergic rhinitis — stable, managed with OTC cetirizine.\n"
                  "2. Overweight (BMI 27.2) — discussed diet and exercise.\n"
                  "3. Prediabetes risk due to family history — advised glucose screening.", normal),
        Spacer(1, 8),
        Paragraph("Plan", heading),
        Paragraph("1. Continue cetirizine 10mg PO PRN for allergy symptoms.\n"
                  "2. Ibuprofen 200mg PO PRN for mild pain, not to exceed 1200mg/day.\n"
                  "3. Follow up in 6 months for repeat labs.\n"
                  "4. Next annual physical scheduled for November 2023.", normal),
    ]

    doc.build(elements)

    txt_content = """Annual Physical Summary
Date of Visit: November 15, 2022
Patient: John Doe
Provider: Dr. Sarah Chen, MD

History
Patient presents for annual physical. No acute complaints. Reports seasonal allergies
in spring and fall, managed with over-the-counter cetirizine 10mg daily as needed.
No new symptoms. Family history: father with type 2 diabetes, mother with hypertension.

Physical Exam
Vitals: BP 128/78, HR 72, Temp 98.6F, BMI 27.2. General: well-appearing, no distress.
HEENT: normal. Cardiovascular: regular rate and rhythm, no murmurs. Respiratory: clear
to auscultation bilaterally. Abdomen: soft, non-tender, no masses.

Immunizations
Tetanus, diphtheria, pertussis (Tdap) booster administered on November 15, 2022.
Influenza vaccine administered on November 15, 2022.
Patient is up to date on all routine vaccinations.

Assessment
1. Seasonal allergic rhinitis — stable, managed with OTC cetirizine.
2. Overweight (BMI 27.2) — discussed diet and exercise.
3. Prediabetes risk due to family history — advised glucose screening.

Plan
1. Continue cetirizine 10mg PO PRN for allergy symptoms.
2. Ibuprofen 200mg PO PRN for mild pain, not to exceed 1200mg/day.
3. Follow up in 6 months for repeat labs.
4. Next annual physical scheduled for November 2023.
"""
    with open(txt_path, "w") as f:
        f.write(txt_content)

    print(f"  Created: {pdf_path.name}")
    print(f"  Created: {txt_path.name}")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating sample medical records...")
    generate_lab_results_march_2023()
    generate_lab_results_september_2023()
    generate_doctor_note_annual_physical()
    print(f"\nDone! {len(list(DATA_DIR.glob('*')))} files in {DATA_DIR}/")
    print("Files:")
    for f in sorted(DATA_DIR.iterdir()):
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()