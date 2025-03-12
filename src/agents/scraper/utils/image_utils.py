"""Image processing utilities for the Lemon8 scraper."""

import os
import base64
from typing import Optional
from PIL import Image

def process_screenshot(
    screenshot_data: bytes | str,
    output_path: str,
    target_width: int = 1920,
    target_height: int = 1080,
) -> Optional[str]:
    """
    Process screenshot data to create a 16:9 aspect ratio image.
    
    Args:
        screenshot_data (Union[bytes, str]): Screenshot data (raw bytes or base64 string)
        output_path (str): Path where screenshot should be saved
        target_width (int, optional): Target width in pixels. Defaults to 1920.
        target_height (int, optional): Target height in pixels. Defaults to 1080.
        
    Returns:
        Optional[str]: Path to saved screenshot if successful, None if failed
        
    Process:
        1. Convert base64 to bytes if needed
        2. Save temporary image
        3. Resize to target width maintaining aspect ratio
        4. Crop to target height if needed
        5. Save optimized PNG
        6. Clean up temporary file
    """
    try:
        # Convert base64 to bytes if needed
        screenshot_bytes = (
            base64.b64decode(screenshot_data)
            if isinstance(screenshot_data, str)
            else screenshot_data
        )

        # Create temporary file path
        temp_path = f"{os.path.splitext(output_path)[0]}_temp.png"
        
        try:
            # Save original screenshot temporarily
            with open(temp_path, "wb") as f:
                f.write(screenshot_bytes)

            # Process with PIL
            with Image.open(temp_path) as img:
                # Calculate resize ratio to match target width
                ratio = target_width / img.width
                new_height = int(img.height * ratio)

                # Resize to target width
                img = img.resize(
                    (target_width, new_height),
                    Image.Resampling.LANCZOS
                )

                # Crop top portion to target height if needed
                if new_height > target_height:
                    img = img.crop((0, 0, target_width, target_height))

                # Save optimized PNG
                img.save(output_path, "PNG", optimize=True)

            return output_path

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        print(f"Error processing screenshot: {str(e)}")
        return None
