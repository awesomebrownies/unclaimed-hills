import React, { useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";
import axios from "axios";

type HexValue = number | null;
type ClickHandler = (index: number, button: "left" | "right") => void;
type MoveType = "claim" | "defend";
type PlayerType = "host" | "player";

type PendingMove = {
  index: number;
  type: MoveType;
} | null;

type GameState = {
  board: HexValue[];
  nextUpdateTime: number;
  pendingMoves: {
    host: PendingMove;
    player: PendingMove;
  };
  countdown: number;
  gameOver: boolean;
  winner: PlayerType | null;
};

const HEX_SIZE = 50;
const HEX_WIDTH = HEX_SIZE * 2;
const HEX_HEIGHT = HEX_SIZE * Math.sqrt(3);
const API_BASE_URL = "http://127.0.0.1:5000";

// Hexagonal grid layout definition - this helps with positioning
// Each tuple is [column, row] of the logical grid
const HEX_LAYOUT = [
  [0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6],
  [1, 0], [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6],
  [2, 0], [2, 1], [2, 2], [2, 3], [2, 4], [2, 5], [2, 6],
  [3, 0], [3, 1], [3, 2], [3, 3], [3, 4], [3, 5], [3, 6],
  [4, 0], [4, 1], [4, 2], [4, 3], [4, 4], [4, 5], [4, 6],
  [5, 0], [5, 1], [5, 2], [5, 3], [5, 4], [5, 5], [5, 6],
  [6, 0], [6, 1], [6, 2], [6, 3], [6, 4], [6, 5], [6, 6]
];

// Initial board state
const initialBoard: HexValue[] = [
  null, 0, 0, 0, 0, null, null,
  null, 0, 0, 0, 0, 0, null,
  0, 0, 0, 0, 0, 0, null,
  0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, null,
  null, 0, 0, 0, 0, 0, null,
  null, 0, 0, 0, 0, null, null
];

const getColorFromValue = (value: HexValue): string => {
  switch (value) {
    case 1: return "#90EE90"; // Light green - host fortress
    case 2: return "#228B22"; // Dark green - fortified host
    case -1: return "#FF0000"; // Red - player fortress
    case -2: return "#8B0000"; // Dark red - fortified player
    case 0: return "#808080"; // Gray - unclaimed
    default: return "transparent"; // Skip rendering for null values
  }
};

// Get preview color for pending moves
const getPreviewColor = (value: HexValue, playerType: PlayerType, moveType: MoveType): string => {
  const baseColor = playerType === "host" ? "#90EE90" : "#FF0000";
  const transparentColor = playerType === "host" ? "rgba(144, 238, 144, 0.5)" : "rgba(255, 0, 0, 0.5)";
  
  // For defend moves, show a more solid color
  if (moveType === "defend") {
    return baseColor;
  }
  
  // For claim moves, show a transparent preview
  return transparentColor;
};

type HexagonProps = {
  x: number;
  y: number;
  value: HexValue;
  index: number;
  onClick: ClickHandler;
  previewHost: boolean;
  previewPlayer: boolean;
  previewMoveType: MoveType | null;
};

const Hexagon: React.FC<HexagonProps> = ({ 
  x, y, value, index, onClick, 
  previewHost, previewPlayer, previewMoveType 
}) => {
  if (value === null) return null;
  
  let backgroundColor = getColorFromValue(value);
  
  // Apply preview styling if this hex has a pending move
  if (previewHost && previewMoveType) {
    backgroundColor = getPreviewColor(value, "host", previewMoveType);
  } else if (previewPlayer && previewMoveType) {
    backgroundColor = getPreviewColor(value, "player", previewMoveType);
  }
  
  return (
    <div
      style={{
        position: "absolute",
        width: `${HEX_WIDTH}px`,
        height: `${HEX_HEIGHT}px`,
        backgroundColor,
        clipPath: "polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)",
        transform: `translate(${x}px, ${y}px)`,
        pointerEvents: "auto",
        cursor: "pointer",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        transition: "background-color 0.3s ease"
      }}
      onMouseDown={(e) => {
        e.preventDefault();
        onClick(index, e.button === 2 ? "right" : "left");
      }}
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* Optional - display the hex value for debugging */}
      <span style={{ color: "#fff", fontWeight: "bold", textShadow: "1px 1px 2px black" }}>
        {value !== 0 ? value : ""}
      </span>
    </div>
  );
};

interface HexGridProps {
  gameCode: string;
  playerId: string;
  playerType: PlayerType;
}

const HexGrid: React.FC<HexGridProps> = ({ gameCode, playerId, playerType }) => {
  const [gameState, setGameState] = useState<GameState>({
    board: initialBoard,
    nextUpdateTime: Date.now() + 5000,
    pendingMoves: {
      host: null,
      player: null
    },
    countdown: 5,
    gameOver: false,
    winner: null
  });
  
  const socketRef = useRef<Socket | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Connect to WebSocket and initialize game
  useEffect(() => {
    // Initialize socket connection
    socketRef.current = io(API_BASE_URL);
    const socket = socketRef.current;

    // Handle socket events
    socket.on('connect', () => {
      console.log('Connected to server');
      // Join the game room
      socket.emit('join_game', { gameCode });
    });

    socket.on('joined', (data) => {
      console.log('Joined game room:', data);
      // Initialize game state with data from server
      if (data && data.board) {
        setGameState(prev => ({
          ...prev,
          board: data.board,
          nextUpdateTime: data.nextUpdateTime * 1000, // Convert to milliseconds
          pendingMoves: data.pendingMoves || { host: null, player: null },
          gameOver: data.gameOver || false,
          winner: data.winner || null
        }));
      }
    });

    socket.on('move_preview', (data) => {
      console.log('Move preview received:', data);
      // Update the pending moves
      setGameState(prev => ({
        ...prev,
        pendingMoves: {
          ...prev.pendingMoves,
          [data.playerType]: data.move
        }
      }));
    });

    socket.on('game_update', (data) => {
      console.log('Game update received:', data);
      // Update the game state with the new board
      if (data && data.board) {
        setGameState(prev => ({
          ...prev,
          board: data.board,
          nextUpdateTime: data.nextUpdateTime * 1000, // Convert to milliseconds
          pendingMoves: data.pendingMoves || { host: null, player: null },
          gameOver: data.gameOver || false,
          winner: data.winner || null
        }));
      }
    });

    socket.on('game_timeout', (data) => {
      console.log('Game timeout:', data);
      alert('Game ended due to inactivity');
      // Redirect to home page or show appropriate UI
    });

    socket.on('error', (data) => {
      console.error('Socket error:', data);
      alert(`Error: ${data.message}`);
    });

    // Start countdown timer
    startCountdownTimer();

    // Cleanup on component unmount
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (socket) {
        socket.disconnect();
      }
    };
  }, [gameCode]);

  // Start a countdown timer for the next move
  const startCountdownTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    timerRef.current = setInterval(() => {
      const now = Date.now();
      const timeRemaining = Math.max(0, Math.floor((gameState.nextUpdateTime - now) / 1000));
      
      setGameState(prev => ({
        ...prev,
        countdown: timeRemaining
      }));
    }, 1000);
  };

  // Handle hex cell clicks
  const handleHexClick: ClickHandler = async (index, button) => {
    // Prevent moves if game is over
    if (gameState.gameOver) {
      alert(gameState.winner === playerType ? 'You won!' : 'You lost!');
      return;
    }
    
    // Handle the click based on button type
    const moveType: MoveType = button === "right" ? "defend" : "claim";
    
    try {
      // Send move to server
      const response = await axios.post(`${API_BASE_URL}/game/move`, {
        gameCode,
        playerId,
        index,
        moveType
      });
      
      console.log('Move response:', response.data);
      
      // Update local game state with pending move (server will also broadcast this via WebSocket)
      setGameState(prev => ({
        ...prev,
        pendingMoves: {
          ...prev.pendingMoves,
          [playerType]: { index, type: moveType }
        }
      }));
    } catch (error) {
      console.error('Error making move:', error);
      if (axios.isAxiosError(error) && error.response) {
        alert(`Error: ${error.response.data.error}`);
      } else {
        alert('Error making move');
      }
    }
  };

  return (
    <div style={{ 
      position: "relative", 
      width: "500px", 
      height: "600px", 
      margin: "50px auto",
      overflow: "hidden" 
    }}>
      {/* Game info overlay */}
      <div style={{ 
        position: "absolute", 
        top: 0, 
        left: 0, 
        right: 0, 
        padding: "10px", 
        backgroundColor: "rgba(0,0,0,0.7)", 
        color: "white",
        textAlign: "center",
        zIndex: 10
      }}>
        {gameState.gameOver ? (
          <h3>Game Over! {gameState.winner === playerType ? 'You Won!' : 'You Lost!'}</h3>
        ) : (
          <>
            <div>Next Move In: {gameState.countdown} seconds</div>
            <div>You are: {playerType === 'host' ? 'Green' : 'Red'}</div>
            <div>Control: Left click to claim, Right click to defend</div>
          </>
        )}
      </div>
      
      {/* Hex grid */}
      {gameState.board.map((value, index) => {
        if (value === null) return null;
        
        // Get the layout coordinates for this hex
        const [col, row] = HEX_LAYOUT[index];
        
        // Calculate position
        const xOffset = col * (HEX_WIDTH * 0.75);
        const yOffset = row * HEX_HEIGHT + (col % 2 === 0 ? HEX_HEIGHT / 2 : 0);

        
        // Check if this cell has a pending move
        const hostMove = gameState.pendingMoves.host;
        const playerMove = gameState.pendingMoves.player;
        const isHostPreview = hostMove?.index === index;
        const isPlayerPreview = playerMove?.index === index;
        
        return (
          <Hexagon
            key={index}
            x={xOffset}
            y={yOffset}
            value={value}
            index={index}
            onClick={handleHexClick}
            previewHost={isHostPreview}
            previewPlayer={isPlayerPreview}
            previewMoveType={isHostPreview ? hostMove?.type : isPlayerPreview ? playerMove?.type : null}
          />
        );
      })}
    </div>
  );
};

export default HexGrid;