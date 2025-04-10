import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from ocr_extraction import process_prescription

load_dotenv()

app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)

# Ensure the uploads directory exists
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        process_prescription(file_path)  # this generates output.json
        with open("output.json", "r") as f:
            extracted_data = f.read()
        return jsonify({"message": "File uploaded and processed successfully", "data": extracted_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔥 Serve React frontend
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_react_app(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
