import cv2
import os
import numpy as np

# Load Haar Cascade for face detection
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Create LBPH Face Recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

dataset_path = "dataset"


def train_model():
    faces = []
    labels = []
    label_map = {}
    current_label = 0

    for filename in os.listdir(dataset_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):

            img_path = os.path.join(dataset_path, filename)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

            faces_detected = face_detector.detectMultiScale(img, 1.3, 5)

            for (x, y, w, h) in faces_detected:
                faces.append(img[y:y+h, x:x+w])
                labels.append(current_label)

            student_name = filename.split(".")[0]
            label_map[current_label] = student_name
            current_label += 1

    if len(faces) > 0:
        recognizer.train(faces, np.array(labels))

    return label_map


def scan_and_mark_attendance():

    label_map = train_model()

    cap = cv2.VideoCapture(0)

    recognized_name = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:

            face_roi = gray[y:y+h, x:x+w]

            try:
                label, confidence = recognizer.predict(face_roi)

                # Lower confidence = better match
                if confidence < 70:
                    recognized_name = label_map[label]
                    cv2.putText(frame, recognized_name, (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Unknown", (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 0, 255), 2)

            except:
                pass

            cv2.rectangle(frame, (x, y),
                          (x+w, y+h),
                          (255, 0, 0), 2)

        cv2.imshow("Smart Attendance Scanner", frame)

        if recognized_name:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return recognized_name