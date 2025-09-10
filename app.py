import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import base64
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr

# Initialize EasyOCR (English + digits)
reader = easyocr.Reader(['en'])

# Initialize Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load YOLOv8 model
model = YOLO(r"C:\Users\mokha\OneDrive\Desktop\License Plate Recognition\licenceplatemodels-20250909T130454Z-1-001\licenceplatemodels\best.pt")

# License plate detection function
def detect_license_plate(image):
    img_np = np.array(image)
    results = model(img_np)[0]

    detections = []
    plate_texts = []
    plate_images_base64 = []

    if results.boxes is not None:
        for box, conf, cls in zip(results.boxes.xyxy.cpu().numpy(),
                                  results.boxes.conf.cpu().numpy(),
                                  results.boxes.cls.cpu().numpy()):
            x1, y1, x2, y2 = map(int, box)
            plate_crop = img_np[y1:y2, x1:x2]
            text = ""

            if plate_crop.size > 0:
                # Preprocess for OCR
                gray = cv2.cvtColor(plate_crop, cv2.COLOR_RGB2GRAY)
                gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                _, gray = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # OCR
                results_ocr = reader.readtext(gray, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                text = " ".join([res[1] for res in results_ocr]) if results_ocr else ""

                # Convert plate crop to base64
                _, buffer = cv2.imencode('.jpg', cv2.cvtColor(plate_crop, cv2.COLOR_RGB2BGR))
                plate_images_base64.append("data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8"))

            plate_texts.append(text)
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': round(float(conf), 3),
                'class': int(cls),
                'text': text
            })

    annotated_img = results.plot()
    return detections, annotated_img, plate_texts, plate_images_base64

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Image upload and processing
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    image = Image.open(filepath).convert("RGB")
    detections, annotated_img, plate_texts, plate_images = detect_license_plate(image)

    # Convert annotated image to base64
    annotated_img_bgr = cv2.cvtColor(annotated_img, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', annotated_img_bgr)
    annotated_base64 = base64.b64encode(buffer).decode("utf-8")

    # Calculate average confidence
    accuracy = round(sum(d['confidence'] for d in detections) / len(detections), 3) if detections else 0.0

    return jsonify({
        "detections": detections,
        "accuracy": accuracy,
        "annotated_image": f"data:image/jpeg;base64,{annotated_base64}",
        "plate_texts": plate_texts,
        "plate_images": plate_images
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
