import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ocr_extraction import process_prescription

# 🔧 Fixed typo: _name_ ➜ __name__
app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)

# Ensure the uploads directory exists
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        process_prescription(file_path)
        with open("output.json", "r") as f:
            extracted_data = f.read()
        return jsonify({"message": "File uploaded and processed successfully", "data": extracted_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Serve React frontend base path
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# ✅ 🔥 FIXED: Serve index.html for all unknown routes (React handles routing client-side)
@app.route('/<path:path>')
def serve_react_app(path):
    requested_path = os.path.join(app.static_folder, path)
    if os.path.exists(requested_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# 🔧 Fixed typo: _name_ ➜ __name__
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)