import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from ocr_extraction import process_prescription

load_dotenv()

app = Flask(__name__)
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

    # Save the file to the uploads directory
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Process the uploaded file using OCR
    try:
        print(f"Processing file: {file_path}")
        process_prescription(file_path)  # This generates `output.json`
        
        output_path = "output.json"
        if not os.path.exists(output_path):
            return jsonify({"error": "Failed to generate output file"}), 500
            
        with open(output_path, "r") as f:
            extracted_data = f.read()
        print("Successfully processed file")
        return jsonify({"message": "File uploaded and processed successfully", "data": extracted_data})
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)