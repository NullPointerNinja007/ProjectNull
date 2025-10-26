import io, json, os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
import pandas as pd

from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Food Detector API", version="1.0.0")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY env var not set")

client = genai.Client(api_key=GOOGLE_API_KEY)

PROMPT = (
    "Identify distinct objects in this photo. only include items which are edible "
    "Return JSON with fields: items:[{label:string, count:int}]. If unsure, best guess."
)

def to_image_part(upload: UploadFile) -> types.Part:
    data = upload.file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    try:
        Image.open(io.BytesIO(data)).verify()
    except UnidentifiedImageError:
        raise HTTPException(400, "Uploaded file is not a valid image")
    mime = upload.content_type or "image/jpeg"
    return types.Part.from_bytes(data=data, mime_type=mime)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    part = to_image_part(file)


    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[part, PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
    except Exception as e:
        raise HTTPException(502, f"Model call failed: {e}")

    # Extract JSON text
    try:
        raw = resp.candidates[0].content.parts[0].text
        data = json.loads(raw)
        items = data.get("items", [])
        # build DataFrame (just to prove it’s tabular—API returns JSON)
        df = pd.DataFrame(items, columns=["label", "count"])
    except Exception as e:
        raise HTTPException(502, f"Bad model response: {e}")

    # Return JSON (client can do pd.DataFrame(...) on this)
    return JSONResponse({"items": items})

@app.get("/healthz")
def healthz():
    return {"ok": True}
