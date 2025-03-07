"use client"
import styles from "./page.module.css";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <button 
          className="flex p-1"
          onClick={() => {
            router.push("/host")
          }}>
          Host
        </button>
        <button
          onClick={() => {
            router.push("/join")
          }}>
          Join
        </button>
      </main>
      <footer className={styles.footer}>
        Visit the source code on GitHub
      </footer>
    </div>
  );
}
