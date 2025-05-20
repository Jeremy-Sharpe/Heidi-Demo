import os
import uuid
import base64
from typing import Dict, Any, List, Optional
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IMAGE_DIR = "static/generated_images"

async def generate_images(adime_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate images for each action item in the intervention section.
    
    Args:
        adime_data: Structured ADIME data with action items
        
    Returns:
        List of dictionaries with action item and corresponding image path
    """
    # Create image directory if it doesn't exist
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Get action items from intervention section
    action_items = []
    
    # Check if we have the new structure with nested intervention
    if isinstance(adime_data.get("intervention"), dict) and "action_items" in adime_data["intervention"]:
        action_items = adime_data["intervention"]["action_items"]
    # Check if we have flat action_items list
    elif "action_items" in adime_data:
        action_items = adime_data["action_items"]
    
    # If no action items found, return empty list
    if not action_items:
        return []
    
    # Generate images for each action item (up to 3 to avoid rate limiting)
    image_tasks = []
    for item in action_items[:3]:  # Limit to 3 images
        if "visualization_prompt" in item:
            prompt = item["visualization_prompt"]
        else:
            prompt = f"Create a simple, clear infographic for a nutritional recommendation: {item['description'][:100]}"
        
        task = generate_image_for_action(item, prompt)
        image_tasks.append(task)
    
    # Wait for all image generation tasks to complete
    results = await asyncio.gather(*image_tasks, return_exceptions=True)
    
    # Filter out any exceptions and collect successful results
    image_info = []
    for result in results:
        if isinstance(result, dict) and "image_path" in result:
            image_info.append(result)
    
    return image_info

async def generate_image_for_action(action_item: Dict[str, str], prompt: str) -> Dict[str, str]:
    """
    Generate an image for a specific action item using OpenAI's DALL-E 3.
    
    Args:
        action_item: Action item dictionary with title and description
        prompt: Prompt to generate the image
        
    Returns:
        Dictionary with action item info and image path
    """
    # If no API key is available, return mock image path
    if not OPENAI_API_KEY:
        print("Warning: No OpenAI API key provided. Cannot generate images.")
        return {
            "title": action_item["title"],
            "description": action_item["description"],
            "image_path": "/static/generated_images/placeholder.png"
        }
    
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(IMAGE_DIR, filename)
        
        # Prepare the API request
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Enhanced prompt for better healthcare/nutrition infographics
        enhanced_prompt = f"""
        Create a professional, clear infographic illustration suitable for a dietitian's patient report. 
        The image should be:
        - Clean, minimalist design with simple icons
        - Use a soft color palette suitable for healthcare
        - Include a clear visual representation of the recommendation
        - No text overlay necessary (text will be added separately)
        - Appropriate for a medical/healthcare context
        
        The nutritional recommendation is:
        {prompt}
        """
        
        # Make the API request
        data = {
            "model": "dall-e-3",
            "prompt": enhanced_prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=60.0)
            response_data = response.json()
        
        # Save the image to disk
        if "data" in response_data and len(response_data["data"]) > 0:
            image_data = response_data["data"][0]["b64_json"]
            image_bytes = base64.b64decode(image_data)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            # Return information about the image
            return {
                "title": action_item["title"],
                "description": action_item["description"],
                "image_path": f"/static/generated_images/{filename}"
            }
        else:
            print(f"Error: No image data returned from OpenAI: {response_data}")
            return {
                "title": action_item["title"],
                "description": action_item["description"],
                "image_path": "/static/generated_images/placeholder.png"
            }
            
    except Exception as e:
        print(f"Error generating image: {e}")
        return {
            "title": action_item["title"],
            "description": action_item["description"],
            "image_path": "/static/generated_images/placeholder.png"
        } 