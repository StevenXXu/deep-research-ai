from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import sys
import os

# Add root CLAW folder to path to find llm_gateway
# We are in workspace/deep-research-saas/backend/
# Root is ../../../
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from research_writer import run_research
from pypdf import PdfReader

app = FastAPI()

# Enable CORS for Direct-to-Backend Uploads
# This bypasses Vercel's 4.5MB request body limit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Vercel, local, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    url: str
    email: str

@app.post("/research")
async def start_research(req: ResearchRequest):
    # Run in background thread so API returns immediately
    thread = threading.Thread(target=run_research, args=(req.url, req.email))
    thread.start()
    
    return {"status": "started", "message": "Agent dispatched locally."}

@app.post("/research-upload")
async def start_research_with_file(
    url: str = Form(...),
    email: str = Form(...),
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
            else:
                # fallback: treat as utf-8 text
                document_text = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"File parse failed: {e}")

    thread = threading.Thread(target=run_research, args=(url, email, document_text))
    thread.start()

    return {
        "status": "started",
        "message": "Agent dispatched with optional document context.",
        "hasDocument": bool(document_text)
    }

@app.get("/")
def home():
    return {"status": "online", "agent": "Deep Research Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
