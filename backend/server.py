from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import sys
import os
import uuid
import time

# Add root CLAW folder to path to find llm_gateway
# We are in workspace/deep-research-saas/backend/
# Root is ../../../
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from research_writer import run_research
from pypdf import PdfReader
import docx  # Added for Word support

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job Store (In-Memory)
jobs = {}

class ResearchRequest(BaseModel):
    url: str
    email: str
    user_id: str = None # Optional for backward compatibility, but required for history

def update_job_progress(job_id, progress, status):
    """Callback to update job status"""
    if job_id in jobs:
        jobs[job_id]["progress"] = progress
        jobs[job_id]["status"] = status
        # Keep job alive for 1 hour
        jobs[job_id]["last_updated"] = time.time()

@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.post("/research")
async def start_research(req: ResearchRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"progress": 0, "status": "Queued", "result": None}
    
    # Run in background thread
    thread = threading.Thread(
        target=run_research, 
        args=(req.url, req.email, None, lambda p, s: update_job_progress(job_id, p, s), req.user_id)
    )
    thread.start()
    
    return {"status": "started", "job_id": job_id, "message": "Agent dispatched locally."}

@app.post("/research-upload")
async def start_research_with_file(
    url: str = Form(...),
    email: str = Form(...),
    user_id: str = Form(None), # Accept user_id from form
    file: UploadFile = File(None)
):
    document_text = None

    if file is not None:
        try:
            filename = (file.filename or "").lower()
            raw = await file.read()

            if filename.endswith(".pdf"):
                import io
                reader = PdfReader(io.BytesIO(raw))
                pages = []
                for p in reader.pages[:30]:
                    pages.append(p.extract_text() or "")
                document_text = "\n".join(pages)
            elif filename.endswith(".docx") or filename.endswith(".doc"):
                import io
                doc = docx.Document(io.BytesIO(raw))
                document_text = "\n".join([p.text for p in doc.paragraphs])
            else:
                # fallback: treat as utf-8 text
                document_text = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"File parse failed: {e}")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"progress": 0, "status": "Queued", "result": None}

    thread = threading.Thread(
        target=run_research, 
        args=(url, email, document_text, lambda p, s: update_job_progress(job_id, p, s), user_id)
    )
    thread.start()

    return {
        "status": "started",
        "job_id": job_id,
        "message": "Agent dispatched with optional document context.",
        "hasDocument": bool(document_text)
    }

@app.get("/")
def home():
    return {"status": "online", "agent": "Deep Research Backend"}

if __name__ == "__main__":
    import uvicorn
    # Respect Railway's dynamic PORT, default to 8081 if not set
    print("\n\n=== DEPLOYMENT CHECK: V4.1 (Final PDF Polish) - FORCE ===\n\n", flush=True)
    port = int(os.getenv("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
