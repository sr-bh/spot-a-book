import json
from fuzzywuzzy import process

def extract_bounding_box(parts, response):
    num_parts = len(parts)
    response = response[1:]
    i = 0
    min_x, max_x, min_y, max_y = float('inf'), 0, float('inf'), 0

    for resp in response:
        name = resp['description'].lower()
        if name == parts[i]:
            for point in resp['boundingPoly']['vertices']:
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

query='the hindu way of awakening'
json_data = json.load(open('img_json.json'))
response = json_data['responses'][0]['textAnnotations']
found = False
fuzzy_match = False
author_match = False
#get candidates
candidates = set(response[0]['description'].lower().split('\n'))
print(candidates)

if query in candidates:
    found = True
    parts = query.split(' ')
    min_x, max_x, min_y, max_y = extract_bounding_box(parts, response)
    print('Found candidate! ', min_x, max_x, min_y, max_y)
else:
    print('Candidate not found')
    #extract fuzzy title matches
    match, score = process.extractOne(query, candidates)
    if score > 80:
        fuzzy_match = True
        parts = match.split(' ')
        min_x, max_x, min_y, max_y = extract_bounding_box(parts, response)
        print('Found a fuzzy title match: ', min_x, max_x, min_y, max_y)

    #extract author based matches
    book_json = json.load(open('book_json.json'))
    author = (book_json['items'][0]["volumeInfo"]["authors"][0]).lower()
    print('author: ', author)
    match, score = process.extractOne(author, candidates)
    if score > 80:
        fuzzy_match = True
        parts = match.split(' ')
        min_x, max_x, min_y, max_y = extract_bounding_box(parts, response)
        print('Found a fuzzy author match: ', min_x, max_x, min_y, max_y)












