from ultralytics import YOLO
import cv2
import pickle
import cvzone
import time
import firebase_admin
from firebase_admin import credentials, db
import numpy as np

cred = credentials.Certificate("C:/Users/KATANA/OneDrive/Documents/Magang BRIN/digitaltwinparkingbrin-firebase-adminsdk-fbsvc-f810a475d7.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://digitaltwinparkingbrin-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

model = YOLO("D:/Digital twin BRIN RI/Digital-Twin-Brin-Parking/ML/B_best.pt")
with open("D:/Digital twin BRIN RI/Digital-Twin-Brin-Parking/A_Mobil_Positioning_Advanced/mobil_positioning_parallelogram.pkl", 'rb') as f:
    posList = pickle.load(f)  # Format: [[x1, y1, x2, y2, x3, y3, x4, y4], ...]

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cv2.namedWindow("Parking Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Parking Detection", 1280, 720)

def adjust_brightness(img, value=-30):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.add(v, value)
    v[v > 255] = 255
    v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

last_update_time = time.time()
update_interval = 8 

def checkParkingSpaceYOLO(img, posList, model, update_firebase=False):
    spaceCounter = 0
    results = model(img, conf=0.1)
    car_boxes = []
    status_dict = {}

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            w, h = 30, 40
            x1_new = x_center - (w // 2)
            y1_new = y_center - (h // 2)
            x2_new = x_center + (w // 2)
            y2_new = y_center + (h // 2)

            confidence = box.conf[0].item()
            class_id = int(box.cls[0].item())
            class_name = model.names[class_id]

            if confidence > 0.1 and 'car' in class_name.lower():
                car_boxes.append([x1_new, y1_new, x2_new, y2_new])
                cv2.rectangle(img, (x1_new, y1_new), (x2_new, y2_new), (255, 0, 0), 2)
                cv2.putText(img, class_name, (x1_new, y1_new - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    for idx, points in enumerate(posList, 1):
        pts = [(points[i], points[i+1]) for i in range(0, 8, 2)] 
        polygon = cv2.convexHull(np.array(pts, dtype=np.int32))
        rect = cv2.boundingRect(polygon)
        rx, ry, rw, rh = rect

        status = False
        for (cx1, cy1, cx2, cy2) in car_boxes:
            if rx < cx2 and cx1 < rx + rw and ry < cy2 and cy1 < ry + rh:
                status = True
                break

        status_dict[f'slot_{idx}'] = status
        color = (0, 0, 255) if status else (0, 255, 0)
        thickness = 3 if status else 5
        if not status:
            spaceCounter += 1

        cv2.polylines(img, [polygon], isClosed=True, color=color, thickness=thickness)
        cvzone.putTextRect(img, str(idx), pts[0], scale=0.5, thickness=1, offset=0, colorR=color)

    if update_firebase:
        ref = db.reference('slot_parking')
        for key, val in status_dict.items():
            ref.child(key).set(val)

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
    return img

while True:
    success, img = cap.read()
    if not success:
        print("Gagal membaca frame dari kamera/video.")
        break

    img = adjust_brightness(img, value=-30)
    current_time = time.time()
    should_update_firebase = (current_time - last_update_time) >= update_interval

    imgResult = checkParkingSpaceYOLO(img, posList, model, update_firebase=should_update_firebase)

    if should_update_firebase:
        last_update_time = current_time

    cv2.imshow("Parking Detection", imgResult)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
