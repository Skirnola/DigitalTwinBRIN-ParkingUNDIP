from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import pickle
import cvzone
import time

# Load model
model = YOLO("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/B_best.pt")

# Load posisi slot parkir
with open("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

# Konfigurasi kamera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)}))
picam2.start()

# Ukuran box
yolo_box_width, yolo_box_height = 30, 40
opencv_box_width, opencv_box_height = 30, 40

def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.2)
    car_boxes = []

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            x1_new = x_center - (yolo_box_width // 2)
            y1_new = y_center - (yolo_box_height // 2)
            x2_new = x_center + (yolo_box_width // 2)
            y2_new = y_center + (yolo_box_height // 2)

            confidence = box.conf[0].item()
            class_id = int(box.cls[0].item())
            class_name = model.names[class_id]

            if confidence > 0.2 and 'car' in class_name.lower():
                car_boxes.append([x1_new, y1_new, x2_new, y2_new])
                cv2.rectangle(img, (x1_new, y1_new), (x2_new, y2_new), (255, 0, 0), 2)
                cv2.putText(img, class_name, (x1_new, y1_new - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    for id, x, y in posList:
        status = False
        for (cx1, cy1, cx2, cy2) in car_boxes:
            if x < cx2 and cx1 < x + opencv_box_width and y < cy2 and cy1 < y + opencv_box_height:
                status = True
                break

        color = (0, 0, 255) if status else (0, 255, 0)
        thickness = 3 if status else 5
        if not status:
            spaceCounter += 1

        cv2.rectangle(img, (x, y), (x + opencv_box_width, y + opencv_box_height), color, thickness)
        cvzone.putTextRect(img, str(id), (x + 5, y + 15), scale=0.5, thickness=1, offset=0, colorR=color)

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
    return img

# Main loop
while True:
    img = picam2.capture_array()
    imgResult = checkParkingSpaceYOLO(img, posList, model)
    cv2.imshow("Parking Detection", imgResult)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
