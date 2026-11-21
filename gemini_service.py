import os
import json
import time
import requests
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class GeminiKeyPool:
    def __init__(self, keys: Optional[List[str]] = None, default_model: str = "gemini-3.6-flash"):
        if keys:
            self.keys = [k.strip() for k in keys if k.strip()]
        else:
            env_keys = os.environ.get("GEMINI_API_KEYS", "")
            self.keys = [k.strip() for k in env_keys.split(",") if k.strip()]
            if not self.keys:
                self.keys = []
        self.current_idx = 0
        self.default_model = default_model
        self.fallback_models = ["gemini-3.6-flash", "gemini-flash-latest"]
        self.key_stats = {k: {"success": 0, "failures": 0, "last_error": None} for k in self.keys}

    def get_keys_status(self) -> List[Dict[str, Any]]:
        status_list = []
        for i, k in enumerate(self.keys):
            masked = k[:6] + "..." + k[-4:] if len(k) > 10 else "***"
            stats = self.key_stats.get(k, {"success": 0, "failures": 0, "last_error": None})
            status_list.append({
                "index": i + 1,
                "masked_key": masked,
                "success_count": stats["success"],
                "failure_count": stats["failures"],
                "last_error": stats["last_error"],
                "is_current": (i == self.current_idx)
            })
        return status_list

    def add_or_update_keys(self, keys: List[str]):
        new_keys = [k.strip() for k in keys if k.strip()]
        if new_keys:
            self.keys = new_keys
            self.current_idx = 0
            self.key_stats = {k: {"success": 0, "failures": 0, "last_error": None} for k in self.keys}

    def _call_gemini_api(self, prompt: str, system_instruction: str = "", model: Optional[str] = None) -> str:
        model_name = model or self.default_model
        total_keys = len(self.keys)
        attempts = 0
        last_exception = None

        while attempts < total_keys * 2:
            key = self.keys[self.current_idx]
            self.current_idx = (self.current_idx + 1) % total_keys
            attempts += 1

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            try:
                response = requests.post(url, json=payload, timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            self.key_stats[key]["success"] += 1
                            return parts[0].get("text", "")
                    self.key_stats[key]["failures"] += 1
                    self.key_stats[key]["last_error"] = "Empty candidates or safety filter"
                elif response.status_code in [429, 503, 500]:
                    err_msg = f"HTTP {response.status_code}: {response.text[:150]}"
                    self.key_stats[key]["failures"] += 1
                    self.key_stats[key]["last_error"] = err_msg
                    last_exception = Exception(err_msg)
                    time.sleep(1)
                    continue
                else:
                    err_msg = f"HTTP {response.status_code}: {response.text[:150]}"
                    self.key_stats[key]["failures"] += 1
                    self.key_stats[key]["last_error"] = err_msg
                    last_exception = Exception(err_msg)
            except Exception as e:
                self.key_stats[key]["failures"] += 1
                self.key_stats[key]["last_error"] = str(e)
                last_exception = e
                time.sleep(1)

        for fallback_m in self.fallback_models:
            if fallback_m == model_name:
                continue
            for key in self.keys:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{fallback_m}:generateContent?key={key}"
                try:
                    payload = {
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                    }
                    if system_instruction:
                        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
                    resp = requests.post(url, json=payload, timeout=90)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                except Exception:
                    continue

        raise Exception(f"All Gemini API keys and models exhausted. Last error: {last_exception}")

    def analyze_batch_questions(self, tender_text: str, questions_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        system_prompt = (
            "You are an expert Government & Corporate Tender Document Analyst and Senior Procurement Auditor. "
            "Your task is to thoroughly analyze the provided tender document text and answer specific checklist criteria with extreme accuracy.\n"
            "CRITICAL RULES:\n"
            "1. For each question, extract the exact fact, figure, value, condition, rate, percentage, or date mentioned in the tender text.\n"
            "2. Always provide the exact source citation (Document name, Page number, and Clause/Section reference) where the answer was found.\n"
            "3. MULTIPLE RELATED ANSWERS / OPTIONS: If a checklist question has multiple relevant clauses, options, rates, phases, or conditions (e.g. 2 to 5 relevant answers found in different sections, or alternative values/milestones), list ALL of them clearly formatted with bullet points ('• Option 1: ...\\n• Option 2: ...') so the user can review all applicable options.\n"
            "4. If the answer is NOT present, not specified, or cannot be found anywhere in the provided tender text, "
            "you MUST set 'answer' strictly to '-' (a single dash string), set 'source' to '-', and set 'status' to 'Not Found'. "
            "Do NOT make assumptions, guess, or provide generic textbook advice. If it is missing, output '-'.\n"
            "5. Return ONLY a valid JSON array of objects conforming to the requested schema."
        )

        batch_input = []
        for q in questions_batch:
            batch_input.append({
                "id": q.get("id"),
                "category": q.get("category", "General"),
                "question": q.get("question"),
                "description": q.get("description", "")
            })

        max_chars = 450000
        safe_tender_text = tender_text[:max_chars] if len(tender_text) > max_chars else tender_text

        user_prompt = f"""
Here is the tender document text extracted from the uploaded PDF files:
==================== TENDER DOCUMENTS START ====================
{safe_tender_text}
==================== TENDER DOCUMENTS END ====================

Please evaluate the following checklist questions against the tender documents:
{json.dumps(batch_input, indent=2)}

Output JSON Schema:
[
  {{
    "id": "crit_id",
    "category": "Category Name",
    "question": "Exact question text",
    "answer": "Exact extracted value/clause from tender (formatted with '• ' bullet points if multiple related answers exist) OR '-' if not found",
    "status": "Found" or "Not Found",
    "source": "Document Name, Page X, Clause Y OR '-' if not found",
    "confidence": "High" / "Medium" / "Low" / "-"
  }}
]
"""
        raw_json = self._call_gemini_api(user_prompt, system_instruction=system_prompt)
        return self._parse_and_normalize_response(raw_json, questions_batch)

    def analyze_missing_questions(self, tender_text: str, missing_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        system_prompt = (
            "You are a Senior Principal Tender Auditor and Contract Law Expert conducting a targeted deep-dive audit. "
            "Your sole objective is to locate specific clauses and terms in the provided tender text that were previously missing or unmapped.\n"
            "CRITICAL INSTRUCTIONS FOR TARGETED AUDIT:\n"
            "1. Focus deeply on General Conditions of Contract (GCC), Special Conditions of Contract (SCC), EPC Agreement Clauses, Schedules (Schedule A to Q), RFP Volumes, Bill of Quantities (BOQ), and Technical Annexures.\n"
            "2. Search specifically for commercial & contractual clauses such as Milestones, Liquidated Damages, Incentive for Early Completion, Minimum value of work to be executed interim RA payment, R.A Bill Payments, Period of Final Measurement, Price Escalation, Stamp Duty for Agreement, Retention Money, Release of Retention Money, Security Deposit, Release of Security Deposit, Performance Security, Release of Performance Security, Defect Liability Period, Mobilisation Advance, Interest Rate of Mobilization Advance, Recovery of Mobilisation Advance, Secured Advance on materials, % of all overheads and profits, Basic Rates, Escrow Account, Space for labour hutment, Working Time, Project Documentary Film & Video-Grapy, Transportation for Client, Staffing, and Force Majeure.\n"
            "3. MULTIPLE RELATED ANSWERS / OPTIONS: If a question has multiple relevant clauses, options, rates, phases, or conditions (e.g. 2 to 5 relevant answers found in different contract sections, or alternative values/milestones), list ALL of them clearly formatted with bullet points ('• Option 1: ...\\n• Option 2: ...') so the user can review all applicable options.\n"
            "4. For any item found, provide the exact Document Name, Page Number, and Clause/Article/Section reference in 'source'.\n"
            "5. If a point is genuinely not mentioned anywhere in the tender documents, strictly output '-' for 'answer', '-' for 'source', and 'Not Found' for 'status'.\n"
            "6. Return ONLY a valid JSON array of objects conforming to the schema."
        )

        batch_input = []
        for q in missing_questions:
            batch_input.append({
                "id": q.get("id"),
                "category": q.get("category", "General"),
                "question": q.get("question"),
                "description": q.get("description", "")
            })

        max_chars = 450000
        safe_tender_text = tender_text[:max_chars] if len(tender_text) > max_chars else tender_text

        user_prompt = f"""
TARGETED DEEP AUDIT FOR MISSING CHECKLIST POINTS:
The following specific criteria points need to be located in the tender document text.
Please perform a thorough search across all contract terms, conditions, schedules, and annexures:

==================== TENDER DOCUMENTS START ====================
{safe_tender_text}
==================== TENDER DOCUMENTS END ====================

Target Missing Criteria to Evaluate:
{json.dumps(batch_input, indent=2)}

Output JSON Schema:
[
  {{
    "id": "crit_id",
    "category": "Category Name",
    "question": "Exact question text",
    "answer": "Exact extracted clause/value (use '• ' bullet points if multiple related answers exist) OR '-' if not found",
    "status": "Found" or "Not Found",
    "source": "Document Name, Page X, Clause Y OR '-' if not found",
    "confidence": "High" / "Medium" / "Low" / "-"
  }}
]
"""
        raw_json = self._call_gemini_api(user_prompt, system_instruction=system_prompt)
        return self._parse_and_normalize_response(raw_json, missing_questions)

    def _parse_and_normalize_response(self, raw_json: str, original_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned_json = raw_json.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()

        try:
            parsed_results = json.loads(cleaned_json)
            normalized = []
            for item in parsed_results:
                ans = str(item.get("answer", "")).strip()
                if not ans or ans.lower() in ["not found", "n/a", "none", "not specified", "nil", "null", "not available"]:
                    ans = "-"
                
                is_found = (ans != "-")
                status = "Found" if is_found else "Not Found"
                source = str(item.get("source", "-")).strip() if is_found else "-"

                normalized.append({
                    "id": item.get("id"),
                    "category": item.get("category", "General"),
                    "question": item.get("question", ""),
                    "answer": ans,
                    "status": status,
                    "source": source if source else "-",
                    "confidence": item.get("confidence", "High") if is_found else "-"
                })
            return normalized
        except Exception as e:
            print(f"Error parsing Gemini response: {e}\nRaw: {raw_json[:300]}")
            fallback_items = []
            for q in original_batch:
                fallback_items.append({
                    "id": q.get("id"),
                    "category": q.get("category", "General"),
                    "question": q.get("question"),
                    "answer": "-",
                    "status": "Not Found",
                    "source": "-",
                    "confidence": "-"
                })
            return fallback_items

gemini_pool = GeminiKeyPool()
