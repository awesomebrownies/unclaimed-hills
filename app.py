import json, time, random;
from flask import Flask, jsonify, request;

app = Flask(__name__)

#planning:
# GETS
#    get full 8x8 board status
#    get synchronize request
#          send: game code, receive: ping, current timer amount

#    get total games in last 24 hours
#    get amount currently playing
# POSTS 
#    post create new game
#        receive: host player id, game code
#    post join game
#        send: game code, receive: confirm, second player id
#    post next move
#        send: game code, vector, move type

#get length to find how many games
startedGames = []

activeGames = {}

def generateCode():
    code = ""
    for i in range(4):
        code += chr(random.randrange(1, 26) + 64)
    return code

@app.route('/game/create', methods=['POST'])
def createGame():
    #generate a random 4 letter code
    gameCode = generateCode()
    creationTime = time.time()

    hostID = generateCode()
    secondPlayerID = generateCode()

    activeGames[gameCode] = {
        'creationTime': creationTime,
        'startTime': -1,
        'hostID': hostID,
        'secondPlayerID': secondPlayerID
    }

@app.route('/game/join', methods=['POST'])
#when join game is called, start game countdown
def joinGame(gameCode):
    activeGames[gameCode]


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