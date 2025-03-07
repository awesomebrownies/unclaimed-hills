"use client";
import styles from "../page.module.css";
import { FormEvent, useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

export default function Home() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [gameCode, setGameCode] = useState<string>("");
  const router = useRouter();

  const API_BASE_URL = "http://127.0.0.1:5000";

  // Typing the joinGame function and the API response data.
  const joinGame = async (gameCode: string): Promise<void> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/game/join`, {
        gameCode: gameCode,
      });
      // Assuming the API returns a success response for a successful join.
      if (response.status === 200) {
        // Navigate to a different page (update as necessary)
        router.push(
          `/play?gameCode=${gameCode}&playerId=${response.data.playerId}`
        );
      } else {
        setErrorMessage("Failed to join the game. Please check the code.");
      }
    } catch (error) {
      setErrorMessage(
        "An error occurred while joining the game. Please try again."
      );
    }
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    joinGame(gameCode);
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>Input Game Code</h1>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            name="code"
            placeholder="Enter Game Code"
            value={gameCode}
            onChange={(e) => setGameCode(e.target.value)}
            required
          />
          <input type="submit" value="Join Game" />
        </form>
        {errorMessage && (
          <div className={styles.errorMessage}>{errorMessage}</div>
        )}
      </main>
    </div>
  );
}
