import os
import cv2
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

roboflow_api_url = os.getenv("ROBOFLOW_API_URL")
roboflow_api_key = os.getenv("ROBOFLOW_API_KEY")
roboflow_model_id = os.getenv("ROBOFLOW_MODEL_ID")

def classify_cropped_object(cropped_img_path):
    """Classifies the cropped image using Roboflow."""
    if not os.path.exists(cropped_img_path):
        print(f"Cropped image path does not exist: {cropped_img_path}")
        return None, None

    img = cv2.imread(cropped_img_path)
    if img is None:
        print(f"Failed to load cropped image from path: {cropped_img_path}")
        return None, None

    _, img_encoded = cv2.imencode('.jpg', img)
    files = {
        'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')
    }

    url = f"{roboflow_api_url}/{roboflow_model_id}?api_key={roboflow_api_key}"
    response = requests.post(url, files=files)

    if response.status_code == 200:
        classification_result = response.json()
        if 'predictions' in classification_result and classification_result['predictions']:
            predicted_class = classification_result['predictions'][0]['class']
            confidence = classification_result['predictions'][0]['confidence']
            return predicted_class, confidence
        else:
            print("No predictions found in the response.")
    else:
        print(f"Error in classification: {response.status_code}, {response.text}")
    return None, None
