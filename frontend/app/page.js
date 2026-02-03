import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Visitor Monitoring MVP</h1>
      <p>Login to view dashboard.</p>
      <Link href="/login">Go to Login</Link>
    </main>
  );
}
