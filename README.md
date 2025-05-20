# ADIME Note Processor

This application processes ADIME (Assessment, Diagnosis, Intervention, Monitoring/Evaluation) notes for dietitians, generating visual reports with AI-generated images.

## Features

- Upload or paste ADIME notes
- Parse text into structured data
- Generate AI images for action plan items
- Create editable HTML previews
- Export as PDF

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd adime-note-processor
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy the example environment file and add your OpenAI API key:

```bash
cp example.env .env
```

Then edit the `.env` file to add your OpenAI API key:

```
OPENAI_API_KEY=your_actual_openai_api_key
```

## Running the Application

Start the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The application will be available at: http://localhost:8000

## Usage

1. **Upload ADIME Note**: Use the web interface to upload a text file or paste ADIME note content
2. **Review & Edit**: The system will parse the note, generate images, and provide an editable preview
3. **Export to PDF**: Download the final report as a PDF

## Structure

- `main.py`: FastAPI application entry point
- `services/`: Core functionality modules
  - `parse_adime.py`: Process ADIME text into structured data
  - `image_gen.py`: Generate images using OpenAI
  - `pdf_gen.py`: Convert HTML to PDF
- `templates/`: HTML templates
- `static/`: Static assets and generated files
- `models.py`: Pydantic data models

## Requirements

- Python 3.8+
- FastAPI
- OpenAI API key
- WeasyPrint (for PDF generation)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 