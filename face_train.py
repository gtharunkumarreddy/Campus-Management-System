import cv2
import os

# Ensure dataset folder exists
if not os.path.exists("dataset"):
    os.makedirs("dataset")

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cam = cv2.VideoCapture(0)

name = input("Enter Student Name: ").strip()
path = os.path.join("dataset", name)

if not os.path.exists(path):
    os.makedirs(path)

count = 0
print("📸 Capturing faces… look straight at the camera")

while True:
    ret, img = cam.read()
    if not ret:
        print("❌ Camera not working")
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        count += 1
        face_img = gray[y:y+h, x:x+w]

        # Resize face (IMPORTANT)
        face_img = cv2.resize(face_img, (200, 200))

        file_path = os.path.join(path, f"{count}.jpg")
        cv2.imwrite(file_path, face_img)

        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        print(f"Saved {file_path}")

    cv2.imshow("Face Capture (ESC to exit)", img)

    if cv2.waitKey(1) == 27 or count >= 30:
        break

cam.release()
cv2.destroyAllWindows()

print("✅ Face dataset saved correctly")
