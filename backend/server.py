from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import sys
import os

# Add root CLAW folder to path to find llm_gateway
# We are in workspace/deep-research-saas/backend/
# Root is ../../../
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from research_writer import run_research

app = FastAPI()

class ResearchRequest(BaseModel):
    url: str
    email: str

@app.post("/research")
async def start_research(req: ResearchRequest):
    # Run in background thread so API returns immediately
    thread = threading.Thread(target=run_research, args=(req.url, req.email))
    thread.start()
    
    return {"status": "started", "message": "Agent dispatched locally."}

@app.get("/")
def home():
    return {"status": "online", "agent": "Deep Research Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
