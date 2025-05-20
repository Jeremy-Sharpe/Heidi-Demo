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
    # Use either uploaded file or text input
    content = ""
    if file:
        content = await file.read()
        content = content.decode("utf-8")
    elif text_content:
        content = text_content
    else:
        return {"error": "No ADIME content provided"}
    
    # Parse ADIME text to structured data
    adime_data = await parse_adime_text(content)
    
    # Generate images for action items
    image_paths = await generate_images(adime_data)
    
    # Combine data and render preview template
    context = {
        "request": request,
        "adime_data": adime_data,
        "image_paths": image_paths
    }
    return templates.TemplateResponse("report_template.html", context)

@app.post("/generate-pdf/")
async def create_pdf(request: Request, html_content: str = Form(...)):
    """Generate PDF from edited HTML content."""
    # Save PDF to static directory
    pdf_path = await generate_pdf(html_content)
    
    # Return PDF file for download
    filename = pdf_path.split("/")[-1]
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf"
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 