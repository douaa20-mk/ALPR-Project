document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const startBtn = document.getElementById("startBtn");
    const captureBtn = document.getElementById("captureBtn");
    const snapBtn = document.getElementById("snapBtn");
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const resultSection = document.getElementById("result-section");
    const resultImage = document.getElementById("resultImage");
    const accuracySpan = document.getElementById("accuracy");
    const detectionsDiv = document.getElementById("detections");
    const plateTextsDiv = document.getElementById("plateTexts");
    const plateImagesDiv = document.getElementById("plateImages");
    const loadingText = document.getElementById("loadingText");
    const timeTaken = document.getElementById("timeTaken");

    let currentImageFile = null;
    let cameraStream = null;

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            currentImageFile = fileInput.files[0];
            startBtn.disabled = false;
        }
    });

    async function sendImageToServer(imageBlob) {
        loadingText.style.display = "block";
        const startTime = performance.now();

        const formData = new FormData();
        formData.append("image", imageBlob);

        try {
            const response = await fetch("/upload", { method: "POST", body: formData });
            const data = await response.json();

            resultSection.style.display = "block";
            resultImage.src = data.annotated_image;
            accuracySpan.textContent = data.accuracy;
            detectionsDiv.innerHTML = "";
            plateImagesDiv.innerHTML = "";
            plateTextsDiv.innerHTML = "";

            // Display all detected plates with OCR text
            data.detections.forEach((det, idx) => {
                const detP = document.createElement("p");
                detP.textContent = `Class: ${det.class}, Conf: ${det.confidence}, BBox: ${det.bbox}, Text: ${det.text}`;
                detectionsDiv.appendChild(detP);

                if (data.plate_images[idx]) {
                    const imgEl = document.createElement("img");
                    imgEl.src = data.plate_images[idx];
                    imgEl.classList.add("plate-crop");
                    plateImagesDiv.appendChild(imgEl);
                }

                if (data.plate_texts[idx]) {
                    const textP = document.createElement("p");
                    textP.textContent = `Plate ${idx + 1}: ${data.plate_texts[idx]}`;
                    plateTextsDiv.appendChild(textP);
                }
            });

            const duration = ((performance.now() - startTime) / 1000).toFixed(2);
            timeTaken.textContent = `⏱ Processing time: ${duration}s`;
            timeTaken.style.display = "block";

        } catch (err) {
            alert("Failed to process image.");
        } finally {
            loadingText.style.display = "none";
        }
    }

    startBtn.addEventListener("click", () => {
        if (currentImageFile) sendImageToServer(currentImageFile);
    });

    captureBtn.addEventListener("click", () => {
        navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
            cameraStream = stream;
            video.style.display = "block";
            snapBtn.style.display = "block";
            video.srcObject = stream;
        });
    });

    snapBtn.addEventListener("click", () => {
        const context = canvas.getContext("2d");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(blob => { if (blob) sendImageToServer(blob); }, "image/jpeg");
    });
});
