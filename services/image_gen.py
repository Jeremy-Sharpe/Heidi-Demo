import os
import uuid
import base64
import random
import glob
from typing import Dict, Any, List, Optional
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Check if DEV_MODE is enabled (default to True if not specified)
DEV_MODE = os.getenv("DEV_MODE", "True").lower() in ("true", "1", "t", "yes")
IMAGE_DIR = "static/generated_images"

# Create image directory if it doesn't exist
os.makedirs(IMAGE_DIR, exist_ok=True)

# Add a placeholder image if none exists
def ensure_placeholder_images_exist():
    """Create placeholder images if they don't exist already."""
    placeholder_path = os.path.join(IMAGE_DIR, "placeholder.png")
    if not os.path.exists(placeholder_path):
        print(f"DEBUG: Creating placeholder image at {placeholder_path}")
        try:
            # Create a simple placeholder image using any available library
            # For this example, we'll just copy an existing image if available
            existing_images = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
            if existing_images:
                # Use an existing image as placeholder
                import shutil
                shutil.copy(existing_images[0], placeholder_path)
                print(f"DEBUG: Copied existing image as placeholder")
            else:
                # Create a basic colored rectangle if no images available
                try:
                    from PIL import Image, ImageDraw
                    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
                    d = ImageDraw.Draw(img)
                    d.rectangle([(200, 150), (600, 450)], fill=(128, 200, 255))
                    img.save(placeholder_path)
                    print(f"DEBUG: Created new placeholder image with PIL")
                except ImportError:
                    # If PIL is not available, just create an empty file
                    with open(placeholder_path, 'wb') as f:
                        f.write(b'')
                    print(f"DEBUG: Created empty placeholder file (PIL not available)")
        except Exception as e:
            print(f"DEBUG: Error creating placeholder: {str(e)}")

# Ensure placeholders exist on module load
ensure_placeholder_images_exist()

async def generate_images(adime_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate images for each action item in the intervention section.
    
    Args:
        adime_data: Structured ADIME data with action items
        
    Returns:
        List of dictionaries with action item and corresponding image path
    """
    print(f"DEBUG: Received ADIME data structure: {type(adime_data)}")
    print(f"DEBUG: ADIME data keys: {adime_data.keys()}")
    
    # Get action items from intervention section
    action_items = []
    
    # Check if we have the new structure with nested intervention
    if isinstance(adime_data.get("intervention"), dict) and "action_items" in adime_data["intervention"]:
        action_items = adime_data["intervention"]["action_items"]
        print(f"DEBUG: Found action_items inside intervention dict")
    # Check if we have flat action_items list
    elif "action_items" in adime_data:
        action_items = adime_data["action_items"]
        print(f"DEBUG: Found action_items at top level")
    
    print(f"DEBUG: Number of action items found: {len(action_items)}")
    
    # If no action items found, return empty list
    if not action_items:
        print("DEBUG: No action items found to generate images for")
        return []
    
    # Check if we're in DEV MODE - if so, use existing images or placeholders
    if DEV_MODE:
        print("DEBUG: Running in DEV_MODE - using existing images or placeholders instead of calling API")
        return await generate_dev_images_for_action_items(action_items)
    
    # Generate images for each action item (up to 3 to avoid rate limiting)
    image_tasks = []
    for i, item in enumerate(action_items[:3]):  # Limit to 3 images
        print(f"DEBUG: Processing action item {i}: {item.get('title', 'No title')}")
        if "visualization_prompt" in item:
            prompt = item["visualization_prompt"]
            print(f"DEBUG: Using visualization_prompt")
        else:
            prompt = f"Create a simple, clear infographic for a personal nutritional goal with first-person perspective (I should, I will): {item['description'][:100]}"
            print(f"DEBUG: Generated default prompt")
        
        task = generate_image_for_action(item, prompt)
        image_tasks.append(task)
    
    # Wait for all image generation tasks to complete
    results = await asyncio.gather(*image_tasks, return_exceptions=True)
    
    # Filter out any exceptions and collect successful results
    image_info = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"DEBUG: Error generating image {i}: {str(result)}")
        elif isinstance(result, dict) and "image_path" in result:
            print(f"DEBUG: Successfully generated image {i}: {result['image_path']}")
            image_info.append(result)
    
    print(f"DEBUG: Returning {len(image_info)} image info items")
    return image_info

async def generate_dev_images_for_action_items(action_items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate placeholder images for action items in dev mode.
    Either reuses existing images or uses placeholder images.
    
    Args:
        action_items: List of action item dictionaries
        
    Returns:
        List of dictionaries with action item info and image path
    """
    image_info = []
    
    # Get list of existing images
    existing_images = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
    existing_images = [img for img in existing_images if "placeholder" not in img]
    print(f"DEBUG: Found {len(existing_images)} existing images to reuse")
    
    # If no existing images (other than placeholder), ensure placeholder exists
    if not existing_images:
        ensure_placeholder_images_exist()
        placeholder_path = os.path.join(IMAGE_DIR, "placeholder.png")
        if os.path.exists(placeholder_path):
            existing_images = [placeholder_path]
    
    # Process each action item
    for i, item in enumerate(action_items[:3]):  # Limit to 3 items
        # Either reuse existing image or use placeholder
        if existing_images:
            # Pick a random existing image
            img_path = random.choice(existing_images)
            filename = os.path.basename(img_path)
            image_path = f"/static/generated_images/{filename}"
            print(f"DEBUG: Reusing existing image for action item {i}: {image_path}")
        else:
            # Use placeholder as fallback
            image_path = "/static/generated_images/placeholder.png"
            print(f"DEBUG: Using placeholder image for action item {i}")
        
        # Add to result
        image_info.append({
            "title": item["title"],
            "description": item["description"],
            "image_path": image_path
        })
    
    return image_info

async def generate_image_for_action(action_item: Dict[str, str], prompt: str) -> Dict[str, str]:
    """
    Generate an image for a specific action item using OpenAI's image generation API.
    
    Args:
        action_item: Action item dictionary with title and description
        prompt: Prompt to generate the image
        
    Returns:
        Dictionary with action item info and image path
    """
    # If no API key is available, return mock image path
    if not OPENAI_API_KEY:
        print("DEBUG: No OpenAI API key provided. Cannot generate images.")
        return {
            "title": action_item["title"],
            "description": action_item["description"],
            "image_path": "/static/generated_images/placeholder.png"
        }
    
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(IMAGE_DIR, filename)
        
        print(f"DEBUG: Will save image to {filepath}")
        
        # Prepare the API request
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Enhanced prompt for better healthcare/nutrition infographics
        enhanced_prompt = f"""
        Create a professional, clear infographic illustration for the specific nutrition recommendation below.
        The image should:
        - Show actual examples of the recommended foods/meals based solely on the recommendation context
        - Use a soft color palette suitable for healthcare
        - Be visually specific to the exact recommendation, not generic
        - Include realistic food portions and combinations relevant to the health context
        - Have a clean, minimalist design focused on the recommended foods
        - No text overlay necessary (text will be added separately)
        - Designed from the patient's perspective (what "I" should eat/do)
        - Be specific to the patient's health context
        
        The specific nutritional recommendation is:
        {prompt}
        """
        
        print(f"DEBUG: Sending request to OpenAI image generation API")
        
        # Make the API request with updated parameters
        data = {
            "model": "gpt-image-1",
            "prompt": enhanced_prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "high",
            "background": "opaque",
            "output_format": "png"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=60.0)
            response_data = response.json()
        
        print(f"DEBUG: Received response from OpenAI API")
        
        # Handle the response based on what's available
        if "data" in response_data and len(response_data["data"]) > 0:
            # For gpt-image-1 model which always returns base64-encoded images
            if "b64_json" in response_data["data"][0]:
                image_data = response_data["data"][0]["b64_json"]
                image_bytes = base64.b64decode(image_data)
            # Handle URL response format
            elif "url" in response_data["data"][0]:
                # Download the image from the provided URL
                image_url = response_data["data"][0]["url"]
                print(f"DEBUG: Downloading image from URL: {image_url}")
                async with httpx.AsyncClient() as client:
                    img_response = await client.get(image_url)
                    image_bytes = img_response.content
            else:
                print(f"DEBUG: Unexpected response format: {response_data}")
                return {
                    "title": action_item["title"],
                    "description": action_item["description"],
                    "image_path": "/static/generated_images/placeholder.png"
                }
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            print(f"DEBUG: Successfully saved image to {filepath}")
            
            # Return information about the image
            image_path = f"/static/generated_images/{filename}"
            print(f"DEBUG: Returning image path: {image_path}")
            
            return {
                "title": action_item["title"],
                "description": action_item["description"],
                "image_path": image_path
            }
        else:
            print(f"DEBUG: No image data in OpenAI response. Response data: {response_data}")
            return {
                "title": action_item["title"],
                "description": action_item["description"],
                "image_path": "/static/generated_images/placeholder.png"
            }
            
    except Exception as e:
        print(f"DEBUG: Exception in image generation: {str(e)}")
        return {
            "title": action_item["title"],
            "description": action_item["description"],
            "image_path": "/static/generated_images/placeholder.png"
        } 