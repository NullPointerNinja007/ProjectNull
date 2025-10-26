import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import google.generativeai as genai

# Load environment variables from .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="Food Detector API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google Generative AI
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("Warning: GOOGLE_API_KEY not found in environment variables")

@app.get("/")
async def root():
    return {"message": "Food Detector API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/detect")
async def detect_food(file: UploadFile = File(...)):
    """
    Detect food in an uploaded image using Google's Gemini Vision API
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Prepare prompt
        prompt = "Identify all food items in this image. List each food item and describe it briefly."
        
        # Generate response
        response = model.generate_content([prompt, image])
        
        return {
            "status": "success",
            "filename": file.filename,
            "detected_foods": response.text
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
