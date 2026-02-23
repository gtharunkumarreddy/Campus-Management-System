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


def recognize_from_frame(frame):
    """
    Recognize a student from a single BGR frame.
    Returns a student name string if matched, else None.
    """
    label_map = train_model()
    if not label_map:
        return None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face_roi = gray[y:y + h, x:x + w]
        try:
            label, confidence = recognizer.predict(face_roi)
            if confidence < 70 and label in label_map:
                return label_map[label]
        except Exception:
            continue

    return None


def extract_face_roi(gray_image):
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)
    if len(faces) == 0:
        return None

    # Use the largest detected face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return gray_image[y:y + h, x:x + w]


def recognize_from_frame_db(frame, face_rows):
    """
    Recognize a student from DB-stored face samples.
    face_rows format: [(roll, name, face_blob), ...]
    Returns dict: {"roll": str, "name": str} or None.
    """
    if not face_rows:
        return None

    train_faces = []
    labels = []
    label_map = {}
    label = 0

    for roll, name, face_blob in face_rows:
        arr = np.frombuffer(face_blob, dtype=np.uint8)
        db_face = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if db_face is None:
            continue
        train_faces.append(db_face)
        labels.append(label)
        label_map[label] = {"roll": roll, "name": name}
        label += 1

    if not train_faces:
        return None

    model = cv2.face.LBPHFaceRecognizer_create()
    model.train(train_faces, np.array(labels))

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_roi = extract_face_roi(gray)
    if face_roi is None:
        return None

    try:
        predicted_label, confidence = model.predict(face_roi)
        if confidence < 75 and predicted_label in label_map:
            return label_map[predicted_label]
    except Exception:
        return None

    return None
