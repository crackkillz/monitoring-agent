from flask import Flask, request, jsonify
import os
from datetime import datetime

# === CONFIG ===
UPLOAD_FOLDER = "uploads"
LOG_FILE = "upload_log.txt"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # Optional: log uploader IP
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - {request.remote_addr} uploaded {filename}\n")

    return jsonify({"message": "File uploaded successfully"}), 200

@app.route("/")
def index():
    return "Upload Server Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
