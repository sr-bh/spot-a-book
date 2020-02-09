from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
import requests
from datetime import datetime
import json
from fuzzywuzzy import process
import os
from werkzeug.utils import secure_filename
from google.cloud import vision
from google.protobuf.json_format import MessageToDict
import io
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

UPLOAD_FOLDER = 'static/images/temp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)


@app.route('/')
def homepage():
    return render_template('index.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        file = request.files['shelf']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            # return redirect(url_for('uploaded_file',
            #                         filename=filename))
            # img_file = url_for('uploaded_file', filename=filename)
            img_file = os.path.join(UPLOAD_FOLDER, filename)
            # print(img_file)
            query = title + author

            texts = detect_text(img_file)
            result = getMatch(query, texts, img_file)
            return result
        else:
            flash('Wrong type of file')
            return redirect(request.url) 


@app.route('/static/images/temp/<filename>')
def uploaded_file(filename):
    # print("HERE")
    return send_from_directory(UPLOAD_FOLDER, filename)


def search_for_book(query):
    url = "https://www.googleapis.com/books/v1/volumes?q="
    terms = query.split()
    url += '+'.join(terms)

    response = requests.get(url)
    # print("Book type", type(response))
    # print(response)
    if response.status_code == requests.codes.ok:
        # print(type(response.text))
        return response.text
    elif response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        raise Exception('Error: Cannot get a book using query: {}'.format(
            query
        ))


@app.route('/getText', methods=['POST'])
def detect_text(path):
    """Detects text in the file."""
    
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    # print(response)
    
    texts = MessageToDict(response)
    # print(type(texts))
    # print("TEXTS: ", texts)
    # print(type(texts))
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        return json.dumps(texts)


def getImage(img_file, min_x, max_x, min_y, max_y):
    img = mpimg.imread(img_file)
    img = cv2.rectangle(img, (min_x - 25, min_y - 25), (max_x + 25, max_y + 25), (0, 255, 0), 15)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    imgplot = plt.imshow(img)
    save_file = img_file.split('.')
    date_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    save_filepath = save_file[0] + date_str + '_box.' + save_file[1]
    plt.savefig(save_filepath)
    return save_filepath


def extract_bounding_box(parts, response):
    num_parts = len(parts)
    response = response[1:]
    i = 0
    min_x, max_x, min_y, max_y = float('inf'), 0, float('inf'), 0
    #points = []
    for resp in response:
        name = resp['description'].lower()
        if name == parts[i]:
            # print(name, parts[i], i)
            # print(resp['boundingPoly']['vertices'])

            for point in resp['boundingPoly']['vertices']:
            
                #points.append(point)
                if point['x'] < min_x:
                    min_x = point['x']
                if point['x'] > max_x:
                    max_x = point['x']
                if point['y'] < min_y:
                    min_y = point['y']
                if point['y'] > max_y:
                    max_y = point['y']
            i += 1
            if i == num_parts:
                break
    return min_x, max_x, min_y, max_y
    #return points


def getMatch(query, texts, img_file):
    found = False
    fuzzy_match = False
    author_match = False
    #get candidates
    texts = json.loads(texts)
    # print(texts)
    # print(type(texts))
    texts = texts['textAnnotations']
    candidates = set(texts[0]['description'].lower().split('\n'))

    if query in candidates:
        found = True
        parts = query.split(' ')
        min_x, max_x, min_y, max_y = extract_bounding_box(parts, texts)
        print('Found candidate! ', min_x, max_x, min_y, max_y)
    else:
        print('Candidate not found')
        # extract fuzzy title matches
        match, score = process.extractOne(query, candidates)
        if score > 80:
            fuzzy_match = True
            parts = match.split(' ')
            min_x, max_x, min_y, max_y = extract_bounding_box(parts, texts)
            print('Found a fuzzy title match: ', min_x, max_x, min_y, max_y)

        # extract author based matches
        book_json = search_for_book(query)
        book_json = json.loads(book_json)
        author = (book_json['items'][0]["volumeInfo"]["authors"][0]).lower()
        # print('author: ', author)
        match, score = process.extractOne(author, candidates)
        if score > 80:
            fuzzy_match = True
            parts = match.split(' ')
            min_x, max_x, min_y, max_y = extract_bounding_box(parts, texts)
            print('Found a fuzzy author match: ', min_x, max_x, min_y, max_y)
        else:
            return render_template('result.html', message="No Books found", filename=img_file)
    # print("I am here!")
    img = getImage(img_file, min_x, max_x, min_y, max_y)
    # print("I am after!")
    return render_template('result.html', message="Here are the books we found", filename=img)


if __name__ == '__main__':
    app.run(debug=True)