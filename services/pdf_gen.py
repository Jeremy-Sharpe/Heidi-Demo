import os
import uuid
import tempfile
from pathlib import Path
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from typing import Optional
import re
from datetime import datetime

# Set the directory for PDF storage
PDF_DIR = "static/pdfs"

# Create directory if it doesn't exist
os.makedirs(PDF_DIR, exist_ok=True)

async def generate_pdf(html_content: str) -> str:
    """
    Generate a PDF from HTML content.
    
    Args:
        html_content: HTML content to convert to PDF
        
    Returns:
        Path to the generated PDF file
    """
    # DEBUG: Print first 300 chars of HTML content
    print(f"DEBUG: HTML content length: {len(html_content)}")
    print(f"DEBUG: HTML content preview: {html_content[:300]}...")
    
    # DEBUG: Check for image tags in the HTML
    img_tags = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', html_content)
    print(f"DEBUG: Found {len(img_tags)} images in HTML:")
    for i, img in enumerate(img_tags[:5]):  # Print first 5 images
        print(f"DEBUG: Image {i}: {img}")
    
    # Fix image paths directly in the HTML content
    # This is a more direct approach than relying on base_url
    cwd = os.getcwd()
    for img_src in img_tags:
        if img_src.startswith('/'):
            # Convert /static/... to absolute file path
            rel_path = img_src[1:]  # Remove leading slash
            abs_path = os.path.join(cwd, rel_path)
            file_url = f"file://{abs_path}"
            # Replace in HTML
            html_content = html_content.replace(f'src="{img_src}"', f'src="{file_url}"')
            print(f"DEBUG: Replaced image path {img_src} with {file_url}")
    
    # Cleanup HTML - remove any empty or unnecessary elements
    # Remove buttons and other control elements that shouldn't be in the PDF
    html_content = re.sub(r'<button[^>]*>.*?</button>', '', html_content)
    
    # Remove any elements with display:none style
    html_content = re.sub(r'<[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>.*?</[^>]*>', '', html_content)
    
    # Remove empty editor divs (those with just <p><br></p> or similar)
    html_content = re.sub(r'<div[^>]*class="[^"]*editor[^"]*"[^>]*>\s*<p>\s*<br>\s*</p>\s*</div>', '', html_content)
    
    # Check if the replacement worked
    fixed_img_tags = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', html_content)
    print(f"DEBUG: After fixing, found {len(fixed_img_tags)} images in HTML:")
    for i, img in enumerate(fixed_img_tags[:5]):
        print(f"DEBUG: Fixed Image {i}: {img}")
    
    # Check if image files actually exist
    for i, img_src in enumerate(img_tags[:5]):
        # Handle both absolute URLs and paths
        if img_src.startswith('http'):
            print(f"DEBUG: Image {i} is a remote URL: {img_src}")
        else:
            # Extract path from the URL format if needed
            local_path = img_src
            if img_src.startswith('file://'):
                local_path = img_src[7:]
            elif img_src.startswith('http://localhost') or img_src.startswith('https://localhost'):
                local_path = re.sub(r'^https?://localhost(:\d+)?', '', img_src)
            
            # For absolute paths starting with /, make them relative to the current directory
            if local_path.startswith('/'):
                local_path = local_path[1:]  # Remove leading slash
                
            # Check if file exists
            if os.path.exists(local_path):
                print(f"DEBUG: Image {i} exists at path: {local_path}")
                # Get file size
                file_size = os.path.getsize(local_path)
                print(f"DEBUG: Image file size: {file_size} bytes")
            else:
                print(f"DEBUG: Image {i} DOES NOT EXIST at path: {local_path}")
                # Try to find the closest matching file
                dir_path = os.path.dirname(local_path) or '.'
                if os.path.exists(dir_path):
                    print(f"DEBUG: Directory exists: {dir_path}")
                    files = os.listdir(dir_path)
                    print(f"DEBUG: Files in directory: {files[:10]}")
                else:
                    print(f"DEBUG: Directory does not exist: {dir_path}")
    
    # Fix relative paths for images
    # Replace relative paths that don't start with http/https
    # First, get the absolute path of the current working directory
    cwd = os.getcwd()
    base_url = f"file://{cwd}/"
    print(f"DEBUG: Base URL for images: {base_url}")
    print(f"DEBUG: Current working directory: {cwd}")
    
    # Check for static directory
    if os.path.exists('static/generated_images'):
        print(f"DEBUG: Found static/generated_images directory")
        img_files = os.listdir('static/generated_images')
        print(f"DEBUG: Files in static/generated_images: {img_files[:10]}")
    else:
        print(f"DEBUG: static/generated_images directory NOT found")
    
    # Create a unique filename for the PDF
    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    
    try:
        # Save original HTML content to file for debugging
        debug_html_path = os.path.join(PDF_DIR, f"debug_{uuid.uuid4()}.html")
        with open(debug_html_path, 'w', encoding='utf-8') as debug_file:
            debug_file.write(html_content)
        print(f"DEBUG: Saved original HTML content to {debug_html_path} for inspection")
        
        # Write the HTML content to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
            temp.write(html_content.encode('utf-8'))
            temp_path = temp.name
        
        print(f"DEBUG: Wrote HTML to temporary file: {temp_path}")
        
        # Convert HTML to PDF with base URL to resolve relative paths
        html = HTML(filename=temp_path, base_url=base_url)
        print(f"DEBUG: Created HTML object for WeasyPrint with base_url: {base_url}")
        
        # Custom CSS for PDF rendering
        css = CSS(string="""
            @page {
                margin: 2cm 1.5cm;
                @top-center {
                    content: "ADIME Report";
                    font-size: 10pt;
                }
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10pt;
                }
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.5;
                color: #333;
                font-size: 11pt;
            }
            h1 {
                color: #2c3e50;
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 18pt;
            }
            h2.section-title {
                color: #2c3e50;
                font-size: 16pt;
                font-weight: bold;
                margin-bottom: 10px;
                margin-top: 25px;
            }
            .patient-info {
                margin-bottom: 20px;
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            .patient-info p {
                margin: 5px 0;
            }
            .data-label {
                font-weight: bold;
                display: inline-block;
                min-width: 200px;
            }
            .data-row {
                margin-bottom: 5px;
            }
            .subsection {
                margin-top: 15px;
                margin-bottom: 15px;
            }
            .subsection-title {
                font-weight: bold;
                margin-bottom: 8px;
            }
            img {
                max-width: 90%;
                height: auto;
                display: block;
                margin: 15px auto;
                border-radius: 5px;
            }
            .section {
                margin-bottom: 30px;
                page-break-inside: avoid;
            }
            /* Fix for empty editor containers */
            .editor {
                border: none !important;
                padding: 0 !important;
                min-height: 0 !important;
                margin-bottom: 10px;
                background-color: transparent !important;
            }
            .clean-content {
                margin-bottom: 10px;
            }
            /* Hide any elements that might be causing empty boxes */
            .ql-editor:empty, 
            .editor:empty, 
            div:empty {
                display: none !important;
                margin: 0 !important;
                padding: 0 !important;
                height: 0 !important;
            }
            
            /* Remove Quill editor-specific styling */
            .ql-container, .ql-editor {
                border: none !important;
                padding: 0 !important;
            }
            
            /* Style list elements */
            ul, ol {
                margin-top: 5px;
                margin-bottom: 10px;
                padding-left: 20px;
            }
            
            li {
                margin-bottom: 3px;
            }
            
            /* Hide any remaining UI controls */
            .add-field-btn, .remove-field-btn, .add-subsection-btn, .add-section-btn, .section-actions, .add-field-container {
                display: none !important;
            }
            
            /* Style custom fields */
            .custom-fields-patient p, 
            .custom-fields-demographics p,
            .custom-fields-dietary p,
            .custom-fields-diet p,
            .custom-fields-medical p,
            .custom-fields-nfpe p,
            .custom-fields-muscle p,
            .custom-fields-hydration p,
            .custom-fields-nutrition p,
            [class^="custom-fields-"] p {
                margin: 5px 0;
            }
            
            /* Style custom subsections */
            [id^="custom-subsections-"] .subsection {
                margin-top: 15px;
                margin-bottom: 15px;
            }
            
            /* Style custom sections */
            #custom-sections .section {
                margin-bottom: 30px;
            }
        """)
        
        print(f"DEBUG: About to generate PDF at {filepath}")
        
        # Generate the PDF
        html.write_pdf(filepath, stylesheets=[css])
        
        print(f"DEBUG: Successfully generated PDF at {filepath}")
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return filepath
    
    except Exception as e:
        print(f"ERROR generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a placeholder path
        return ""

def render_template_to_html(template_name: str, context: dict) -> str:
    """
    Render a Jinja2 template to HTML.
    
    Args:
        template_name: Name of the template file
        context: Dictionary of variables to pass to the template
        
    Returns:
        Rendered HTML content
    """
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template_name)
    
    # Add current datetime to context if not already present
    if 'now' not in context:
        context['now'] = datetime.now()
    
    # Render the template
    return template.render(**context) 