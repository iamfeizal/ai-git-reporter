from docx import Document

def read_sample(filepath):
    doc = Document(filepath)
    print(f"Reading: {filepath}")
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            print(f"[{i}] {p.text.strip()}")
            if i > 50:
                break

if __name__ == "__main__":
    read_sample("sample_data/09-25 Laporan Bulanan September 2025 - Imam AF.docx")
