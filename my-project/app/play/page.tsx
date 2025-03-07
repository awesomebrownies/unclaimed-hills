"use client";

import { useEffect, useState } from "react";
import styles from "../page.module.css";
import { useRouter, useSearchParams } from "next/navigation";
import HexGrid from "../hexgrid"; // Assuming HexGrid is in components folder

export default function PlayPage() {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Get gameCode and playerId from URL parameters
  const gameCode = searchParams?.get("gameCode");
  const playerId = searchParams?.get("playerId");

  useEffect(() => {
    // Validate that we have required parameters
    if (!gameCode || !playerId) {
      setError("Missing required game information. Please join the game again.");
      setIsLoading(false);
      return;
    }

    // Set loading to false once we have all required data
    setIsLoading(false);
  }, [gameCode, playerId]);

  if (isLoading) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <h2>Loading game...</h2>
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
          <h1>You have joined a game</h1>
          <h2>Game Code: <span className={styles.gameCode}>{gameCode}</span></h2>
        </div>

        {gameCode && playerId && (
          <div className={styles.gameContainer}>
            <HexGrid 
              gameCode={gameCode} 
              playerId={playerId} 
              playerType="player" 
            />
          </div>
        )}
      </main>
    </div>
  );
}