import time, random, logging, threading;
from flask import Flask, jsonify, request;

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

#planning:
# GETS
#    get radius 5 hexagon
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
activeGames = {}
hex_rows = [1,2,4,5,4,3,2,1]

@app.route('/game/active', methods=['GET'])
def countActiveGames():
    return jsonify({'count': len(activeGames)})

@app.route('/game/sync', methods=['GET'])
def synchronize():
    data = request.get_json()
    gameCode = data.get('gameCode')

    if gameCode not in activeGames:
        return jsonify({'error': 'Game not found'}), 404
    #find current interval time, the board arraylist
    return jsonify({'board': activeGames[gameCode]['board']})

def generateCode():
    return "".join(chr(random.randint(65, 90)) for _ in range(4))

@app.route('/game/create', methods=['POST'])
def createGame():
    #generate a random 4 letter code
    gameCode = generateCode()
    creationTime = time.time()

    hostID = generateCode()
    playerID = generateCode()

    hostLocation = random.randrange(0,24)
    playerLocation = random.randrange(0,23)
    if(hostLocation == playerLocation):
        playerLocation += 1

    #0=unclaimed, 1=host fortress, -1=player fortress, 2=claimed by host, -2=claimed by player
    #additional numbers=stacked protection
    board = [0] * sum(hex_rows)
    board[hostLocation] = 1
    board[playerLocation] = -1

    activeGames[gameCode] = {
        'creationTime': creationTime,
        'startTime': -1,
        'timeout': 0,
        'hostID': hostID,
        'playerID': playerID,
        'hostMove': None,
        'playerMove': None,
        'board': board
    }
    return jsonify({'gameCode': gameCode, 'hostID': hostID, 'playerID': playerID})

@app.route('/game/join', methods=['POST'])
#when join game is called, start game countdown
def joinGame():
    data = request.get_json()
    gameCode = data.get('gameCode')

    if gameCode not in activeGames:
        return jsonify({'error': 'Game not found'}), 404

    activeGames[gameCode]['startTime'] = time.time()

    return jsonify({'message': 'Game joined'})

def get_adjacent_tiles(x,y,board_size):
    #returns list of adjacent tile positions
    adjacent_offsets = [
        (-1,-1), (0,-1),
        (-1,1), (0,1),
        (-1,0), (1,0)
    ]

    if y % 2 == 0:
        adjacent_offsets = [(dx + 1 if dx == 0 else dx, dy) for dx,dy in adjacent_offsets]

    adjacent_tiles = [(x + dx, y + dy) for dx, dy in adjacent_offsets]

    #return and filter out of bounds
    return [(nx, ny) for nx, ny in adjacent_tiles if 0 <= nx < board_size and 0 <= ny < board_size]

@app.route('/game/move', methods=['POST'])
def makeMove():
    data = request.get_json()
    gameCode, playerID, moveIndex, moveType = data.get('gameCode'), data.get('playerID'), data.get('moveIndex'), data.get('moveType')

    if gameCode not in activeGames or moveIndex is None:
        return jsonify({'error': 'Invalid request'}), 400

    game = activeGames[gameCode]
    if playerID not in [game['hostID'], game['playerID']]:
        return jsonify({'error': 'Unauthorized'}), 403
    playerSymbol = 1 if playerID ==game['hostID'] else -1
    if game['board'][moveIndex] != 0 and moveType == 'claim':
        return jsonify({'error': 'Invalid move'}), 400
    
    if moveType == 'claim':
        game['board'][moveIndex] = playerSymbol
    elif moveType == 'defend' and abs(game['board'][moveIndex]) == 1:
        game['board'][moveIndex] += playerSymbol
    
    if playerID == game['hostID']:
        game['hostMove'] = (moveIndex,moveType)
    else:
        game['playerMove'] = (moveIndex, moveType)

    return jsonify({'message': 'Move recorded'})

def has_adjacent_claimed(x,y,board,board_size,faction):
    #checks if tile has any adjacent friendly claimed tiles
    for nx,ny in get_adjacent_tiles(x,y,board_size):
        index = coord_to_index(nx,ny)
        if index is not None and abs(board[index]) >= 1:
            return True
    return False

def coord_to_index(x,y):
    #convert coord back to index for use in board list
    if y < 0 or y >= len(hex_rows) or x < 0 or x >= hex_rows[y]:
        return None

    index = sum(hex_rows[:y]) + x
    return index

def index_to_coord(index):
    #converts an index to coordinates, allowing for easier adjacent tile calculations
    row,total = 0,0
    while total + hex_rows[row] <= index:
        total += hex_rows[row]
        row += 1

    col = index - total
    return col, row

#game loop
def loop():
    while True:
        time.sleep(5)
        logging.debug('test2')
        for gameCode in list(activeGames.keys()):
            game = activeGames[gameCode]
            if game['creationTime']-time.time() > 60 * 1000 * 5:
                activeGames.pop(game)
            if game['startTime'] != -1:
                continue
            board = game['board']

            for playerType in ['hostMove', 'playerMove']:
                move = game[playerType]
                if not move:
                    continue
                
                moveIndex,moveType=move
                x,y=index_to_coord(moveIndex)

                for nx,ny in get_adjacent_tiles(x,y):
                    adj_index = coord_to_index(nx,ny)
                    if adj_index is None:
                        continue
                    adj_value = board[adj_value]

                    if moveType == 'claim' and abs(adj_value) == 1:
                        board[adj_value] = board[adj_index] if random.random() < 0.5 else 0
                    elif moveType == 'defend' and abs(adj_value) == 1:
                        board[adj_index] += board[moveIndex]

                game[playerType] = None
            
            if game['timeout'] > 20:
                activeGames.pop(gameCode)

if __name__ == '__main__':
    #run game in separate thread
    game_thread = threading.Thread(target=loop, daemon=True)
    game_thread.start()
    #run flask
    app.run(debug=True)

