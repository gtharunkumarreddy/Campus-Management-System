import cv2
import numpy as np
import os

dataset_path = "dataset"

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

faces = []
labels = []
label_map = {}
current_label = 0

for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    label_map[current_label] = person

    for image_name in os.listdir(person_path):
        image_path = os.path.join(person_path, image_name)
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        faces.append(img)
        labels.append(current_label)

    current_label += 1

print("Training model... Please wait")

recognizer.train(faces, np.array(labels))
recognizer.save("trainer.yml")

print("✅ Training completed successfully!")
print("Model saved as trainer.yml")

