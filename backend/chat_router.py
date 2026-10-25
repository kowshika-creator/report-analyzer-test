import os
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List
import schemas
from core import generate_local_chatbot_response

router = APIRouter(
    prefix="/api",
    tags=["chat"]
)

# Standard clinical medical disclaimer
DISCLAIMER_TEXT = (
    "Disclaimer: This AI chatbot companion provides educational insights based on your parsed lab report. "
    "These findings do NOT replace a professional consultation, medical diagnosis, or personalized treatment plan "
    "from your licensed physician or healthcare provider."
)

def run_local_chatbot_fallback(
    query: str, 
    extracted_metrics: Optional[List[Any]] = None, 
    tone: Optional[str] = "Empathetic", 
    language: Optional[str] = "English"
) -> str:
    """
    Backwards-compatible helper wrapper calling local chatbot knowledge engine.
    """
    metrics_dicts = []
    if extracted_metrics:
        for m in extracted_metrics:
            if hasattr(m, "model_dump"):
                metrics_dicts.append(m.model_dump())
            elif isinstance(m, dict):
                metrics_dicts.append(m)
    reply, _ = generate_local_chatbot_response(
        user_query=query,
        extracted_metrics=metrics_dicts,
        tone=tone or "Empathetic",
        language=language or "English"
    )
    return reply

@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_assistant(
    request: schemas.ChatRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    POST /api/chat
    Safely interprets patient questions using local deterministic medical knowledge engine or optional Gemini AI,
    dynamically adapting to selected conversational tones (Empathetic, Clinical, Educational, Family).
    """
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    raw_tone = (request.selected_tone or "Empathetic").strip()
    lang_str = (request.language or "English").strip()

    metrics_dicts = [m.model_dump() for m in request.extracted_metrics]
    scan_dict = request.scan_context.model_dump() if request.scan_context else None

    # Handle scan report chat
    if request.report_type == "scan" or scan_dict:
        if not api_key:
            local_reply, disclaimer = generate_local_chatbot_response(
                user_query=request.current_message,
                scan_context=scan_dict,
                tone=raw_tone,
                language=lang_str
            )
            return schemas.ChatResponse(
                response=local_reply,
                disclaimer=disclaimer
            )

        try:
            from gemini_service import generate_gemini_content
            metadata = scan_dict.get("scan_metadata", {}) if scan_dict else {}
            findings = scan_dict.get("findings_breakdown", []) if scan_dict else []
            findings_str = "\n".join([f"- [{f.get('category', '').upper()}] {f.get('finding_text', '')}: {f.get('plain_english_explanation', '')}" for f in findings])

            prompt = (
                f"You are AXON Specialized Radiology & Medical Imaging Health Companion. "
                f"The patient language is {lang_str}. Tone: {raw_tone}.\n\n"
                f"### Scan Context:\n"
                f"- Modality: {metadata.get('modality', 'Imaging Scan')}\n"
                f"- Anatomical Region: {metadata.get('body_region', 'Clinical Region')}\n"
                f"- Impression: {scan_dict.get('radiologist_impression_summary', '') if scan_dict else 'N/A'}\n"
                f"- Triage Headline: {scan_dict.get('triage', {}).get('summary_headline', '') if scan_dict else 'N/A'}\n"
                f"Findings:\n{findings_str}\n\n"
                f"Patient Question: {request.current_message}\n\n"
                f"Instructions:\n"
                f"1. Explain findings in plain, empathetic, reassuring language ({lang_str}).\n"
                f"2. Explain what radiological terms mean without making definitive diagnoses.\n"
                f"3. Remind the patient that you are clarifying the written report and they should consult their radiologist or ordering doctor for definitive guidance."
            )
            response = generate_gemini_content(api_key, prompt)
            if response and response.text:
                return schemas.ChatResponse(
                    response=response.text,
                    disclaimer=DISCLAIMER_TEXT
                )
        except Exception as e:
            print(f"Optional Cloud AI Radiology Chat error skipped: {e}")

        local_reply, disclaimer = generate_local_chatbot_response(
            user_query=request.current_message,
            scan_context=scan_dict,
            tone=raw_tone,
            language=lang_str
        )
        return schemas.ChatResponse(
            response=local_reply,
            disclaimer=disclaimer
        )

    # Otherwise standard Lab report chat
    if not api_key:
        local_reply, disclaimer = generate_local_chatbot_response(
            user_query=request.current_message,
            extracted_metrics=metrics_dicts,
            tone=raw_tone,
            language=lang_str
        )
        return schemas.ChatResponse(
            response=local_reply,
            disclaimer=disclaimer
        )

    try:
        from gemini_service import generate_gemini_content
        metrics_str = ""
        for m in request.extracted_metrics:
            metrics_str += f"- {m.biomarker_name}: {m.value} {m.unit} (Status: {m.status})\n"

        prompt = (
            f"You are AXON General Health Companion. The patient language is {lang_str}. Tone: {raw_tone}.\n"
            f"Extracted patient lab values:\n{metrics_str}\n\n"
            f"Patient Question: {request.current_message}"
        )
        response = generate_gemini_content(api_key, prompt)
        if response and response.text:
            return schemas.ChatResponse(
                response=response.text,
                disclaimer=DISCLAIMER_TEXT
            )
    except Exception as e:
        print(f"Optional Cloud AI Chat error skipped: {e}")

    # Fallback to local chatbot
    local_reply, disclaimer = generate_local_chatbot_response(
        user_query=request.current_message,
        extracted_metrics=metrics_dicts,
        tone=raw_tone,
        language=lang_str
    )
    return schemas.ChatResponse(
        response=local_reply,
        disclaimer=disclaimer
    )
