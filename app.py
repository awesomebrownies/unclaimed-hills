import time, random, logging, threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Active games storage
activeGames = {}

# Board configuration that matches the frontend structure
# We'll use flat arrays to match the frontend structure
# null values represent non-playable spaces
BOARD_CONFIG = [
    None, 0, 0, 0, 0, None, None,
    None, 0, 0, 0, 0, 0, None,
    0, 0, 0, 0, 0, 0, None,
    0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, None,
    None, 0, 0, 0, 0, 0, None,
    None, 0, 0, 0, 0, None, None
]

# Map flat index to 2D coordinates for adjacency calculations
COORDINATES_MAP = {}
ADJACENCY_MAP = {}

def initialize_maps():
    """Create maps for flat index to 2D coordinates and adjacency"""
    grid_width = 7  # width of our hex grid
    idx = 0
    
    # Create a 2D map from the flat board
    board_2d = []
    for col in range(grid_width):
        col_arr = []
        for row in range(grid_width):
            if idx < len(BOARD_CONFIG):
                col_arr.append(BOARD_CONFIG[idx])
                if BOARD_CONFIG[idx] is not None:
                    COORDINATES_MAP[idx] = (col, row)
                idx += 1
        board_2d.append(col_arr)
    
    # Calculate adjacency for each valid cell
    for idx, coords in COORDINATES_MAP.items():
        col, row = coords
        adjacent_indices = []
        
        # Get adjacent cells based on hex grid rules
        offset_type = 'odd' if col % 2 else 'even'
        directions = {
            'odd': [(0, -1), (1, -1), (1, 0), (0, 1), (-1, 0), (-1, -1)],
            'even':  [(0, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
        }
        
        for dx, dy in directions[offset_type]:
            new_col, new_row = col + dx, row + dy
            # Check if valid position
            if 0 <= new_col < grid_width and 0 <= new_row < grid_width:
                # Find the corresponding flat index
                for adj_idx, adj_coords in COORDINATES_MAP.items():
                    if adj_coords == (new_col, new_row):
                        adjacent_indices.append(adj_idx)
                        break
        
        ADJACENCY_MAP[idx] = adjacent_indices

# Initialize the coordinate and adjacency maps
initialize_maps()

def generate_code(length=4):
    """Generate a random code of specified length"""
    return "".join(chr(random.randint(65, 90)) for _ in range(length))

def check_win_condition(board):
    """Check if either player has won the game"""
    # Check if host fortresses (value 1 or 2) exist
    host_fortress_exists = any(cell in [1, 2] for cell in board if cell is not None)
    
    # Check if player fortresses (value -1 or -2) exist
    player_fortress_exists = any(cell in [-1, -2] for cell in board if cell is not None)
    
    if not host_fortress_exists:
        return 'player'
    elif not player_fortress_exists:
        return 'host'
    
    return None  # No winner yet

@app.route('/game/active', methods=['GET'])
def count_active_games():
    """Return count of active games"""
    return jsonify({'count': len(activeGames)})

@app.route('/game/create', methods=['POST'])
def create_game():
    """Create a new game with initial fortresses"""
    # Generate game code and player IDs
    gameCode = generate_code()
    hostId = generate_code()
    playerId = generate_code()
    
    # Create a copy of the empty board
    board = BOARD_CONFIG.copy()
    
    # Get valid positions (non-None cells)
    valid_positions = [idx for idx, cell in enumerate(board) if cell is not None]
    
    # Place fortresses (1 for host, -1 for player)
    host_pos, player_pos = random.sample(valid_positions, 2)
    board[host_pos] = 1    # Host fortress
    board[player_pos] = -1  # Player fortress
    
    # Set up game state
    nextUpdateTime = time.time() + 5  # First update in 5 seconds
    activeGames[gameCode] = {
        'creationTime': time.time(),
        'startTime': -1,  # Will be set when second player joins
        'nextUpdateTime': nextUpdateTime,
        'timeout': 0,
        'hostId': hostId,
        'playerId': playerId,
        'hostMove': None,
        'playerMove': None,
        'board': board,
        'gameOver': False,
        'winner': None
    }
    
    return jsonify({
        'gameCode': gameCode,
        'hostId': hostId,
        'playerId': playerId,
        'board': board,
        'nextUpdateTime': nextUpdateTime
    })

@app.route('/game/sync', methods=['GET'])
def synchronize():
    """Synchronize game state"""
    data = request.args
    gameCode = data.get('gameCode')

    if gameCode not in activeGames:
        return jsonify({'error': 'Game not found'}), 404
    
    game = activeGames[gameCode]
    
    return jsonify({
        'board': game['board'],
        'nextUpdateTime': game['nextUpdateTime'],
        'pendingMoves': {
            'host': game['hostMove'],
            'player': game['playerMove']
        },
        'gameOver': game['gameOver'],
        'winner': game['winner']
    })

@app.route('/game/join', methods=['POST'])
def join_game():
    """Join an existing game"""
    data = request.json
    gameCode = data.get('gameCode')
    
    if gameCode not in activeGames:
        return jsonify({'error': 'Game not found'}), 404
    
    # Mark game as started
    game = activeGames[gameCode]
    game['startTime'] = time.time()
    
    return jsonify({
        'playerId': game['playerId'],
        'board': game['board'],
        'nextUpdateTime': game['nextUpdateTime']
    })

@app.route('/game/move', methods=['POST'])
def make_move():
    """Process a player move"""
    data = request.get_json()
    gameCode = data.get('gameCode')
    playerId = data.get('playerId')
    index = data.get('index')  # Flat index of the cell
    moveType = data.get('moveType')  # 'claim' or 'defend'
    
    if gameCode not in activeGames:
        return jsonify({'error': 'Game not found'}), 404
    
    game = activeGames[gameCode]
    
    # Check if game is over
    if game['gameOver']:
        return jsonify({'error': 'Game is over'}), 400
    
    # Verify player identity
    if playerId not in [game['hostId'], game['playerId']]:
        return jsonify({'error': 'Unauthorized player'}), 403
    
    # Determine player type and symbol
    playerType = 'host' if playerId == game['hostId'] else 'player'
    playerSymbol = 1 if playerType == 'host' else -1
    
    # Validate move
    if index < 0 or index >= len(game['board']):
        return jsonify({'error': 'Invalid position'}), 400
    
    current_value = game['board'][index]
    
    # Cell must exist
    if current_value is None:
        return jsonify({'error': 'Invalid cell'}), 400
    
    if moveType == 'claim':
        # Cannot claim own cells
        if current_value != 0 or current_value == playerSymbol:
            return jsonify({'error': 'Cell already claimed'}), 400
        
        # Check for adjacent friendly territory
        has_adjacent_friendly = False
        for adj_idx in ADJACENCY_MAP.get(index, []):
            adj_value = game['board'][adj_idx]
            if adj_value is not None and (adj_value * playerSymbol > 0):
                has_adjacent_friendly = True
                break
        
        # Allow first move without adjacency check if no fortress exists
        if not has_adjacent_friendly:
            fortress_exists = any(
                cell * playerSymbol > 0 for cell in game['board'] if cell is not None
            )
            if fortress_exists:
                return jsonify({'error': 'Must be adjacent to friendly territory'}), 400
    
    elif moveType == 'defend':
        # Can only defend your own territory
        if current_value * playerSymbol <= 0:
            return jsonify({'error': 'Can only defend your own territory'}), 400
    
    # Store the move
    move_data = {'index': index, 'type': moveType}
    if playerType == 'host':
        game['hostMove'] = move_data
    else:
        game['playerMove'] = move_data
    
    # Broadcast move preview to all clients in the game room
    socketio.emit('move_preview', {
        'playerType': playerType,
        'move': move_data
    }, room=gameCode)
    
    return jsonify({
        'message': 'Move queued',
        'nextUpdateTime': game['nextUpdateTime']
    })

@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')

@socketio.on('join_game')
def handle_join_game(data):
    gameCode = data.get('gameCode')
    
    if gameCode not in activeGames:
        emit('error', {'message': 'Game not found'})
        return
    
    # Join the socket room for this game
    join_room(gameCode)
    
    game = activeGames[gameCode]
    emit('joined', {
        'message': 'Successfully joined game room',
        'gameCode': gameCode,
        'board': game['board'],
        'nextUpdateTime': game['nextUpdateTime'],
        'pendingMoves': {
            'host': game['hostMove'],
            'player': game['playerMove']
        },
        'gameOver': game['gameOver'],
        'winner': game['winner']
    })

def process_moves(game):
    """Process the queued moves for a game"""
    board = game['board']
    moves_made = False
    
    # Process both players' moves
    for move_type, move_data in [('host', game['hostMove']), ('player', game['playerMove'])]:
        if not move_data:
            continue
        
        moves_made = True
        index = move_data['index']
        move_action = move_data['type']
        player_symbol = 1 if move_type == 'host' else -1
        
        # Apply the move
        if move_action == 'claim':
            board[index] = player_symbol
        elif move_action == 'defend':
            # Increment/decrement defense value
            current_value = board[index]
            if player_symbol > 0:  # Host
                board[index] = min(2, current_value + 1)
            else:  # Player
                board[index] = max(-2, current_value - 1)
        
        # Process combat effects on adjacent tiles
        for adj_idx in ADJACENCY_MAP.get(index, []):
            adj_value = board[adj_idx]
            if adj_value is not None and adj_value * player_symbol < 0:
                # Combat between opposing territories
                if move_action == 'claim' and abs(adj_value) == 1:
                    # 50% chance to neutralize enemy territory
                    if random.random() < 0.5:
                        board[adj_idx] = 0
                elif move_action == 'defend' and abs(adj_value) == 1:
                    # Defending applies pressure based on strength
                    friendly_pressure = abs(board[index])
                    enemy_pressure = abs(adj_value)
                    if friendly_pressure > enemy_pressure:
                        board[adj_idx] = 0
    
    # Clear moves after processing
    game['hostMove'] = None
    game['playerMove'] = None
    
    return moves_made

def game_loop():
    """Main game loop that runs in background thread"""
    while True:
        current_time = time.time()
        
        # Process each active game
        for gameCode in list(activeGames.keys()):
            game = activeGames[gameCode]
            
            # Skip games that haven't started
            if game['startTime'] == -1:
                continue
            
            # Skip games that have ended
            if game['gameOver']:
                continue
                
            # Process moves when it's time
            if current_time >= game['nextUpdateTime']:
                moves_made = process_moves(game)
                
                # Set next update time (5 seconds from now)
                game['nextUpdateTime'] = current_time + 5
                
                # Check for winner
                winner = check_win_condition(game['board'])
                if winner:
                    game['gameOver'] = True
                    game['winner'] = winner
                
                # Send update to all clients in the game room
                socketio.emit('game_update', {
                    'board': game['board'],
                    'nextUpdateTime': game['nextUpdateTime'],
                    'pendingMoves': {
                        'host': game['hostMove'],
                        'player': game['playerMove']
                    },
                    'gameOver': game['gameOver'],
                    'winner': game['winner']
                }, room=gameCode)
                
                # Track inactivity
                if not moves_made:
                    game['timeout'] += 1
                else:
                    game['timeout'] = 0
                
                # End inactive games
                if game['timeout'] > 12:  # 1 minute without moves
                    socketio.emit('game_timeout', {
                        'message': 'Game ended due to inactivity'
                    }, room=gameCode)
                    activeGames.pop(gameCode, None)
        
        # Cleanup old unstarted games
        for gameCode in list(activeGames.keys()):
            game = activeGames[gameCode]
            if game['startTime'] == -1 and current_time - game['creationTime'] > 600:  # 10 minutes
                activeGames.pop(gameCode, None)
        
        # Sleep to avoid excessive CPU usage
        time.sleep(0.1)

if __name__ == '__main__':
    # Start game loop in a separate thread
    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()
    
    # Run Flask with SocketIO
    socketio.run(app, debug=True, host="0.0.0.0", allow_unsafe_werkzeug=True)