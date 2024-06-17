# image_processing.py
import os
import cv2
import subprocess
from inference_sdk import InferenceHTTPClient
from config import ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID, IMG_DIR

# Initialize the Roboflow InferenceHTTPClient
client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=ROBOFLOW_API_KEY
)

def capture_image():
    """
    Capture an image using the system's camera and save it to a predefined directory.
    """
    img_path = os.path.join(IMG_DIR, 'captured_image.jpg')
    capture_command = ['libcamera-still', '-o', img_path, '--timeout', '1000']
    subprocess.run(capture_command)
    if os.path.exists(img_path):
        print(f"Image captured and saved to {img_path}")
    else:
        print("Failed to capture image.")
    return img_path

def process_image(img_path):
    """
    Process the captured image to prepare it for classification.
    """
    print(f"Processing image: {img_path}")
    if not os.path.exists(img_path):
        print(f"Image path does not exist: {img_path}")
        return None

    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image from path: {img_path}")
        return None

    # Define the coordinates for the crop area based on the rectangle in the wooden platform
    top_left_x = 600
    top_left_y = 0
    bottom_right_x = 1900
    bottom_right_y = 1900

    # Crop the image to the specified area
    cropped_img = img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]

    # Save the cropped image for verification
    cropped_img_path = os.path.join(IMG_DIR, 'cropped_image.jpg')
    cv2.imwrite(cropped_img_path, cropped_img)
    print(f"Cropped image saved to {cropped_img_path}")

    return cropped_img_path

def classify_cropped_object(cropped_img_path):
    """
    Classify the cropped image using the Roboflow API.
    """
    print(f"Classifying cropped image: {cropped_img_path}")
    if not os.path.exists(cropped_img_path):
        print(f"Cropped image path does not exist: {cropped_img_path}")
        return None, None

    # Use the client to infer the image
    try:
        result = client.infer(cropped_img_path, model_id=ROBOFLOW_MODEL_ID)

        if 'predictions' in result and result['predictions']:
            predicted_class = result['predictions'][0]['class']
            confidence = result['predictions'][0]['confidence']
            return predicted_class, confidence
        else:
            print("No predictions found in the response.")
            return None, None
    except Exception as e:
        print(f"Error in classification: {e}")
        return None, None
