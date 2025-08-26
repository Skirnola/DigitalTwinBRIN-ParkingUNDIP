from ultralytics import YOLO
import cv2
import pickle
import cvzone
import numpy as np

# === Load model dan posisi slot
model = YOLO("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/B_best.pt")
with open("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

opencv_box_width, opencv_box_height = 50, 60

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cv2.namedWindow("Parking Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Parking Detection", 1280, 720)

def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.2)
    car_boxes = []
    car_areas = []
    centroids = []
    contours_list = []

    for result in results:
        # === Ambil kontur dari masking (YOLO segmentation)
        if hasattr(result, 'masks') and result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            for mask in masks:
                binary_mask = (mask * 255).astype(np.uint8)
                binary_mask = cv2.resize(binary_mask, (img.shape[1], img.shape[0]))
                contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 1000:
                        car_areas.append(area)
                        contours_list.append(cnt)
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:
                            cx, cy = 0, 0
                        centroids.append((cx, cy))

        # === Tampilkan bounding box biru
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            x_center = (x1 + x2) // 2
            y_center = (y1 + y2) // 2
            confidence = box.conf[0].item()
            class_id = int(box.cls[0].item())
            class_name = model.names[class_id]

            if confidence > 0.2 and 'car' in class_name.lower():
                car_boxes.append([x1, y1, x2, y2])
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(img, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # === Manual fuzzy logic untuk klasifikasi ukuran mobil
    if len(car_areas) >= 2:
        mean_area = np.mean(car_areas)
        for i, area in enumerate(car_areas):
            cx, cy = centroids[i]
            if area < mean_area:
                ukuran = "City Car"
                color = (0, 255, 0)
            else:
                ukuran = "SUV"
                color = (255, 0, 0)
            cv2.putText(img, ukuran, (cx - 40, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            # Tambahkan juga visualisasi kontur mobil
            cv2.drawContours(img, [contours_list[i]], -1, color, 2)
    else:
        for i, (cx, cy) in enumerate(centroids):
            cv2.putText(img, "Mobil", (cx - 30, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Cek status slot berdasarkan bounding box
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
        cvzone.putTextRect(img, str(id), (x + 5, y + 15),
                           scale=0.5, thickness=1, offset=0, colorR=color)

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}',
                       (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))

    return img

# === MAIN LOOP
while True:
    success, img = cap.read()
    if not success:
        print("Gagal membaca frame dari kamera.")
        break

    imgResult = checkParkingSpaceYOLO(img, posList, model)
    cv2.imshow("Parking Detection", imgResult)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
