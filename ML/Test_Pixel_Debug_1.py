from ultralytics import YOLO
import cv2
import pickle
import cvzone
import numpy as np
import skfuzzy as fuzz
from picamera2 import Picamera2

# === Load YOLO model & parking positions
model = YOLO("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/B_best.pt")
with open("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

# === Parameters
yolo_box_width, yolo_box_height = 50, 60
opencv_box_width, opencv_box_height = 30, 40

# === Setup PiCamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)})
picam2.configure(config)
picam2.start()

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

# === Parking space detection and classification
def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.1)
    car_masks, car_areas, centroids = [], [], []

    overlay = img.copy()  # For transparent mask overlay

    for result in results:
        # Segmentation masks
        if hasattr(result, 'masks') and result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            for mask in masks:
                binary = (mask * 255).astype(np.uint8)
                binary = cv2.resize(binary, (img.shape[1], img.shape[0]))
                cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in cnts:
                    a = cv2.contourArea(cnt)
                    if a > 500:
                        car_areas.append(a)
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:
                            cx, cy = 0, 0
                        centroids.append((cx, cy))
                        car_masks.append(cnt)

        # Bounding boxes
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = box.conf[0].item()
            cls_id = int(box.cls[0].item())
            name = model.names[cls_id]

            if conf > 0.1 and 'car' in name.lower():
                w = x2 - x1
                h = y2 - y1
                a = w * h
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                car_areas.append(a)
                centroids.append((cx, cy))
                cnt_box = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
                car_masks.append(cnt_box)

    # === Fuzzy C-means classification
    colors = []
    if len(car_areas) >= 2:
        data = np.array(car_areas).reshape(1, -1)
        cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(data, c=2, m=2, error=0.005, maxiter=1000)
        cluster = np.argmax(u, axis=0)
        order = np.argsort(cntr[:, 0])
        labels = {order[0]: "City Car", order[1]: "SUV"}
        for i, (cx, cy) in enumerate(centroids):
            ukuran = labels[cluster[i]]
            color = (0, 255, 0) if ukuran == "City Car" else (255, 0, 0)
            colors.append(color)
            cv2.putText(img, ukuran, (cx - 40, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        for cx, cy in centroids:
            colors.append((200, 200, 200))
            cv2.putText(img, "Mobil", (cx - 30, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Draw transparent filled contours
    for i, cnt in enumerate(car_masks):
        mask = np.zeros_like(img, dtype=np.uint8)
        cv2.drawContours(mask, [cnt], -1, colors[i], thickness=cv2.FILLED)
        overlay = cv2.addWeighted(overlay, 1.0, mask, 0.4, 0)

    img = overlay  # Apply overlay result

    # === Check parking slot occupancy
    for id, x, y in posList:
        status = False
        for i, cnt in enumerate(car_masks):
            if cv2.pointPolygonTest(cnt, (x + opencv_box_width // 2, y + opencv_box_height // 2), False) >= 0:
                status = True
                break

        if not status:
            spaceCounter += 1
        color = (0, 0, 255) if status else (0, 255, 0)
        thickness = 3 if status else 5
        cv2.rectangle(img, (x, y), (x + opencv_box_width, y + opencv_box_height), color, thickness)
        cvzone.putTextRect(
            img, str(id), (x + 5, y + 15),
            scale=0.5, thickness=1, offset=0, colorR=color)

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}',
                       (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))

    return img

# === MAIN LOOP
while True:
    img = picam2.capture_array()
    img = enhance_image(img)
    imgResult = checkParkingSpaceYOLO(img, posList, model)
    cv2.imshow("Parking Detection", imgResult)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

cv2.destroyAllWindows()
picam2.stop()

