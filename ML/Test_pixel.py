from ultralytics import YOLO
import cv2
import pickle
import cvzone
import time
from datetime import datetime
import skfuzzy as fuzz
import numpy as np

# === Load YOLO model & parking positions
model = YOLO("D:/Digital twin BRIN RI/Digital-Twin-Brin-Parking/ML/B_best.pt")
with open("D:/Digital twin BRIN RI/Digital-Twin-Brin-Parking/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

# === Parameters
yolo_box_width, yolo_box_height = 30, 40
opencv_box_width, opencv_box_height = 30, 40

# === Camera Setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cv2.namedWindow("Parking Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Parking Detection", 1280, 720)

# === Enhance image: Brightness, Contrast, Saturation
def enhance_image(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    s = cv2.add(s, 10)
    v = cv2.add(v, 10)

    s = np.clip(s, 0, 255)
    v = np.clip(v, 0, 255)

    final_hsv = cv2.merge((h, s, v))
    return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

# === Detection Logic
def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.3)
    car_boxes, car_areas, centroids = [], [], []

    for result in results:
        if hasattr(result, 'masks') and result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            for mask in masks:
                binary_mask = (mask * 255).astype(np.uint8)
                binary_mask_resized = cv2.resize(binary_mask, (img.shape[1], img.shape[0]))
                contours, _ = cv2.findContours(binary_mask_resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > 1000:
                        overlay = img.copy()
                        cv2.drawContours(overlay, [contour], -1, (0, 255, 0), thickness=cv2.FILLED)
                        img = cv2.addWeighted(overlay, 0.3, img, 0.7, 0)

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

            if confidence > 0.3 and 'car' in class_name.lower():
                car_boxes.append([x1_new, y1_new, x2_new, y2_new])
                area = (x2_new - x1_new) * (y2_new - y1_new)
                car_areas.append(area)
                centroids.append((x_center, y_center))

                cv2.rectangle(img, (x1_new, y1_new), (x2_new, y2_new), (255, 0, 0), 2)
                cv2.putText(img, class_name, (x1_new, y1_new - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # === Fuzzy C-means Klasifikasi Ukuran
    if len(car_areas) >= 2:
        data = np.array(car_areas).reshape(1, -1)
        cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(data, c=2, m=2, error=0.005, maxiter=1000)
        cluster_membership = np.argmax(u, axis=0)
        cluster_urutan = np.argsort(cntr[:, 0])
        label_dict = {
            cluster_urutan[0]: "City Car",
            cluster_urutan[1]: "SUV"
        }

        for i in range(len(car_boxes)):
            ukuran = label_dict[cluster_membership[i]]
            cx, cy = centroids[i]
            cv2.putText(img, ukuran, (cx - 40, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    else:
        for (cx, cy) in centroids:
            cv2.putText(img, "Mobil", (cx - 30, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    for id, x, y in posList:
        status_bool = False
        for (cx1, cy1, cx2, cy2) in car_boxes:
            if x < cx2 and cx1 < x + opencv_box_width and y < cy2 and cy1 < y + opencv_box_height:
                status_bool = True
                break

        color = (0, 0, 255) if status_bool else (0, 255, 0)
        thickness = 3 if status_bool else 5
        if not status_bool:
            spaceCounter += 1

        cv2.rectangle(img, (x, y), (x + opencv_box_width, y + opencv_box_height), color, thickness)
        cvzone.putTextRect(img, str(id), (x + 5, y + 15), scale=0.5, thickness=1, offset=0, colorR=color)

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
    return img

# === MAIN LOOP
while True:
    success, img = cap.read()
    if not success:
        print("Gagal membaca frame.")
        break

    img = enhance_image(img)
    imgResult = checkParkingSpaceYOLO(img, posList, model)

    cv2.imshow("Parking Detection", imgResult)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
