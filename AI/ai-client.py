import socket
import time
import cv2
from ultralytics import YOLO

# Load model
model = YOLO('AI/yolo_finetuned.pt')

def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image {image_path}")
        return None, None

    predictions = model.predict(source=image_path, save=False)

    if len(predictions) == 0 or len(predictions[0].boxes) == 0:
        return None, None

    boxes = predictions[0].boxes.xyxy  
    confs = predictions[0].boxes.conf  
    cls = predictions[0].boxes.cls  

    classifications = []
    accuracies = []

    for i in range(len(boxes)):
        label = model.names[int(cls[i])]
        confidence = confs[i]
        classifications.append(label)
        accuracies.append(confidence)

    if classifications and accuracies:
        max_confidence_index = accuracies.index(max(accuracies))
        material_type = classifications[max_confidence_index]
        accuracy = accuracies[max_confidence_index]
        return material_type, accuracy

    return None, None

def main():
    server_ip = '172.30.252.204'  # Change this to the IP address of your Raspberry Pi
    server_port = 65432

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    print("Connected to the server")

    try:
        while True:
            # Replace this with the path to your test image
            image_path = 'AI/testphotos/test6.png'
            material_type, accuracy = process_image(image_path)

            if material_type and accuracy is not None:
                data = f"{material_type},{accuracy:.2f}"
                client_socket.sendall(data.encode())
                print(f"Sent data: {data}")

            time.sleep(5)  # Delay between sending data
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
