import os
import uuid
import tempfile
from pathlib import Path
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from typing import Optional

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
    # Create a unique filename for the PDF
    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    
    try:
        # Write the HTML content to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
            temp.write(html_content.encode('utf-8'))
            temp_path = temp.name
        
        # Convert HTML to PDF
        html = HTML(filename=temp_path)
        
        # Custom CSS for PDF rendering
        css = CSS(string="""
            @page {
                margin: 1cm;
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
            }
            h1 {
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            h2 {
                color: #3498db;
                margin-top: 20px;
            }
            img {
                max-width: 90%;
                height: auto;
                display: block;
                margin: 15px auto;
                border-radius: 5px;
            }
            .action-item {
                background-color: #f9f9f9;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #3498db;
                border-radius: 3px;
            }
            .section {
                margin-bottom: 30px;
            }
        """)
        
        # Generate the PDF
        html.write_pdf(filepath, stylesheets=[css])
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return filepath
    
    except Exception as e:
        print(f"Error generating PDF: {e}")
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
    
    # Render the template
    return template.render(**context) 