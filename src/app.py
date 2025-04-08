from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename
import numpy as np
import cv2
import os
import time

compressed_result = 'Foto yang telah Dikompresi'

if not os.path.exists(compressed_result):
    os.makedirs(compressed_result)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'static/compressed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def im2double(im):
    """Convert image to double precision."""
    info = np.iinfo(im.dtype)
    return im.astype(np.float64) / 255.0

def channel_svd(channel):
    """Compute SVD of the input data matrix."""
    u, sigma, vt = np.linalg.svd(channel, full_matrices=False)
    return u, sigma, vt

def channel_via_optimal_k(k, u, s_diagonalized, vt):
    """Reconstruct matrix by selecting optimal_k singular values."""
    u_k = u[:, :k]
    s_k = np.diag(s_diagonalized[:k])
    vt_k = vt[:k, :]
    return np.dot(np.dot(u_k, s_k), vt_k)

def compress_image(image_path, compression_rate):
    img = cv2.imread(image_path)
    blue_channel = im2double(img[:, :, 0])
    green_channel = im2double(img[:, :, 1])
    red_channel = im2double(img[:, :, 2])

    u_red, s_red, vt_red = channel_svd(red_channel)
    u_blue, s_blue, vt_blue = channel_svd(blue_channel)
    u_green, s_green, vt_green = channel_svd(green_channel)

    effective_compression_rate = 100 - compression_rate

    optimal_k_red = max(1, min(int(effective_compression_rate / 100 * len(s_red)), len(s_red)))
    optimal_k_blue = max(1, min(int(effective_compression_rate / 100 * len(s_blue)), len(s_blue)))
    optimal_k_green = max(1, min(int(effective_compression_rate / 100 * len(s_green)), len(s_green)))

    blue_reconstruction_matrix = channel_via_optimal_k(optimal_k_blue, u_blue, s_blue, vt_blue)
    green_reconstruction_matrix = channel_via_optimal_k(optimal_k_green, u_green, s_green, vt_green)
    red_reconstruction_matrix = channel_via_optimal_k(optimal_k_red, u_red, s_red, vt_red)

    re_image = cv2.merge((blue_reconstruction_matrix, green_reconstruction_matrix, red_reconstruction_matrix))
    re_image = (re_image * 255).astype(np.uint8)

    pixel_difference = compression_rate
    
    filename = os.path.basename(image_path)
    compressed_filename = f'compressed_photo_{filename}'

    result_compressed_folder = 'Foto yang telah Dikompresi'
    compressed_image_path_result = os.path.join(result_compressed_folder, compressed_filename)
    cv2.imwrite(compressed_image_path_result, re_image, [cv2.IMWRITE_JPEG_QUALITY, 90])

    compressed_image_path = os.path.join(COMPRESSED_FOLDER, f'compressed_photo_{filename}')
    cv2.imwrite(compressed_image_path, re_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    info_percentage_red = (optimal_k_red / len(s_red)) * 100
    info_percentage_blue = (optimal_k_blue / len(s_blue)) * 100
    info_percentage_green = (optimal_k_green / len(s_green)) * 100
    info_percentage = (info_percentage_red + info_percentage_blue + info_percentage_green) / 3

    return compressed_image_path, info_percentage, pixel_difference
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(COMPRESSED_FOLDER, filename)
    
    return filename.save(COMPRESSED_FOLDER)

@app.route('/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        start_time = time.time()
        compression_rate = int(request.form['rate'])
        compressed_image_path, info_percentage, pixel_difference = compress_image(filepath, compression_rate)
        compression_time = time.time() - start_time
        return jsonify({
            'compression_time': compression_time,
            'info_percentage': info_percentage,
            'pixel_difference': pixel_difference,
            'compressed_image_path': f"/static/compressed/{os.path.basename(compressed_image_path)}"
        })

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(COMPRESSED_FOLDER):
        os.makedirs(COMPRESSED_FOLDER)
    app.run(debug=True)
