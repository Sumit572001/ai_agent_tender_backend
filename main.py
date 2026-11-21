import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from storage_service import storage
from pdf_service import pdf_svc
from gemini_service import gemini_pool
from excel_service import excel_svc

app = FastAPI(
    title="TenderAI Backend API",
    description="Intelligent Tender PDF Analysis & 63-Point Checklist Portal",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FolderCreate(BaseModel):
    name: str
    department: Optional[str] = ""
    description: Optional[str] = ""

class CriterionCreate(BaseModel):
    category: str
    question: str
    description: Optional[str] = ""

class CriterionUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None

class BulkCriteria(BaseModel):
    items: List[dict]

class KeysUpdate(BaseModel):
    keys: List[str]

def resolve_folder_and_pdfs(folder_id: Optional[str] = None, folder_name: Optional[str] = None):
    folder = None
    if folder_id:
        folder = storage.get_folder(folder_id)
    
    if not folder and folder_name:
        all_folders = storage.get_folders()
        for f in all_folders:
            if f.get("name", "").strip().lower() == folder_name.strip().lower():
                folder = f
                break
    
    if not folder:
        all_folders = storage.get_folders()
        if all_folders:
            folder = all_folders[0]

    if not folder:
        return None, []

    f_id = folder.get("id")
    folder_dir = os.path.join(storage.folders_dir, f_id)
    pdf_paths = []
    if os.path.exists(folder_dir):
        pdf_paths = [os.path.join(folder_dir, f) for f in os.listdir(folder_dir) if f.lower().endswith(".pdf")]
    
    return folder, pdf_paths

@app.get("/")
def root():
    return {
        "app": "TenderAI",
        "status": "running",
        "version": "1.0.0",
        "model": gemini_pool.default_model,
        "active_keys": len(gemini_pool.keys),
        "total_criteria": len(storage.get_criteria())
    }

@app.get("/api/status")
def get_system_status():
    keys_status = gemini_pool.get_keys_status()
    criteria = storage.get_criteria()
    folders = storage.get_folders()
    return {
        "status": "online",
        "model": gemini_pool.default_model,
        "keys_count": len(gemini_pool.keys),
        "keys": keys_status,
        "criteria_count": len(criteria),
        "active_criteria_count": sum(1 for c in criteria if c.get("active", True)),
        "folders_count": len(folders)
    }

@app.post("/api/settings/keys")
def update_api_keys(payload: KeysUpdate):
    if not payload.keys:
        raise HTTPException(status_code=400, detail="Keys list cannot be empty")
    gemini_pool.add_or_update_keys(payload.keys)
    return {
        "message": f"Successfully updated {len(gemini_pool.keys)} API keys",
        "keys": gemini_pool.get_keys_status()
    }

@app.get("/api/folders")
def list_folders():
    return storage.get_folders()

@app.post("/api/folders")
def create_folder(payload: FolderCreate):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Folder name is required")
    folder = storage.create_folder(
        name=payload.name.strip(),
        department=payload.department.strip() if payload.department else "",
        description=payload.description.strip() if payload.description else ""
    )
    return folder

@app.get("/api/folders/{folder_id}")
def get_folder_details(folder_id: str):
    folder = storage.get_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    folder_dir = os.path.join(storage.folders_dir, folder_id)
    files_info = []
    if os.path.exists(folder_dir):
        for fname in os.listdir(folder_dir):
            fpath = os.path.join(folder_dir, fname)
            if os.path.isfile(fpath) and fname.lower().endswith(".pdf"):
                size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 2)
                files_info.append({
                    "name": fname,
                    "size_mb": size_mb,
                    "path": fpath
                })
    folder["file_details"] = files_info
    folder["file_count"] = len(files_info)
    return folder

@app.delete("/api/folders/{folder_id}")
def delete_folder(folder_id: str):
    success = storage.delete_folder(folder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"message": "Folder deleted successfully"}

MAX_FILE_SIZE_BYTES = 60 * 1024 * 1024

@app.post("/api/folders/{folder_id}/upload")
async def upload_pdfs_to_folder(folder_id: str, files: List[UploadFile] = File(...)):
    folder = storage.get_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_dir = os.path.join(storage.folders_dir, folder_id)
    os.makedirs(folder_dir, exist_ok=True)

    uploaded_files = []
    oversized_files = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        
        contents = await file.read()
        file_size = len(contents)
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = round(file_size / (1024 * 1024), 2)
            oversized_files.append(f"{file.filename} ({size_mb} MB)")
            continue

        safe_filename = os.path.basename(file.filename)
        dest_path = os.path.join(folder_dir, safe_filename)
        with open(dest_path, "wb") as f:
            f.write(contents)
        
        uploaded_files.append(safe_filename)

    if oversized_files:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds 60 MB limit: {', '.join(oversized_files)}. Please upload files under 60 MB."
        )

    all_pdfs = [f for f in os.listdir(folder_dir) if f.lower().endswith(".pdf")]
    storage.update_folder_file_count(folder_id, len(all_pdfs))

    return {
        "message": f"Successfully uploaded {len(uploaded_files)} PDF files",
        "uploaded": uploaded_files,
        "total_folder_files": len(all_pdfs)
    }

@app.delete("/api/folders/{folder_id}/files/{filename}")
def delete_file_from_folder(folder_id: str, filename: str):
    folder = storage.get_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_dir = os.path.join(storage.folders_dir, folder_id)
    target_path = os.path.join(folder_dir, os.path.basename(filename))

    if os.path.exists(target_path):
        os.remove(target_path)
        all_pdfs = [f for f in os.listdir(folder_dir) if f.lower().endswith(".pdf")]
        storage.update_folder_file_count(folder_id, len(all_pdfs))
        return {"message": f"File '{filename}' deleted", "remaining": len(all_pdfs)}
    else:
        raise HTTPException(status_code=404, detail="File not found in folder")

@app.get("/api/criteria")
def get_criteria():
    return storage.get_criteria()

@app.post("/api/criteria")
def add_criterion(payload: CriterionCreate):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question text is required")
    new_crit = storage.add_criterion({
        "category": payload.category.strip() or "General",
        "question": payload.question.strip(),
        "description": payload.description.strip() if payload.description else "",
        "active": True
    })
    return new_crit

@app.post("/api/criteria/bulk")
def bulk_add_criteria(payload: BulkCriteria):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Items list is empty")
    added = storage.bulk_add_criteria(payload.items)
    return {"message": f"Added {len(added)} criteria points", "total": len(storage.get_criteria())}

@app.post("/api/criteria/reset")
def reset_criteria():
    criteria = storage.reset_to_default_criteria()
    return {"message": "Reset to default 63 checklist criteria", "criteria": criteria}

@app.put("/api/criteria/{crit_id}")
def update_criterion(crit_id: str, payload: CriterionUpdate):
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    updated = storage.update_criterion(crit_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Criterion not found")
    return updated

@app.patch("/api/criteria/{crit_id}/toggle")
def toggle_criterion(crit_id: str):
    updated = storage.toggle_criterion(crit_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Criterion not found")
    return updated

@app.delete("/api/criteria/{crit_id}")
def delete_criterion(crit_id: str):
    success = storage.delete_criterion(crit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Criterion not found")
    return {"message": "Criterion deleted successfully"}

# ----------------- ANALYSIS STREAMING -----------------

@app.get("/api/analyze/{folder_id}")
@app.get("/api/analyze/{folder_id}/stream")
async def analyze_folder(folder_id: str):
    folder, pdf_paths = resolve_folder_and_pdfs(folder_id=folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if not pdf_paths:
        raise HTTPException(status_code=400, detail="No PDF files in this folder to analyze.")

    criteria = storage.get_criteria()
    active_criteria = [c for c in criteria if c.get("active", True)]
    if not active_criteria:
        raise HTTPException(status_code=400, detail="No active checklist points.")

    async def event_generator():
        yield f"data: {json.dumps({'stage': 'extracting', 'message': f'Extracting text from {len(pdf_paths)} PDF documents in folder...'})}\n\n"
        await asyncio.sleep(0.2)
        
        combined_text, doc_summaries = pdf_svc.extract_folder_documents(pdf_paths)
        if not combined_text.strip():
            yield f"data: {json.dumps({'stage': 'error', 'message': 'Failed to extract text from PDFs.'})}\n\n"
            return

        yield f"data: {json.dumps({'stage': 'extraction_complete', 'doc_count': len(pdf_paths), 'total_points': len(active_criteria)})}\n\n"
        await asyncio.sleep(0.2)

        batch_size = 10
        all_evaluated = []
        total_batches = (len(active_criteria) + batch_size - 1) // batch_size

        for i in range(0, len(active_criteria), batch_size):
            batch = active_criteria[i:i + batch_size]
            current_batch_num = (i // batch_size) + 1
            progress_pct = round((len(all_evaluated) / len(active_criteria)) * 100, 1)

            yield f"data: {json.dumps({'stage': 'analyzing', 'current_batch': current_batch_num, 'total_batches': total_batches, 'processed_points': len(all_evaluated), 'total_points': len(active_criteria), 'progress': progress_pct, 'current_category': batch[0].get('category', 'General')})}\n\n"
            
            try:
                batch_results = await asyncio.to_thread(gemini_pool.analyze_batch_questions, combined_text, batch)
                all_evaluated.extend(batch_results)
            except Exception as e:
                print(f"Batch analysis error: {e}")
                for q in batch:
                    all_evaluated.append({
                        "id": q.get("id"),
                        "category": q.get("category", "General"),
                        "question": q.get("question"),
                        "answer": "-",
                        "status": "Not Found",
                        "source": "-",
                        "confidence": "-"
                    })
            await asyncio.sleep(0.1)

        total_points = len(all_evaluated)
        found_points = sum(1 for item in all_evaluated if item.get("status") == "Found" and str(item.get("answer", "-")).strip() != "-")
        missing_points = total_points - found_points
        accuracy_score = round((found_points / max(1, total_points)) * 100, 2)

        analysis_record = {
            "folder_id": folder.get("id"),
            "folder_name": folder.get("name"),
            "created_at": datetime.now().isoformat(),
            "total_points": total_points,
            "found_points": found_points,
            "missing_points": missing_points,
            "accuracy_score": accuracy_score,
            "files": [os.path.basename(p) for p in pdf_paths],
            "doc_summaries": doc_summaries,
            "model_used": gemini_pool.default_model,
            "results": all_evaluated
        }

        analysis_id = storage.save_analysis_result(analysis_record)
        analysis_record["id"] = analysis_id

        yield f"data: {json.dumps({'stage': 'complete', 'progress': 100.0, 'analysis_id': analysis_id, 'data': analysis_record})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/analyze/{folder_id}")
async def analyze_folder_direct(folder_id: str):
    folder, pdf_paths = resolve_folder_and_pdfs(folder_id=folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if not pdf_paths:
        raise HTTPException(status_code=400, detail="No PDF files in this folder to analyze.")

    criteria = storage.get_criteria()
    active_criteria = [c for c in criteria if c.get("active", True)]
    if not active_criteria:
        raise HTTPException(status_code=400, detail="No active checklist points.")

    combined_text, doc_summaries = pdf_svc.extract_folder_documents(pdf_paths)
    if not combined_text.strip():
        raise HTTPException(status_code=400, detail="Failed to extract text from PDFs.")

    batch_size = 10
    all_evaluated = []
    for i in range(0, len(active_criteria), batch_size):
        batch = active_criteria[i:i + batch_size]
        try:
            batch_results = await asyncio.to_thread(gemini_pool.analyze_batch_questions, combined_text, batch)
            all_evaluated.extend(batch_results)
        except Exception as e:
            for q in batch:
                all_evaluated.append({
                    "id": q.get("id"),
                    "category": q.get("category", "General"),
                    "question": q.get("question"),
                    "answer": "-",
                    "status": "Not Found",
                    "source": "-",
                    "confidence": "-"
                })

    total_points = len(all_evaluated)
    found_points = sum(1 for item in all_evaluated if item.get("status") == "Found" and str(item.get("answer", "-")).strip() != "-")
    missing_points = total_points - found_points
    accuracy_score = round((found_points / max(1, total_points)) * 100, 2)

    analysis_record = {
        "folder_id": folder.get("id"),
        "folder_name": folder.get("name"),
        "created_at": datetime.now().isoformat(),
        "total_points": total_points,
        "found_points": found_points,
        "missing_points": missing_points,
        "accuracy_score": accuracy_score,
        "files": [os.path.basename(p) for p in pdf_paths],
        "doc_summaries": doc_summaries,
        "model_used": gemini_pool.default_model,
        "results": all_evaluated
    }

    analysis_id = storage.save_analysis_result(analysis_record)
    analysis_record["id"] = analysis_id
    return analysis_record

# ----------------- RE-ANALYZE ENDPOINTS (100% PRESERVE FOUND, TARGET MISSING) -----------------

@app.get("/api/reanalyze/{analysis_id}/stream")
@app.get("/api/reanalyze/{analysis_id}")
async def reanalyze_missing_points_stream(analysis_id: str):
    existing = storage.get_analysis_result(analysis_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Analysis record not found")

    folder, pdf_paths = resolve_folder_and_pdfs(
        folder_id=existing.get("folder_id"),
        folder_name=existing.get("folder_name")
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Tender folder not found.")
    if not pdf_paths:
        raise HTTPException(status_code=400, detail="No PDF files in folder.")

    current_results = existing.get("results", [])
    found_map = {}
    missing_criteria = []

    for item in current_results:
        ans = str(item.get("answer", "-")).strip()
        status = item.get("status", "Not Found")
        if status == "Found" and ans != "-":
            found_map[item.get("id")] = item  # 100% PRESERVED
        else:
            missing_criteria.append(item)

    async def event_generator():
        if not missing_criteria:
            yield f"data: {json.dumps({'stage': 'complete', 'progress': 100.0, 'analysis_id': analysis_id, 'data': existing, 'message': 'All points already found!'})}\n\n"
            return

        yield f"data: {json.dumps({'stage': 'extracting', 'message': f'Loading {len(pdf_paths)} tender documents for deep targeted audit of {len(missing_criteria)} missing points...'})}\n\n"
        await asyncio.sleep(0.2)

        combined_text, doc_summaries = pdf_svc.extract_folder_documents(pdf_paths)
        if not combined_text.strip():
            yield f"data: {json.dumps({'stage': 'error', 'message': 'Failed to extract text from tender PDFs.'})}\n\n"
            return

        yield f"data: {json.dumps({'stage': 'extraction_complete', 'doc_count': len(pdf_paths), 'missing_count': len(missing_criteria), 'preserved_count': len(found_map)})}\n\n"
        await asyncio.sleep(0.2)

        batch_size = 8
        reanalyzed_findings = {}
        total_missing = len(missing_criteria)
        total_batches = (total_missing + batch_size - 1) // batch_size

        for i in range(0, total_missing, batch_size):
            batch = missing_criteria[i:i + batch_size]
            current_batch_num = (i // batch_size) + 1
            progress_pct = round(20 + ((i / total_missing) * 75), 1)

            yield f"data: {json.dumps({'stage': 'analyzing', 'current_batch': current_batch_num, 'total_batches': total_batches, 'processed_points': i, 'total_missing': total_missing, 'preserved_count': len(found_map), 'progress': progress_pct, 'current_category': batch[0].get('category', 'Contract Conditions')})}\n\n"

            try:
                batch_results = await asyncio.to_thread(gemini_pool.analyze_missing_questions, combined_text, batch)
                for res_item in batch_results:
                    reanalyzed_findings[res_item.get("id")] = res_item
            except Exception as e:
                print(f"Re-analysis batch error: {e}")
                for q in batch:
                    reanalyzed_findings[q.get("id")] = q

            await asyncio.sleep(0.1)

        # Merge results - STRICT PRESERVATION of found items
        merged_results = []
        for orig in current_results:
            q_id = orig.get("id")
            if q_id in found_map:
                merged_results.append(found_map[q_id])
            elif q_id in reanalyzed_findings:
                new_finding = reanalyzed_findings[q_id]
                new_ans = str(new_finding.get("answer", "-")).strip()
                if new_finding.get("status") == "Found" and new_ans != "-":
                    merged_results.append(new_finding)
                else:
                    merged_results.append(orig)
            else:
                merged_results.append(orig)

        total_points = len(merged_results)
        found_points = sum(1 for item in merged_results if item.get("status") == "Found" and str(item.get("answer", "-")).strip() != "-")
        missing_points = total_points - found_points
        accuracy_score = round((found_points / max(1, total_points)) * 100, 2)

        existing["total_points"] = total_points
        existing["found_points"] = found_points
        existing["missing_points"] = missing_points
        existing["accuracy_score"] = accuracy_score
        existing["results"] = merged_results
        existing["reanalyzed_at"] = datetime.now().isoformat()

        storage.save_analysis_result(existing)

        yield f"data: {json.dumps({'stage': 'complete', 'progress': 100.0, 'analysis_id': analysis_id, 'data': existing})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/reanalyze/{analysis_id}")
async def reanalyze_missing_points_direct(analysis_id: str):
    existing = storage.get_analysis_result(analysis_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Analysis record not found")

    folder, pdf_paths = resolve_folder_and_pdfs(
        folder_id=existing.get("folder_id"),
        folder_name=existing.get("folder_name")
    )
    if not folder or not pdf_paths:
        raise HTTPException(status_code=400, detail="Folder or PDFs not found.")

    current_results = existing.get("results", [])
    found_map = {}
    missing_criteria = []

    for item in current_results:
        ans = str(item.get("answer", "-")).strip()
        status = item.get("status", "Found" if ans != "-" else "Not Found")
        if status == "Found" and ans != "-":
            found_map[item.get("id")] = item
        else:
            missing_criteria.append(item)

    if not missing_criteria:
        return existing

    combined_text, doc_summaries = pdf_svc.extract_folder_documents(pdf_paths)
    if not combined_text.strip():
        raise HTTPException(status_code=400, detail="Failed to extract text from tender PDFs.")

    batch_size = 8
    reanalyzed_findings = {}
    for i in range(0, len(missing_criteria), batch_size):
        batch = missing_criteria[i:i + batch_size]
        try:
            batch_results = await asyncio.to_thread(gemini_pool.analyze_missing_questions, combined_text, batch)
            for res_item in batch_results:
                reanalyzed_findings[res_item.get("id")] = res_item
        except Exception as e:
            for q in batch:
                reanalyzed_findings[q.get("id")] = q

    merged_results = []
    for orig in current_results:
        q_id = orig.get("id")
        if q_id in found_map:
            merged_results.append(found_map[q_id])
        elif q_id in reanalyzed_findings:
            new_finding = reanalyzed_findings[q_id]
            new_ans = str(new_finding.get("answer", "-")).strip()
            if new_finding.get("status") == "Found" and new_ans != "-":
                merged_results.append(new_finding)
            else:
                merged_results.append(orig)
        else:
            merged_results.append(orig)

    total_points = len(merged_results)
    found_points = sum(1 for item in merged_results if item.get("status") == "Found" and str(item.get("answer", "-")).strip() != "-")
    missing_points = total_points - found_points
    accuracy_score = round((found_points / max(1, total_points)) * 100, 2)

    existing["total_points"] = total_points
    existing["found_points"] = found_points
    existing["missing_points"] = missing_points
    existing["accuracy_score"] = accuracy_score
    existing["results"] = merged_results
    existing["reanalyzed_at"] = datetime.now().isoformat()

    storage.save_analysis_result(existing)
    return existing

# ----------------- RESULTS, EXPORT & HISTORY -----------------

@app.get("/api/results/{analysis_id}")
def get_single_analysis(analysis_id: str):
    res = storage.get_analysis_result(analysis_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return res

@app.get("/api/export/{analysis_id}")
def export_analysis_to_excel(analysis_id: str):
    res = storage.get_analysis_result(analysis_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    excel_path = excel_svc.generate_excel_report(res)
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=500, detail="Failed to generate Excel file")

    safe_folder_name = "".join(c for c in res.get("folder_name", "Tender") if c.isalnum() or c in (' ', '_', '-')).strip()
    download_filename = f"TenderAI_Audit_{safe_folder_name}_{res.get('id', 'report')[:8]}.xlsx"

    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=download_filename
    )

@app.get("/api/history")
def get_analysis_history():
    return storage.get_all_history()

@app.delete("/api/history/{analysis_id}")
def delete_history_item(analysis_id: str):
    success = storage.delete_history_item(analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="History record not found")
    return {"message": "History record deleted successfully"}
