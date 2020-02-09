from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import requests


@app.route('/getBook', methods=['GET'])
def search_for_book(query):
    url = "https://www.googleapis.com/books/v1/volumes?q="
    terms = query.split()

    url += '+'.join(terms)

    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        return jsonify(response.text)
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
def detect_text_uri(uri):
    """Detects text in the file located in Google Cloud Storage or on the Web.
    """
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()
    image = vision.types.Image()
    image.source.image_uri = uri

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print('Texts:')

    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                    for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))


    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        return texts


if __name__ == '__main__':
    app.run(debug=True)
