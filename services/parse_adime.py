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
    Parse ADIME note text into structured data using OpenAI's GPT-4.
    
    Args:
        content: Raw ADIME note text
        
    Returns:
        Structured data dictionary with Assessment, Diagnosis, Intervention, and Monitoring sections
    """
    # Basic rule-based parsing as fallback
    sections = {
        "assessment": "",
        "diagnosis": "",
        "intervention": "",
        "monitoring": "",
        "action_items": []
    }
    
    # Simple rule-based parsing (can be enhanced with regex patterns)
    if "ASSESSMENT" in content.upper():
        assessment_match = re.search(r"(?i)ASSESSMENT[:\s]+(.*?)(?:DIAGNOSIS|INTERVENTION|MONITORING|$)", 
                                    content, re.DOTALL)
        if assessment_match:
            sections["assessment"] = assessment_match.group(1).strip()
    
    if "DIAGNOSIS" in content.upper():
        diagnosis_match = re.search(r"(?i)DIAGNOSIS[:\s]+(.*?)(?:ASSESSMENT|INTERVENTION|MONITORING|$)", 
                                   content, re.DOTALL)
        if diagnosis_match:
            sections["diagnosis"] = diagnosis_match.group(1).strip()
    
    if "INTERVENTION" in content.upper():
        intervention_match = re.search(r"(?i)INTERVENTION[:\s]+(.*?)(?:ASSESSMENT|DIAGNOSIS|MONITORING|$)", 
                                      content, re.DOTALL)
        if intervention_match:
            sections["intervention"] = intervention_match.group(1).strip()
    
    if "MONITORING" in content.upper():
        monitoring_match = re.search(r"(?i)MONITORING[:\s]+(.*?)(?:ASSESSMENT|DIAGNOSIS|INTERVENTION|$)", 
                                    content, re.DOTALL)
        if monitoring_match:
            sections["monitoring"] = monitoring_match.group(1).strip()
    
    # If OpenAI API key is available, use GPT for more accurate parsing
    if OPENAI_API_KEY:
        try:
            # Use OpenAI's API for more sophisticated parsing
            structured_data = await parse_with_openai(content)
            return structured_data
        except Exception as e:
            print(f"Error using OpenAI API: {e}")
            # Fall back to rule-based parsing
            print("Falling back to rule-based parsing")
    
    # Extract action items from the intervention section
    action_items = extract_action_items(sections["intervention"])
    sections["action_items"] = action_items
    
    return sections

async def parse_with_openai(content: str) -> Dict[str, Any]:
    """
    Use OpenAI's API to parse ADIME content into structured data.
    
    Args:
        content: Raw ADIME note text
        
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
    Parse the following ADIME (Assessment, Diagnosis, Intervention, Monitoring/Evaluation) note into structured JSON.
    Extract key information for each section, and especially identify clear action items from the Intervention section 
    that we could visualize.
    
    ADIME NOTE:
    {content}
    
    Return ONLY a JSON object with the following structure:
    {{
        "assessment": {{
            "summary": "Brief summary of patient assessment",
            "weight": "patient weight if mentioned",
            "labs": ["relevant lab results"],
            "current_intake": "description of current diet/intake"
        }},
        "diagnosis": {{
            "problems": ["list of identified problems"],
            "summary": "summary of diagnosis"
        }},
        "intervention": {{
            "summary": "summary of intervention plan",
            "action_items": [
                {{ 
                    "title": "clear action item title", 
                    "description": "detailed explanation",
                    "visualization_prompt": "detailed prompt to generate an image for this action item"
                }}
            ]
        }},
        "monitoring": {{
            "follow_up": "follow up plan",
            "metrics": ["metrics to monitor"],
            "timeline": "timeline for monitoring"
        }}
    }}
    """
    
    # Make the API request
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a dietitian's assistant that specializes in parsing ADIME notes into structured data."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
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
        # Return a basic structure if parsing fails
        return {
            "assessment": {"summary": "Could not parse assessment"},
            "diagnosis": {"problems": [], "summary": "Could not parse diagnosis"},
            "intervention": {"summary": "Could not parse intervention", "action_items": []},
            "monitoring": {"follow_up": "Could not parse monitoring", "metrics": []}
        }

def extract_action_items(intervention_text: str) -> List[Dict[str, str]]:
    """
    Extract action items from intervention text.
    
    Args:
        intervention_text: Text from intervention section
        
    Returns:
        List of action items with title and description
    """
    action_items = []
    
    # Simple rule-based extraction - look for numbered or bulleted items
    bullet_points = re.findall(r"(?:\d+\.|•|\*)\s*(.*?)(?=(?:\d+\.|•|\*)|$)", intervention_text, re.DOTALL)
    
    for point in bullet_points:
        point = point.strip()
        if point:
            # Create a simple title from the first few words
            words = point.split()
            title = " ".join(words[:4]) + ("..." if len(words) > 4 else "")
            
            action_items.append({
                "title": title,
                "description": point,
                "visualization_prompt": f"Create a simple, clear infographic for a nutritional recommendation: {point}"
            })
    
    # If no bullet points were found, try to create action items from paragraphs
    if not action_items and intervention_text:
        paragraphs = intervention_text.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:  # Only substantial paragraphs
                words = para.split()
                title = " ".join(words[:4]) + ("..." if len(words) > 4 else "")
                
                action_items.append({
                    "title": title,
                    "description": para,
                    "visualization_prompt": f"Create a simple, clear infographic for a nutritional recommendation: {para[:100]}"
                })
    
    return action_items 