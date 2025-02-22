import json, time;
from flask import Flask, jsonify, request;

# app = Flask(__name__)

# snippets = {1: {'timestamp': -1, 'paste': 'example'}}


# @app.route('/snippets', methods=['GET'])
# def getAllSnippets():
#     return jsonify({snippets})

# @app.route('/snippets/<int:id>', methods=['GET'])
# def getSnippet(id: int):
#     if id in snippets:
#         return jsonify({'id': id, **snippets[id]})
#     return jsonify({'error': 'Snippet not found'}), 404

# @app.route('/snippets', methods=['POST'])
# def createSnippet():
#     nextSnippetId = snippets.__len__ + 1
#     timestamp = time.time()
#     postData = request.get_json()

#     if 'paste' not in postData:
#         return jsonify({'error': 'Missing "paste" field'}), 400

#     snippets[nextSnippetId] = {'timestamp': timestamp, 'paste': postData['paste']}
#     response = {'id': id, **snippets[nextSnippetId]}

#     return jsonify(response), 201

