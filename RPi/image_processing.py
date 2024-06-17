import os
import cv2
import numpy as np
from ultralytics import YOLO
import config
import subprocess

# Load the YOLO model
yolo_model = YOLO(config.yolo_model_path)

def capture_image(img_dir):
    """Captures an image using libcamera-still and saves it to the specified directory."""
    img_path = os.path.join(img_dir, 'captured_image.jpg')
    capture_command = ['libcamera-still', '-o', img_path, '--timeout', '1000']
    subprocess.run(capture_command)
    if not os.path.exists(img_path):
        print("Failed to capture image.")
    return img_path

def crop_image(img_path):
    """Crops the image to the specified area."""
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image from path: {img_path}")
        return None

    cropped_img = img[config.top_left_y:config.bottom_right_y, config.top_left_x:config.bottom_right_x]
    cropped_img_path = os.path.join(os.path.dirname(img_path), 'cropped_image.jpg')
    cv2.imwrite(cropped_img_path, cropped_img)
    return cropped_img_path

def process_image(img_path):
    """Processes the image with YOLO and returns the cropped detected object's path, label, and confidence."""
    cropped_img_path = crop_image(img_path)
    if not cropped_img_path:
        return None, None, None

    cropped_img = cv2.imread(cropped_img_path)
    predictions = yolo_model.predict(source=cropped_img, save=False)

    if not predictions or not predictions[0].boxes:
        return None, None, None

    boxes = predictions[0].boxes.xyxy
    confs = predictions[0].boxes.conf
    cls = predictions[0].boxes.cls

    max_confidence_index = np.argmax(confs)
    box = boxes[max_confidence_index]
    confidence = confs[max_confidence_index]
    label = yolo_model.names[int(cls[max_confidence_index])]

    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(cropped_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(cropped_img, f"{label} {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    output_img_path = os.path.join(os.path.dirname(img_path), 'processed_image_with_boxes.jpg')
    cv2.imwrite(output_img_path, cropped_img)
    
    # Further crop to the detected object's bounding box if needed
    detected_obj_img = cropped_img[y1:y2, x1:x2]
    detected_obj_img_path = os.path.join(os.path.dirname(img_path), 'cropped_detected_image.png')
    cv2.imwrite(detected_obj_img_path, detected_obj_img)

    return detected_obj_img_path, label, confidence
