# from ultralytics import YOLO
# # from ultralytics.yolo.v8.detect.predict import DetectionPredictor
# import cv2

# model = YOLO("D:/Digital twin BRIN RI/Digital-Twin-Brin-Parking/ML/B_best.pt")
# model.predict(source="0", show=True, conf=0.5)  # accepts all formats - images, video, webcam


from ultralytics import YOLO
import cv2
import pickle
import cvzone
import time

# Load custom YOLOv8 model
model = YOLO("C:/Users/KATANA/OneDrive/Documents/Magang BRIN/B_best.pt")

# Load list of predefined parking slot positions
with open("D:/Digital twin BRIN RI/Digital-Twin-Brin-Parking/A_Mobil_Positions/mobil_positions.pkl", 'rb') as f:
    posList = pickle.load(f)

# Konfigurasi ukuran bounding box untuk deteksi YOLO dan kotak parkir
yolo_box_width, yolo_box_height = 30, 40
opencv_box_width, opencv_box_height = 30, 40

# Inisialisasi kamera (webcam)
cap = cv2.VideoCapture(0)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Setup jendela tampilan
cv2.namedWindow("Parking Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Parking Detection", 1280, 720)

def checkParkingSpaceYOLO(img, posList, model):
    spaceCounter = 0
    results = model(img, conf=0.2)
    car_boxes = []

    for result in results:
        # Dapatkan mask jika model adalah segmentation
        if result.masks is not None:
            for mask in result.masks.data:
                mask = mask.cpu().numpy().astype("uint8") * 255
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(img, contours, -1, (255, 255, 0), 2)

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

    # Cek status setiap kotak parkir
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


# Loop utama
while True:
    success, img = cap.read()
    if not success:
        print("Gagal membaca frame dari kamera/video.")
        break

    # Proses deteksi parkir
    imgResult = checkParkingSpaceYOLO(img, posList, model)
    cv2.imshow("Parking Detection", imgResult)

    # Tekan 'Esc' untuk keluar
    if cv2.waitKey(1) & 0xFF == 27:  
        break

# Bersihkan resource
cap.release()
cv2.destroyAllWindows()
