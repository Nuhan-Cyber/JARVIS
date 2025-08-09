# jarvis-ai/src/tools/qr_code_generator.py

import os
import sys
import qrcode
from PIL import Image
from datetime import datetime

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import settings

def generate_qr_code(data: str, file_name: str = None) -> str:
    """
    Generates a QR code from the given data, saves it as an image, and returns the file path.

    Args:
        data (str): The text or URL to encode in the QR code.
        file_name (str, optional): The desired name for the output file (without extension). 
                                   If None, a timestamp-based name is generated.

    Returns:
        str: The absolute path to the saved QR code image file.
             Returns an error string if generation fails.
    """
    if not data:
        return "Error: No data provided for QR code generation."

    # Ensure the download directory exists
    output_dir = settings.IMAGE_DOWNLOAD_PATH
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename if not provided
    if not file_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"qr_code_{timestamp}"
    
    file_path = os.path.join(output_dir, f"{file_name}.png")

    try:
        print(f"Generating QR code for data: '{data[:50]}...'")
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add data and generate the image
        qr.add_data(data)
        qr.make(fit=True)

        # Create an image from the QR Code instance
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image
        img.save(file_path)
        
        print(f"QR Code successfully generated and saved to: {file_path}")
        return file_path

    except Exception as e:
        error_message = f"Error generating QR code: {e}"
        print(error_message)
        return error_message

if __name__ == '__main__':
    # --- Test Cases ---
    print("--- Testing QR Code Generator ---")
    
    # Test case 1: Simple URL
    print("\n1. Generating QR code for a URL...")
    test_data_1 = "https://github.com/Nuhan-Cyber"
    path_1 = generate_qr_code(test_data_1, "github_profile_qr")
    if "Error:" not in path_1:
        print(f"   Success! Saved at: {path_1}")
        # Open the image for verification
        Image.open(path_1).show()