import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.pdf.dxf_to_pdf import convert_dxf_to_pdf


def test_pdf_generation():
    dxf_path = os.path.join(project_root, "output", "survey_47_test_sld.dxf")
    pdf_path = os.path.join(project_root, "output", "survey_47_test_sld.pdf")

    convert_dxf_to_pdf(dxf_path, pdf_path)

    pdf_exists = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0

    print("=================================================================================")
    print("                             PDF CONVERSION TEST RESULTS")
    print("=================================================================================")
    if pdf_exists:
        file_size = os.path.getsize(pdf_path)
        print("PDF Generation: PASS")
        print(f"Output Path: {pdf_path}")
        print(f"File Size:   {file_size} bytes")
    else:
        print("PDF Generation: FAIL")
        print(f"Output Path: {pdf_path}")
    print("=================================================================================")


if __name__ == "__main__":
    test_pdf_generation()
