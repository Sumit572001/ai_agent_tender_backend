import os
import json
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from default_criteria import DEFAULT_TENDER_CRITERIA

BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FOLDERS_DIR = os.path.join(BASE_DATA_DIR, "folders")
RESULTS_DIR = os.path.join(BASE_DATA_DIR, "results")
EXPORTS_DIR = os.path.join(BASE_DATA_DIR, "exports")
CRITERIA_FILE = os.path.join(BASE_DATA_DIR, "criteria.json")
HISTORY_FILE = os.path.join(BASE_DATA_DIR, "history.json")

def init_storage():
    """Ensure all required directories and files exist."""
    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    os.makedirs(FOLDERS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    if not os.path.exists(CRITERIA_FILE):
        with open(CRITERIA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TENDER_CRITERIA, f, indent=2, ensure_ascii=False)

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

# ----------------- FOLDER MANAGEMENT -----------------

def get_all_folders() -> List[Dict[str, Any]]:
    init_storage()
    folders = []
    if not os.path.exists(FOLDERS_DIR):
        return folders
    
    for item in os.listdir(FOLDERS_DIR):
        fpath = os.path.join(FOLDERS_DIR, item)
        if os.path.isdir(fpath):
            meta_path = os.path.join(fpath, "meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        files = [f for f in os.listdir(fpath) if f.lower().endswith(".pdf")]
                        meta["file_count"] = len(files)
                        meta["files"] = files
                        folders.append(meta)
                except Exception:
                    pass
    folders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return folders

def create_folder(name: str, description: str = "", department: str = "") -> Dict[str, Any]:
    init_storage()
    folder_id = str(uuid.uuid4())[:8] + "_" + "".join(c if c.isalnum() else "_" for c in name.lower())[:24]
    folder_path = os.path.join(FOLDERS_DIR, folder_id)
    os.makedirs(folder_path, exist_ok=True)

    meta = {
        "id": folder_id,
        "name": name,
        "description": description,
        "department": department,
        "created_at": datetime.now().isoformat(),
        "file_count": 0,
        "files": []
    }

    with open(os.path.join(folder_path, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta

def get_folder(folder_id: str) -> Optional[Dict[str, Any]]:
    init_storage()
    folder_path = os.path.join(FOLDERS_DIR, folder_id)
    if not os.path.exists(folder_path):
        return None
    meta_path = os.path.join(folder_path, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
            file_details = []
            for fn in files:
                full_fn = os.path.join(folder_path, fn)
                file_details.append({
                    "name": fn,
                    "size_bytes": os.path.getsize(full_fn),
                    "size_mb": round(os.path.getsize(full_fn) / (1024 * 1024), 2)
                })
            meta["file_count"] = len(files)
            meta["files"] = files
            meta["file_details"] = file_details
            return meta
    return None

def delete_folder(folder_id: str) -> bool:
    folder_path = os.path.join(FOLDERS_DIR, folder_id)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path, ignore_errors=True)
        return True
    return False

def get_folder_pdf_paths(folder_id: str) -> List[str]:
    folder_path = os.path.join(FOLDERS_DIR, folder_id)
    if not os.path.exists(folder_path):
        return []
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

def save_uploaded_file(folder_id: str, filename: str, content: bytes) -> str:
    folder_path = os.path.join(FOLDERS_DIR, folder_id)
    os.makedirs(folder_path, exist_ok=True)
    safe_filename = os.path.basename(filename)
    dest_path = os.path.join(folder_path, safe_filename)
    with open(dest_path, "wb") as f:
        f.write(content)
    return dest_path

def delete_folder_file(folder_id: str, filename: str) -> bool:
    folder_path = os.path.join(FOLDERS_DIR, folder_id)
    file_path = os.path.join(folder_path, os.path.basename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

# ----------------- CRITERIA (QUESTIONS) MANAGEMENT -----------------

def get_criteria(active_only: bool = False) -> List[Dict[str, Any]]:
    init_storage()
    try:
        with open(CRITERIA_FILE, "r", encoding="utf-8") as f:
            criteria = json.load(f)
            if active_only:
                return [c for c in criteria if c.get("active", True)]
            return criteria
    except Exception:
        return DEFAULT_TENDER_CRITERIA

def save_criteria(criteria: List[Dict[str, Any]]):
    init_storage()
    with open(CRITERIA_FILE, "w", encoding="utf-8") as f:
        json.dump(criteria, f, indent=2, ensure_ascii=False)

def add_criterion(question: str, category: str = "General & Authority", description: str = "", active: bool = True) -> Dict[str, Any]:
    criteria = get_criteria()
    new_id = f"crit_{len(criteria) + 1}_{uuid.uuid4().hex[:6]}"
    item = {
        "id": new_id,
        "category": category.strip() or "General",
        "question": question.strip(),
        "description": description.strip(),
        "active": active
    }
    criteria.append(item)
    save_criteria(criteria)
    return item

def update_criterion(crit_id: str, question: Optional[str] = None, category: Optional[str] = None, description: Optional[str] = None, active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    criteria = get_criteria()
    for c in criteria:
        if c.get("id") == crit_id:
            if question is not None:
                c["question"] = question.strip()
            if category is not None:
                c["category"] = category.strip()
            if description is not None:
                c["description"] = description.strip()
            if active is not None:
                c["active"] = active
            save_criteria(criteria)
            return c
    return None

def delete_criterion(crit_id: str) -> bool:
    criteria = get_criteria()
    new_criteria = [c for c in criteria if c.get("id") != crit_id]
    if len(new_criteria) != len(criteria):
        save_criteria(new_criteria)
        return True
    return False

def reset_criteria_to_default() -> List[Dict[str, Any]]:
    save_criteria(DEFAULT_TENDER_CRITERIA)
    return DEFAULT_TENDER_CRITERIA

def bulk_add_criteria(questions: List[str], default_category: str = "Custom Checklist") -> List[Dict[str, Any]]:
    criteria = get_criteria()
    added = []
    for q in questions:
        if not q.strip():
            continue
        new_id = f"crit_{len(criteria) + 1}_{uuid.uuid4().hex[:6]}"
        item = {
            "id": new_id,
            "category": default_category,
            "question": q.strip(),
            "description": "User custom point",
            "active": True
        }
        criteria.append(item)
        added.append(item)
    save_criteria(criteria)
    return added

# ----------------- RESULTS & HISTORY -----------------

def save_analysis_result(result_data: Dict[str, Any]) -> str:
    init_storage()
    analysis_id = result_data.get("id") or str(uuid.uuid4())[:10]
    result_data["id"] = analysis_id
    result_data["created_at"] = result_data.get("created_at") or datetime.now().isoformat()

    res_path = os.path.join(RESULTS_DIR, f"{analysis_id}.json")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    history_entry = {
        "id": analysis_id,
        "folder_id": result_data.get("folder_id"),
        "folder_name": result_data.get("folder_name"),
        "created_at": result_data["created_at"],
        "total_points": result_data.get("total_points", 0),
        "found_points": result_data.get("found_points", 0),
        "missing_points": result_data.get("missing_points", 0),
        "accuracy_score": result_data.get("accuracy_score", 0.0),
        "file_count": len(result_data.get("files", [])),
        "files": result_data.get("files", []),
        "model_used": result_data.get("model_used", "")
    }

    history = get_history()
    history = [h for h in history if h.get("id") != analysis_id]
    history.insert(0, history_entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return analysis_id

def get_history() -> List[Dict[str, Any]]:
    init_storage()
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def get_analysis_result(analysis_id: str) -> Optional[Dict[str, Any]]:
    init_storage()
    res_path = os.path.join(RESULTS_DIR, f"{analysis_id}.json")
    if os.path.exists(res_path):
        try:
            with open(res_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def delete_history_item(analysis_id: str) -> bool:
    init_storage()
    res_path = os.path.join(RESULTS_DIR, f"{analysis_id}.json")
    if os.path.exists(res_path):
        try:
            os.remove(res_path)
        except Exception:
            pass
    history = get_history()
    new_history = [h for h in history if h.get("id") != analysis_id]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(new_history, f, indent=2, ensure_ascii=False)
    return True

# ----------------- STORAGE CLASS ADAPTER -----------------

class StorageService:
    @property
    def folders_dir(self):
        init_storage()
        return FOLDERS_DIR

    def get_folders(self):
        return get_all_folders()

    def create_folder(self, name: str, description: str = "", department: str = ""):
        return create_folder(name=name, description=description, department=department)

    def get_folder(self, folder_id: str):
        return get_folder(folder_id)

    def delete_folder(self, folder_id: str):
        return delete_folder(folder_id)

    def update_folder_file_count(self, folder_id: str, count: int):
        f = get_folder(folder_id)
        if f:
            f["file_count"] = count
            meta_path = os.path.join(FOLDERS_DIR, folder_id, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "w", encoding="utf-8") as file:
                    json.dump(f, file, indent=2)

    def get_criteria(self, active_only: bool = False):
        return get_criteria(active_only=active_only)

    def add_criterion(self, data: dict):
        return add_criterion(
            question=data.get("question", ""),
            category=data.get("category", "General"),
            description=data.get("description", ""),
            active=data.get("active", True)
        )

    def update_criterion(self, crit_id: str, updates: dict):
        return update_criterion(
            crit_id=crit_id,
            question=updates.get("question"),
            category=updates.get("category"),
            description=updates.get("description"),
            active=updates.get("active")
        )

    def toggle_criterion(self, crit_id: str):
        c = [x for x in get_criteria() if x.get("id") == crit_id]
        if c:
            curr = c[0].get("active", True)
            return update_criterion(crit_id=crit_id, active=not curr)
        return None

    def delete_criterion(self, crit_id: str):
        return delete_criterion(crit_id)

    def reset_to_default_criteria(self):
        return reset_criteria_to_default()

    def bulk_add_criteria(self, items: list):
        if isinstance(items, list) and items and isinstance(items[0], str):
            return bulk_add_criteria(items)
        questions = [it.get("question", "") if isinstance(it, dict) else str(it) for it in items]
        return bulk_add_criteria(questions)

    def save_analysis_result(self, result_data: dict):
        return save_analysis_result(result_data)

    def get_analysis_result(self, analysis_id: str):
        return get_analysis_result(analysis_id)

    def get_all_history(self):
        return get_history()

    def delete_history_item(self, analysis_id: str):
        return delete_history_item(analysis_id)

storage = StorageService()
