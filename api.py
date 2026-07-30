from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import json
from datetime import datetime
from agent_api import analyze_image
from tools.models import SkinAnalysisSchema

app = FastAPI(title="Auto Retoucher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR  = "uploads"
HISTORY_DIR = "history"
os.makedirs(UPLOAD_DIR,  exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# NOTE: app.mount() is called AFTER all @app routes are defined below,
# so FastAPI matches API routes first and only falls back to StaticFiles for /uploads/*.


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/analyze", response_model=SkinAnalysisSchema)
async def analyze_endpoint(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = analyze_image(file_path)

    # Persist result so it can be retrieved from history without re-processing
    history_entry = {
        "filename":    file.filename,
        "analyzed_at": datetime.now().isoformat(),
        "result":      result.model_dump(),
    }
    history_path = os.path.join(HISTORY_DIR, file.filename + ".json")
    with open(history_path, "w", encoding="utf-8") as hf:
        json.dump(history_entry, hf, ensure_ascii=False, indent=2)

    return result


@app.get("/history")
async def get_history():
    items = []
    for fname in os.listdir(HISTORY_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(HISTORY_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception:
            pass
    items.sort(key=lambda x: x.get("analyzed_at", ""), reverse=True)
    return items


@app.delete("/history/{filename}")
async def delete_history(filename: str):
    # Guard against path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    img_path     = os.path.join(UPLOAD_DIR,  filename)
    history_path = os.path.join(HISTORY_DIR, filename + ".json")

    deleted = []
    for p in [img_path, history_path]:
        if os.path.exists(p):
            os.remove(p)
            deleted.append(p)

    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"deleted": deleted}


# Static files mounted last so API routes take priority during matching
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
