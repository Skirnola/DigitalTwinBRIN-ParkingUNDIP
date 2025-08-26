import cv2
import pickle
import os

width, height = 30, 35

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

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cv2.namedWindow("Setup Slot Parkir", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Setup Slot Parkir", 1280, 720)  

while True:
    success, img = cap.read()
    if not success:
        print("Gagal membuka kamera.")
        break

    for id, x, y in posList:
        cv2.rectangle(img, (x, y), (x + width, y + height), (255, 0, 0), 2)
        cv2.putText(img, str(id), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

    cv2.imshow("Setup Slot Parkir", img)
    cv2.setMouseCallback("Setup Slot Parkir", mouseClick)

    key = cv2.waitKey(1)
    if key == 27:  
        cv2.imwrite(image_save_path, img)
        print(f"Gambar layout parkir disimpan di {image_save_path}")
        break

cap.release()
cv2.destroyAllWindows()
