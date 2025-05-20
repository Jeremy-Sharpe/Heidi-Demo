import os
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Import services
from services.parse_adime import parse_adime_text
from services.image_gen import generate_images
from services.pdf_gen import generate_pdf

# Load environment variables
load_dotenv()

# Development Mode
# The app checks for DEV_MODE in the environment variables (default: True)
# When DEV_MODE is True, the image generator uses placeholders or existing images
# instead of making expensive API calls
# To use real image generation, set DEV_MODE=False in your .env file
DEV_MODE = os.getenv("DEV_MODE", "True").lower() in ("true", "1", "t", "yes")
if DEV_MODE:
    print("\n-------------------- RUNNING IN DEVELOPMENT MODE --------------------")
    print("Image generation will use placeholders or reuse existing images.")
    print("To use real image generation, set DEV_MODE=False in your .env file.")
    print("----------------------------------------------------------------------\n")

# Create directories if they don't exist
Path("static/generated_images").mkdir(parents=True, exist_ok=True)
Path("static/pdfs").mkdir(parents=True, exist_ok=True)

# Initialize FastAPI
app = FastAPI(title="ADIME Note Processor")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Render the upload form."""
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/upload-adime/")
async def upload_adime(request: Request, 
                     file: UploadFile = File(None),
                     text_content: str = Form(None)):
    """Process uploaded ADIME content and create editable preview."""
    print("\nDEBUG: Processing upload-adime request")
    
    # Use either uploaded file or text input
    content = ""
    if file:
        content = await file.read()
        content = content.decode("utf-8")
        print(f"DEBUG: Received content from file upload, length: {len(content)}")
    elif text_content:
        content = text_content
        print(f"DEBUG: Received content from text input, length: {len(content)}")
    else:
        print("DEBUG: No ADIME content provided")
        return {"error": "No ADIME content provided"}
    
    # Parse ADIME text to structured data
    print("DEBUG: Calling parse_adime_text")
    adime_data = await parse_adime_text(content)
    print(f"DEBUG: Received parsed ADIME data with keys: {adime_data.keys()}")
    
    # Generate images for action items
    print("DEBUG: Calling generate_images")
    image_paths = await generate_images(adime_data)
    print(f"DEBUG: Received {len(image_paths)} image paths from generate_images")
    
    # Combine data and render preview template
    context = {
        "request": request,
        "adime_data": adime_data,
        "image_paths": image_paths
    }
    
    print("DEBUG: Rendering report_template.html")
    return templates.TemplateResponse("report_template.html", context)

@app.post("/generate-pdf/")
async def create_pdf(request: Request, html_content: str = Form(...)):
    """Generate PDF from edited HTML content."""
    print("\nDEBUG: Processing generate-pdf request")
    print(f"DEBUG: Received HTML content length: {len(html_content)}")
    
    # Save PDF to static directory
    print("DEBUG: Calling generate_pdf")
    pdf_path = await generate_pdf(html_content)
    
    if not pdf_path:
        print("DEBUG: No PDF path returned from generate_pdf")
        return {"error": "Failed to generate PDF"}
    
    # Return PDF file for download
    filename = pdf_path.split("/")[-1]
    print(f"DEBUG: Returning PDF file: {filename}, path: {pdf_path}")
    
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf"
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 