import os
import zipfile
import glob
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, jsonify, send_file
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPS

app = Flask(__name__)

# Gunakan /tmp (sementara) karena Vercel hanya izin write di sana
BASE_DIR = '/tmp'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'svg_input')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'eps_output')
ZIP_PATH = os.path.join(OUTPUT_FOLDER, 'converted_eps.zip')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_files():
    if 'files' not in request.files:
        return jsonify({'error': 'Tidak ada file'}), 400
        
    files = request.files.getlist('files')
    
    # Bersihkan file lama (kecuali zip)
    for f in glob.glob(os.path.join(OUTPUT_FOLDER, '*')):
        if not f.endswith('.zip'):
            try: os.remove(f)
            except: pass

    converted_paths = []
    for file in files:
        if file.filename == '': continue
        
        svg_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(svg_path)
        
        eps_filename = os.path.splitext(file.filename)[0] + '.eps'
        eps_path = os.path.join(OUTPUT_FOLDER, eps_filename)
        
        try:
            # Membaca SVG menggunakan svglib
            drawing = svg2rlg(svg_path)
            
            # Mengonversi ke format EPS/PS menggunakan backend ReportLab
            renderPS.drawToFile(drawing, eps_path)
            
            converted_paths.append(eps_path)
            os.remove(svg_path)
        except Exception as e:
            print(f"Gagal convert {file.filename}: {e}")

    if converted_paths:
        with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
            for eps_p in converted_paths:
                zipf.write(eps_p, os.path.basename(eps_p))
        return jsonify({'success': True})
    
    return jsonify({'error': 'Gagal konversi'}), 400

@app.route('/download', methods=['GET'])
def download_zip():
    if os.path.exists(ZIP_PATH):
        return send_file(ZIP_PATH, as_attachment=True, download_name='converted_eps.zip')
    return "File tidak ditemukan", 404

# Hanya untuk running lokal, di Vercel tidak akan dieksekusi
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
