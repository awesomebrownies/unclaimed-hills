"use client";

import { useEffect, useState } from "react";
import styles from "../page.module.css";
import axios from "axios";
import { useRouter } from "next/navigation";
import HexGrid from "../hexgrid"; // Assuming HexGrid is in components folder

export default function HostPage() {
  const [gameCode, setGameCode] = useState<string | null>(null);
  const [hostId, setHostId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const API_BASE_URL = "http://127.0.0.1:5000";

  // Create a new game on component mount
  useEffect(() => {
    const createGame = async () => {
      try {
        setIsLoading(true);
        const response = await axios.post(`${API_BASE_URL}/game/create`);
        
        if (response.data && response.data.gameCode) {
          setGameCode(response.data.gameCode);
          setHostId(response.data.hostId);
          setIsLoading(false);
        } else {
          setError("Failed to create game. Please try again.");
          setIsLoading(false);
        }
      } catch (error) {
        setError("An error occurred while creating the game. Please try again.");
        setIsLoading(false);
      }
    };

    createGame();
  }, []);

  // Copy game code to clipboard
  const copyToClipboard = () => {
    if (gameCode) {
      navigator.clipboard.writeText(gameCode);
      // alert("Game code copied to clipboard!");
    }
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <h2>Creating new game...</h2>
          <div className={styles.loader}></div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => router.push("/")}>Return to Home</button>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.gameInfo}>
          <h1>You are hosting a game</h1>
          <div className={styles.codeContainer}>
            <h2>Game Code: <span className={styles.gameCode}>{gameCode}</span></h2>
            <button onClick={copyToClipboard} className={styles.copyButton}>
              Copy Code
            </button>
          </div>
          <p>Share this code with another player to join your game.</p>
          <p>Waiting for player to join...</p>
        </div>

        {gameCode && hostId && (
          <div className={styles.gameContainer}>
            <HexGrid gameCode={gameCode} playerId={hostId} playerType="host" />
          </div>
        )}
      </main>
      <footer className={styles.footer}>Visit the source code on GitHub</footer>
    </div>
  );
}