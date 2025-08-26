from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import pickle
import cvzone
import numpy as np
import skfuzzy as fuzz
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import time

# === Firebase Setup ===
cred = credentials.Certificate("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/digitaltwinparkingbrin-firebase-adminsdk-fbsvc-f810a475d7.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://digitaltwinparkingbrin-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# Load YOLO segmentation model
model = YOLO("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/ML/B_best.pt")

# Load posisi slot parkir
with open("/home/pi/DigitalTwinBRIN/Digital-Twin-Brin-Parking-main/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

# Konfigurasi kamera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (1280, 720)})
picam2.configure(config)

sensor_w, sensor_h = picam2.sensor_resolution
preview_aspect = 16 / 9
zoom_factor = 1.9  # awal normal

def apply_zoom(factor):
    """Atur ROI zoom sesuai faktor (1.0 = normal, >1.0 = zoom in)."""
    global zoom_factor
    zoom_factor = max(1.9, min(factor, 5.0))  # batasi 1x–5x zoom

    center_x, center_y = sensor_w // 2, sensor_h // 2
    new_width = int(sensor_w / zoom_factor)
    new_height = int(new_width / preview_aspect)

    # jika tinggi melebihi sensor, sesuaikan
    if new_height > int(sensor_h / zoom_factor):
        new_height = int(sensor_h / zoom_factor)
        new_width = int(new_height * preview_aspect)

    roi = (
        center_x - new_width // 2,
        center_y - new_height // 2,
        new_width,
        new_height
    )
    picam2.set_controls({"ScalerCrop": roi})
    print(f"Zoom factor: {zoom_factor:.1f}x")

# Terapkan zoom awal
apply_zoom(zoom_factor)

picam2.start()

opencv_box_width, opencv_box_height = 36, 46

# --- Timer untuk history update ---
last_history_update = time.time()
HISTORY_INTERVAL = 120   # detik


def checkParkingSpaceYOLO(img, posList, model):
    global last_history_update

    spaceCounter = 0
    results = model(img, conf=0.3)

    car_masks, car_areas, centroids = [], [], []
    overlay = img.copy()
    size_labels = []  # simpan label ukuran mobil

    # === Ambil segmentation mask ===
    for result in results:
        if hasattr(result, 'masks') and result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            for mask in masks:
                binary = (mask * 255).astype(np.uint8)
                binary = cv2.resize(binary, (img.shape[1], img.shape[0]))
                cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in cnts:
                    area = cv2.contourArea(cnt)
                    if area > 500:
                        car_masks.append(cnt)
                        car_areas.append(area)
                        M = cv2.moments(cnt)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:
                            cx, cy = 0, 0
                        centroids.append((cx, cy))

    # === Fuzzy C-means clustering ===
    colors = []
    if len(car_areas) >= 3:
        data = np.array(car_areas).reshape(1, -1)
        cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(
            data, c=3, m=2, error=0.005, maxiter=1000
        )
        cluster = np.argmax(u, axis=0)
        order = np.argsort(cntr[:, 0])
        label_map = {
            order[0]: ("Small", (0, 255, 0)),
            order[1]: ("Medium", (0, 255, 255)),
            order[2]: ("Big", (0, 0, 255))
        }

        for i, (cx, cy) in enumerate(centroids):
            ukuran, color = label_map[cluster[i]]
            colors.append(color)
            size_labels.append(ukuran)
            cv2.putText(img, ukuran, (cx - 40, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    else:
        for cx, cy in centroids:
            colors.append((200, 200, 200))
            size_labels.append("Unknown")
            cv2.putText(img, "Mobil", (cx - 30, cy + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    # === Gambar masking ===
    for i, cnt in enumerate(car_masks):
        mask = np.zeros_like(img, dtype=np.uint8)
        color = colors[i] if i < len(colors) else (255, 0, 0)
        cv2.drawContours(mask, [cnt], -1, color, thickness=cv2.FILLED)
        overlay = cv2.addWeighted(overlay, 1.0, mask, 0.4, 0)

    img = overlay

    # === Update slot parking + Firebase ===
    ref_parking = db.reference("slot_parking")
    ref_history = db.reference("slot_history")

    # cek apakah sudah waktunya update history
    now = time.time()
    do_history_update = (now - last_history_update) >= HISTORY_INTERVAL
    if do_history_update:
        last_history_update = now

    for id, x, y in posList:
        status = False
        size = "None"
        for i, cnt in enumerate(car_masks):
            if cv2.pointPolygonTest(cnt, (x + opencv_box_width // 2,
                                          y + opencv_box_height // 2), False) >= 0:
                status = True
                size = size_labels[i]
                break

        color = (0, 0, 255) if status else (0, 255, 0)
        thickness = 3 if status else 5
        if not status:
            spaceCounter += 1

        cv2.rectangle(img, (x, y), (x + opencv_box_width, y + opencv_box_height), color, thickness)
        cvzone.putTextRect(img, str(id), (x + 5, y + 15),
                           scale=0.5, thickness=1, offset=0, colorR=color)

        # --- Update realtime slot status ---
        ref_parking.child(f"slot_{id}").set({
            "occupied": status,
            "size": size
        })

        # --- Update history hanya tiap HISTORY_INTERVAL detik ---
        if do_history_update:
            waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if status:
                ref_history.child(f"slot_{id}").child(waktu).set({
                    "status": "terisi",
                    "size": size
                })
            else:
                ref_history.child(f"slot_{id}").child(waktu).set({
                    "status": "kosong",
                    "size": "None"
                })

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}',
                       (50, 50), scale=2.5, thickness=4, offset=10, colorR=(0, 200, 0))
    cv2.putText(img, f"Zoom: {zoom_factor:.1f}x", (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    return img


# === Main Loop ===
while True:
    img = picam2.capture_array()
    imgResult = checkParkingSpaceYOLO(img, posList, model)
    cv2.imshow("Parking Detection", imgResult)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('+') or key == ord('='):
        apply_zoom(zoom_factor + 0.5)
    elif key == ord('-') or key == ord('_'):
        apply_zoom(zoom_factor - 0.5)

picam2.stop()
cv2.destroyAllWindows()
