
import sys

def extract_text(pdf_path):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        pass

    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        pass
        
    try:
        from pdfminer.high_level import extract_text
        return extract_text(pdf_path)
    except ImportError:
        return "ERROR: No PDF library found (PyPDF2, pypdf, pdfminer). Please install one."
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    pdf_path = "End-to-End Data Pipeline.pdf"
    print(extract_text(pdf_path))
