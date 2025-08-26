# from picamera2 import Picamera2
# from ultralytics import YOLO
# import cv2
# import pickle
# import cvzone
# import time

# # Load model
# model = YOLO("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/B_best.pt")

# # Load posisi slot parkir
# with open("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
#     posList = pickle.load(f)

# # Konfigurasi kamera
# picam2 = Picamera2()
# picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)}))
# picam2.start()


# # Ukuran box
# yolo_box_width, yolo_box_height = 50, 60
# opencv_box_width, opencv_box_height = 50, 60

# def checkParkingSpaceYOLO(img, posList, model):
#     spaceCounter = 0
#     results = model(img, conf=0.1)
#     car_boxes = []

#     for result in results:
#         for box in result.boxes:
#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#             x_center = (x1 + x2) // 2
#             y_center = (y1 + y2) // 2
#             x1_new = x_center - (yolo_box_width // 2)
#             y1_new = y_center - (yolo_box_height // 2)
#             x2_new = x_center + (yolo_box_width // 2)
#             y2_new = y_center + (yolo_box_height // 2)

#             confidence = box.conf[0].item()
#             class_id = int(box.cls[0].item())
#             class_name = model.names[class_id]

#             if confidence > 0.1 and 'car' in class_name.lower():
#                 car_boxes.append([x1_new, y1_new, x2_new, y2_new])
#                 cv2.rectangle(img, (x1_new, y1_new), (x2_new, y2_new), (255, 0, 0), 2)
#                 cv2.putText(img, class_name, (x1_new, y1_new - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

#     for id, x, y in posList:
#         status = False
#         for (cx1, cy1, cx2, cy2) in car_boxes:
#             if x < cx2 and cx1 < x + opencv_box_width and y < cy2 and cy1 < y + opencv_box_height:
#                 status = True
#                 break

#         color = (0, 0, 255) if status else (0, 255, 0)
#         thickness = 3 if status else 5
#         if not status:
#             spaceCounter += 1

#         cv2.rectangle(img, (x, y), (x + opencv_box_width, y + opencv_box_height), color, thickness)
#         cvzone.putTextRect(img, str(id), (x + 5, y + 15), scale=0.5, thickness=1, offset=0, colorR=color)

#     cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
#     return img

# # Main loop
# while True:
#     img = picam2.capture_array()
#     imgResult = checkParkingSpaceYOLO(img, posList, model)
#     cv2.imshow("Parking Detection", imgResult)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# picam2.stop()
# cv2.destroyAllWindows()

from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import pickle
import cvzone
import numpy as np
import skfuzzy as fuzz

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
yolo_box_width, yolo_box_height = 50, 60
opencv_box_width, opencv_box_height = 50, 60


def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.1)
    car_boxes, car_areas, centroids = [], [], []

    # === Deteksi mobil dengan YOLO
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

            if confidence > 0.1 and 'car' in class_name.lower():
                w, h = x2_new - x1_new, y2_new - y1_new
                area = w * h
                car_boxes.append([x1_new, y1_new, x2_new, y2_new])
                car_areas.append(area)
                centroids.append(((x1_new + x2_new) // 2, (y1_new + y2_new) // 2))

    # === Fuzzy C-means clustering (Small, Medium, Big) ===
    labels, colors = [], []
    if len(car_areas) >= 3:
        data = np.array(car_areas).reshape(1, -1)
        cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(
            data, c=3, m=2, error=0.005, maxiter=1000
        )
        cluster = np.argmax(u, axis=0)
        
        # Urutkan cluster berdasarkan luas (kecil -> besar)
        order = np.argsort(cntr[:, 0])  
        label_map = {
            order[0]: "Small",
            order[1]: "Medium",
            order[2]: "Big"
        }

        for i, (cx, cy) in enumerate(centroids):
            ukuran = label_map[cluster[i]]
            if ukuran == "Small":
                color = (0, 255, 0)   # Hijau
            elif ukuran == "Medium":
                color = (0, 255, 255) # Kuning
            else:
                color = (255, 0, 0)   # Biru

            colors.append(color)
            cv2.putText(img, ukuran, (cx - 40, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        # Kalau mobil < 3, pakai label default
        for cx, cy in centroids:
            colors.append((200, 200, 200))
            cv2.putText(img, "Mobil", (cx - 30, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Gambar box mobil
    for i, (x1, y1, x2, y2) in enumerate(car_boxes):
        color = colors[i] if i < len(colors) else (255, 0, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

    # === Check parking slot occupancy
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

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}',
                       (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
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
