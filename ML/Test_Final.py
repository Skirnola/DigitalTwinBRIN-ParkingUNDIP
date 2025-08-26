# from picamera2 import Picamera2
# from ultralytics import YOLO
# import cv2
# import pickle
# import cvzone
# import numpy as np
# import skfuzzy as fuzz

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
#     results = model(img, conf=0.2)
#     car_boxes, car_areas, centroids = [], [], []

#     overlay = img.copy()  # buat masking transparan

#     # === Deteksi mobil dengan YOLO
#     for result in results:
#         for box in result.boxes:
#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#             confidence = box.conf[0].item()
#             class_id = int(box.cls[0].item())
#             class_name = model.names[class_id]

#             if confidence > 0.2 and 'car' in class_name.lower():
#                 w, h = x2 - x1, y2 - y1
#                 area = w * h
#                 car_boxes.append([x1, y1, x2, y2])
#                 car_areas.append(area)
#                 centroids.append(((x1 + x2) // 2, (y1 + y2) // 2))

#     # === Fuzzy C-means clustering (Small, Medium, Big)
#     colors, labels = [], []
#     if len(car_areas) >= 3:
#         data = np.array(car_areas).reshape(1, -1)
#         cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(
#             data, c=3, m=2, error=0.005, maxiter=1000
#         )
#         cluster = np.argmax(u, axis=0)
#         order = np.argsort(cntr[:, 0])  # kecil → sedang → besar
#         label_map = {
#             order[0]: ("Small", (0, 255, 0)),     # hijau
#             order[1]: ("Medium", (0, 255, 255)), # kuning
#             order[2]: ("Big", (0, 0, 255))       # merah
#         }

#         for i, (cx, cy) in enumerate(centroids):
#             ukuran, color = label_map[cluster[i]]
#             labels.append(ukuran)
#             colors.append(color)
#             cv2.putText(img, ukuran, (cx - 40, cy + 20),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
#     else:
#         # kalau mobil kurang dari 3 → default abu-abu
#         for cx, cy in centroids:
#             colors.append((200, 200, 200))
#             labels.append("Mobil")
#             cv2.putText(img, "Mobil", (cx - 30, cy + 20),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

#     # === Gambar masking transparan
#     for i, (x1, y1, x2, y2) in enumerate(car_boxes):
#         mask = np.zeros_like(img, dtype=np.uint8)
#         color = colors[i] if i < len(colors) else (255, 0, 0)
#         cv2.rectangle(mask, (x1, y1), (x2, y2), color, thickness=cv2.FILLED)
#         overlay = cv2.addWeighted(overlay, 1.0, mask, 0.4, 0)

#     img = overlay  # apply masking

#     # === Check parking slot occupancy
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
#         cvzone.putTextRect(img, str(id), (x + 5, y + 15),
#                            scale=0.5, thickness=1, offset=0, colorR=color)

#     cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}',
#                        (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
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

# Load YOLO segmentation model
model = YOLO("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/B_best.pt")

# Load posisi slot parkir
with open("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

# Konfigurasi kamera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)}))
picam2.start()

# Ukuran box parkir
opencv_box_width, opencv_box_height = 50, 60


def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.3)  # segmentation model

    car_masks, car_areas, centroids = [], [], []
    overlay = img.copy()

    # === Ambil segmentation mask dari YOLO
    for result in results:
        if hasattr(result, 'masks') and result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            for mask in masks:
                binary = (mask * 255).astype(np.uint8)
                binary = cv2.resize(binary, (img.shape[1], img.shape[0]))
                cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in cnts:
                    area = cv2.contourArea(cnt)
                    if area > 500:  # filter noise kecil
                        car_masks.append(cnt)
                        car_areas.append(area)
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:
                            cx, cy = 0, 0
                        centroids.append((cx, cy))

    # === Fuzzy C-means clustering (3 kelompok: Small, Medium, Big)
    colors = []
    if len(car_areas) >= 3:
        data = np.array(car_areas).reshape(1, -1)
        cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(
            data, c=3, m=2, error=0.005, maxiter=1000
        )
        cluster = np.argmax(u, axis=0)
        order = np.argsort(cntr[:, 0])  # kecil → sedang → besar
        label_map = {
            order[0]: ("Small", (0, 255, 0)),     # hijau
            order[1]: ("Medium", (0, 255, 255)), # kuning
            order[2]: ("Big", (0, 0, 255))       # merah
        }

        for i, (cx, cy) in enumerate(centroids):
            ukuran, color = label_map[cluster[i]]
            colors.append(color)
            cv2.putText(img, ukuran, (cx - 40, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        for cx, cy in centroids:
            colors.append((200, 200, 200))
            cv2.putText(img, "Mobil", (cx - 30, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Gambar masking sesuai bentuk mobil
    for i, cnt in enumerate(car_masks):
        mask = np.zeros_like(img, dtype=np.uint8)
        color = colors[i] if i < len(colors) else (255, 0, 0)
        cv2.drawContours(mask, [cnt], -1, color, thickness=cv2.FILLED)
        overlay = cv2.addWeighted(overlay, 1.0, mask, 0.4, 0)

    img = overlay  # apply masking transparan

    # === Cek slot parkir kosong / terisi
    for id, x, y in posList:
        status = False
        for cnt in car_masks:
            if cv2.pointPolygonTest(cnt, (x + opencv_box_width // 2,
                                          y + opencv_box_height // 2), False) >= 0:
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


# Main loop
while True:
    img = picam2.capture_array()
    imgResult = checkParkingSpaceYOLO(img, posList, model)
    cv2.imshow("Parking Detection", imgResult)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
