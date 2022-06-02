import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory,flash 
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import tensorflow_hub as hub
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils

app = Flask(__name__)

app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['DOWNLOAD_FOLDER'] = 'downloads/'

LABEL_FILENAME = 'labels/labelmap.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(
    LABEL_FILENAME, use_display_name=True)

print('''
 _                    _ _               __  __           _      _             
| |    ___   __ _  __| (_)_ __   __ _  |  \/  | ___   __| | ___| |            
| |   / _ \ / _` |/ _` | | '_ \ / _` | | |\/| |/ _ \ / _` |/ _ \ |            
| |__| (_) | (_| | (_| | | | | | (_| | | |  | | (_) | (_| |  __/ |  _   _   _ 
|_____\___/ \__,_|\__,_|_|_| |_|\__, | |_|  |_|\___/ \__,_|\___|_| (_) (_) (_)
                                |___/                                         
''')
model = 'model/'
hub_model = hub.load(model)
print('''
 __  __           _      _   _                    _          _   _ 
|  \/  | ___   __| | ___| | | |    ___   __ _  __| | ___  __| | | |
| |\/| |/ _ \ / _` |/ _ \ | | |   / _ \ / _` |/ _` |/ _ \/ _` | | |
| |  | | (_) | (_| |  __/ | | |__| (_) | (_| | (_| |  __/ (_| | |_|
|_|  |_|\___/ \__,_|\___|_| |_____\___/ \__,_|\__,_|\___|\__,_| (_)
''')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def load_image_into_numpy_array(image):
    (image_width, image_height) = image.size
    return np.array(image.getdata()).reshape((1, image_height, image_width, 3)).astype(np.uint8)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = Image.open(file)
        image_path = image_path.convert('RGB')
        image_np = load_image_into_numpy_array(image_path)
        flip_image_horizontally = False
        convert_image_to_grayscale = False
        if(flip_image_horizontally):
            image_np[0] = np.fliplr(image_np[0]).copy()
        if(convert_image_to_grayscale):
            image_np[0] = np.tile(
                np.mean(image_np[0], 2, keepdims=True), (1, 1, 3)).astype(np.uint8)
        results = hub_model(image_np)
        result = {key: value.numpy() for key, value in results.items()}
        label_id_offset = 0
        image_np_with_detections = load_image_into_numpy_array(image_path)
        viz_utils.visualize_boxes_and_labels_on_image_array(
            image_np_with_detections[0],
            result['detection_boxes'][0],
            (result['detection_classes'][0] + label_id_offset).astype(int),
            result['detection_scores'][0],
            category_index,
            use_normalized_coordinates=True,
            max_boxes_to_draw=200,
            line_thickness=5,
            min_score_thresh=.3,
            agnostic_mode=False)
        label = viz_utils.visualize_boxes_and_labels_on_image_array.class_name
        print(label)
        predicted_image = Image.fromarray(
            image_np_with_detections.squeeze())
        predicted_image.save('downloads/' + filename)
        data={
                "processed_img":'downloads/'+filename,
                "uploaded_img":'uploads/'+filename
        }
        return render_template('index.html', data=data)    


@app.route('/downloads/<name>')
def download_file(name):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], name)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=443)