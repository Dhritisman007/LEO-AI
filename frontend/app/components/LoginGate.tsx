"use client";
import { useSession, signIn, signOut } from "next-auth/react";

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
        <span className="text-5xl">🐐</span>
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

  return (
    <div className="relative h-full">
      <div className="absolute top-3 right-3 z-30 flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-full pl-1 pr-3 py-1">
        {session.user?.image && (
          <img src={session.user.image} className="w-6 h-6 rounded-full" alt="avatar" />
        )}
        <span className="text-xs text-zinc-300">{session.user?.name}</span>
        <button
          onClick={() => signOut()}
          className="text-xs text-zinc-500 hover:text-red-400 ml-1"
        >
          Sign out
        </button>
      </div>
      {children}
    </div>
  );
}
