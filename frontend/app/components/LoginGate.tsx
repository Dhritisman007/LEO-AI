"use client";
import { useSession, signIn, signOut } from "next-auth/react";
import { Bot } from "lucide-react";

export default function LoginGate({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="h-screen flex items-center justify-center bg-zinc-950 text-zinc-500">
        Loading...
      </div>
    );
  }

  if (!session) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-zinc-950 text-white gap-4">
        <Bot size={48} className="text-zinc-300" />
        <h1 className="text-2xl font-bold">LEO</h1>
        <p className="text-zinc-500 text-sm">Sign in to start your own session</p>
        <button
          onClick={() => signIn("github", { callbackUrl: "/" })}
          className="bg-white text-black font-semibold px-5 py-2.5 rounded-lg hover:bg-zinc-200 transition text-sm"
        >
          Sign in with GitHub
        </button>
      </div>
    );
  }

  // Render children only — user info is shown in the main header
  return <>{children}</>;
}
