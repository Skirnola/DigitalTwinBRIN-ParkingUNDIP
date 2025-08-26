from picamera2 import Picamera2
import cv2
import os
import pickle

width, height = 36, 46
save_folder = 'A_Mobil_Positions'
os.makedirs(save_folder, exist_ok=True)

save_path = os.path.join(save_folder, 'mobil_positions.pkl')
image_save_path = os.path.join(save_folder, 'layout_parking_spaces.png')

try:
    with open(save_path, 'rb') as f:
        posList = pickle.load(f)
except:
    posList = []

def mouseClick(events, x, y, flags, params):
    global posList
    if events == cv2.EVENT_LBUTTONDOWN:
        posList.append((len(posList) + 1, x, y))
    elif events == cv2.EVENT_RBUTTONDOWN:
        for i, (id, x1, y1) in enumerate(posList):
            if x1 < x < x1 + width and y1 < y < y1 + height:
                posList.pop(i)
                break
    with open(save_path, 'wb') as f:
        pickle.dump(posList, f)

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

cv2.namedWindow("Setup Slot Parkir", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Setup Slot Parkir", 1280, 720)

while True:
    frame = picam2.capture_array()

    # Gambar slot parkir
    for id, x, y in posList:
        cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 0, 0), 2)
        cv2.putText(frame, str(id), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

    cv2.imshow("Setup Slot Parkir", frame)
    cv2.setMouseCallback("Setup Slot Parkir", mouseClick)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        cv2.imwrite(image_save_path, frame)
        print(f"Gambar layout parkir disimpan di {image_save_path}")
        break
    elif key == ord('+') or key == ord('='):  # zoom in
        apply_zoom(zoom_factor + 0.5)
    elif key == ord('-') or key == ord('_'):  # zoom out
        apply_zoom(zoom_factor - 0.5)

picam2.stop()
cv2.destroyAllWindows()
