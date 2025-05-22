import os
import json
import re
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv

load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def parse_adime_text(content: str) -> Dict[str, Any]:
    """
    Parse any text into structured ADIME data using OpenAI's GPT-4.
    
    Args:
        content: Raw text content to be parsed
        
    Returns:
        Structured data dictionary with Assessment, Diagnosis, Intervention, and Monitoring sections
    """
    # Use OpenAI API for parsing
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required but not found in environment variables")
    
    try:
        # Process with OpenAI, regardless of input format
        structured_data = await parse_with_openai(content)
        return structured_data
    except Exception as e:
        print(f"Error using OpenAI API: {e}")
        # Return empty structure if parsing fails
        return {
            "assessment": {"summary": "Could not parse content", "weight": "", "labs": [], "current_intake": ""},
            "diagnosis": {"problems": [], "summary": "Could not parse content"},
            "intervention": {"summary": "Could not parse content", "short_term_goals": [], "long_term_goals": [], "action_items": []},
            "monitoring": {"follow_up": "Could not parse content", "metrics": [], "timeline": ""}
        }

async def parse_with_openai(content: str) -> Dict[str, Any]:
    """
    Use OpenAI's API to parse any text into structured ADIME data.
    
    Args:
        content: Raw text content
        
    Returns:
        Structured data dictionary
    """
    # Prepare the API request
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare the prompt
    prompt = f"""
    Parse the following text into a structured ADIME (Assessment, Diagnosis, Intervention, Monitoring/Evaluation) format.
    
    Analyze the content to identify key information that would fit into each ADIME category, even if the original text isn't explicitly structured this way.
    If the text is already in ADIME format, maintain that structure but extract data in a more structured way.
    
    TEXT TO PARSE:
    {content}
    
    Return a JSON object with the following structure, focusing on extracting EXACTLY what's in the text:
    {{
        "patient_info": {{
            "name": "Extract resident/patient name if present",
            "date": "Extract date if present",
            "time": "Extract time if present",
            "rd_name": "Extract dietitian name if present",
            "additional_fields": [] // Any other patient-related fields found that don't fit the above categories
        }},
        "assessment": {{
            // Extract ONLY fields that actually appear in the text, but use these common fields if they exist:
            "age": null,
            "gender": null,
            "weight": null,
            "height": null,
            "bmi": null,
            "ubw": null,
            "weight_history": null,
            "ibw": null,
            "appetite": null,
            "food_allergies": null,
            "food_preferences": null,
            "adaptive_devices": null,
            "diet_order": null,
            "meal_intake_percent": null,
            "supplement_order": null,
            "supplement_intake_percent": null,
            "chewing_swallowing": null,
            "feeding_assistance": null,
            "skin_condition": null,
            "medical_diagnosis": null,
            "labs": [],
            "medications": null,
            "nfpe_appearance": null,
            "nfpe_body_fat": null,
            "nfpe_orbital": null,
            "nfpe_triceps": null, 
            "nfpe_ribs_fat": null,
            "muscle_temple": null,
            "muscle_pectoralis": null,
            "muscle_delt": null,
            "muscle_hand": null,
            "muscle_back": null,
            "muscle_thigh": null,
            "hydration_status": null,
            "malnutrition_status": null,
            "calories_needs": null,
            "protein_needs": null,
            "fluid_needs": null,
            "needs_met": null,
            // Dynamic fields - detect any assessment-related fields not covered above
            "additional_fields": [
                // Example: {{"name": "Field Name", "value": "Field Value"}}
            ],
            // Group any additional assessment data by category if detected in the text
            "categories": [
                // Example: {{"name": "Category Name", "fields": [{{"name": "Field Name", "value": "Field Value"}}]}}
            ],
            "summary": "A concise summary of the patient's current health status"
        }},
        "diagnosis": {{
            "content": "The full nutrition diagnosis statement if present",
            "problems": ["List of nutrition problems mentioned in the text"],
            "goals": ["List of nutrition goals mentioned in the text"],
            "additional_fields": [
                // Example: {{"name": "Field Name", "value": "Field Value"}}
            ],
            "summary": "Summary of nutrition issues described in the text"
        }},
        "intervention": {{
            "content": "The full intervention section if present as text",
            "summary": "Summary of nutrition recommendations mentioned in the text",
            "short_term_goals": ["Short-term goals mentioned in the text"],
            "long_term_goals": ["Longer-term goals mentioned in the text"],
            "additional_fields": [
                // Example: {{"name": "Field Name", "value": "Field Value"}}
            ],
            "action_items": [
                {{ 
                    "title": "Title for a specific intervention mentioned in the text", 
                    "description": "Description of this intervention",
                    "visualization_prompt": "Create a simple, clear infographic that illustrates: [intervention from the text]"
                }}
            ]
        }},
        "monitoring": {{
            "content": "The full monitoring/evaluation section if present as text",
            "follow_up": "Follow-up plans mentioned in the text",
            "metrics": ["Metrics for measuring progress mentioned in the text"],
            "timeline": "Timeline for monitoring mentioned in the text",
            "additional_fields": [
                // Example: {{"name": "Field Name", "value": "Field Value"}}
            ]
        }},
        // Include any additional sections found in the text that don't fit into traditional ADIME
        "additional_sections": [
            // Example: {{"title": "Section Title", "content": "Section content"}}
        ]
    }}
    
    Important guidelines:
    1. Focus on extracting EXACTLY what's in the text, not generating new content
    2. If a field is not mentioned in the text, set it to null (for single values) or [] (for arrays)
    3. Include any detected fields not covered by the standard schema in the "additional_fields" arrays
    4. If you detect additional categories or sections, include them appropriately
    5. Preserve the exact terminology used in the source text
    """
    
    # Make the API request
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a clinical nutrition data extraction system that organizes health and nutrition text into structured ADIME data. You extract exactly what is mentioned in the text with minimal interpretation. Focus on capturing the full range of information in the text, including any unusual fields or sections that may not fit standard schemas. Always return null for fields not present rather than making assumptions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data, timeout=60.0)
        response_data = response.json()
    
    # Parse the response
    try:
        content = response_data["choices"][0]["message"]["content"]
        # Extract JSON from the response (in case there's any additional text)
        json_match = re.search(r"({.*})", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            result = json.loads(json_str)
            return result
        else:
            # If no JSON pattern found, try parsing the whole content
            return json.loads(content)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing OpenAI response: {e}")
        raise 