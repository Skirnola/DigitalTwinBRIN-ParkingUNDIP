from ultralytics import YOLO
import cv2
import time

model = YOLO("C:/Users/KATANA/OneDrive/Documents/Magang BRIN/B_best.pt")

cap = cv2.VideoCapture(0)  

if not cap.isOpened():
    print("Gagal membuka kamera.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cv2.namedWindow("YOLOv8 Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("YOLOv8 Detection", 1280, 720)

while True:
    start_time = time.time()

    success, frame = cap.read()
    if not success:
        print("Gagal membaca frame dari kamera.")
        break

    results = model.predict(frame, conf=0.1, device='cuda' if model.device.type == 'cuda' else 'cpu')

    annotated_frame = frame.copy()
    num_detections = 0

    if results:
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]

                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{class_name} {conf:.2f}"
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                num_detections += 1

    fps = 1.0 / (time.time() - start_time)

    cv2.putText(annotated_frame, f"Terdeteksi: {num_detections}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("YOLOv8 Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
