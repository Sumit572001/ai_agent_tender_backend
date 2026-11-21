import os
import re
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
import pdfplumber

PRIORITY_ORDER = [
    "eProcurement",
    "RFP",
    "AGREEMENT",
    "Schedule",
    "Scope",
    "MAKE",
    "TECH",
    "DBR",
    "Site",
    "Environmental",
    "SUBSOIL",
    "ARCHITECTURE"
]

def get_doc_priority(filename: str) -> int:
    fn_lower = filename.lower()
    for idx, key in enumerate(PRIORITY_ORDER):
        if key.lower() in fn_lower:
            return idx
    return 99

def extract_text_from_pdf(pdf_path: str, max_pages: int = 50) -> Dict[str, Any]:
    filename = os.path.basename(pdf_path)
    pages_data = []
    total_text = ""
    page_count = 0

    try:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        pages_to_read = min(page_count, max_pages)
        for idx in range(pages_to_read):
            page_num = idx + 1
            try:
                text = reader.pages[idx].extract_text() or ""
                text = re.sub(r'[ 	]+', ' ', text).strip()
                if text:
                    pages_data.append({
                        "page_num": page_num,
                        "text": text,
                        "length": len(text)
                    })
                    total_text += f"\n--- [Document: {filename} | Page {page_num}] ---\n{text}\n"
            except Exception:
                continue
    except Exception as e:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                pages_to_read = min(page_count, max_pages)
                for idx in range(pages_to_read):
                    page_num = idx + 1
                    try:
                        text = pdf.pages[idx].extract_text() or ""
                        text = re.sub(r'[ 	]+', ' ', text).strip()
                        if text:
                            pages_data.append({
                                "page_num": page_num,
                                "text": text,
                                "length": len(text)
                            })
                            total_text += f"\n--- [Document: {filename} | Page {page_num}] ---\n{text}\n"
                    except Exception:
                        continue
        except Exception as e2:
            print(f"Error extracting PDF {filename}: {e2}")

    return {
        "filename": filename,
        "filepath": pdf_path,
        "page_count": page_count,
        "extracted_pages": len(pages_data),
        "total_chars": len(total_text),
        "pages": pages_data,
        "full_text": total_text
    }

def extract_folder_documents(pdf_paths: List[str], max_total_chars: int = 450000) -> Tuple[str, List[Dict[str, Any]]]:
    # Sort paths by business priority: Notice & Commercial > RFP > EPC Agreement > Schedules > Scope > Specs > Site > Drawings
    sorted_paths = sorted(pdf_paths, key=lambda p: get_doc_priority(os.path.basename(p)))

    combined_parts = []
    summaries = []
    current_chars = 0

    for path in sorted_paths:
        if not os.path.exists(path):
            continue
        doc_info = extract_text_from_pdf(path, max_pages=40)
        summaries.append({
            "filename": doc_info["filename"],
            "page_count": doc_info["page_count"],
            "total_chars": doc_info["total_chars"],
            "extracted_pages": doc_info["extracted_pages"]
        })
        if doc_info["full_text"]:
            combined_parts.append(doc_info["full_text"])
            current_chars += doc_info["total_chars"]
            if current_chars >= max_total_chars:
                break

    combined_text = "\n\n".join(combined_parts)
    if len(combined_text) > max_total_chars:
        combined_text = combined_text[:max_total_chars]

    return combined_text, summaries

class PDFService:
    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 50):
        return extract_text_from_pdf(pdf_path, max_pages=max_pages)

    def extract_folder_documents(self, pdf_paths: List[str], max_total_chars: int = 450000):
        return extract_folder_documents(pdf_paths, max_total_chars=max_total_chars)

pdf_svc = PDFService()
