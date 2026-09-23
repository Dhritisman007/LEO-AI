import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { createHmac } from "crypto";
import { authOptions } from "../../lib/authOptions";

// Mints a short-lived JWT (HS256, signed with NEXTAUTH_SECRET) that the
// LEO backend can verify to confirm a request really comes from the
// currently signed-in user — used for authenticated download links, since
// the backend (a separate origin) never sees the NextAuth session cookie.

function base64url(input: Buffer | string): string {
  return Buffer.from(input)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function signBackendToken(userId: string, secret: string): string {
  const header = { alg: "HS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const payload = { sub: userId, iat: now, exp: now + 300 }; // 5 minutes

  const encodedHeader = base64url(JSON.stringify(header));
  const encodedPayload = base64url(JSON.stringify(payload));
  const signingInput = `${encodedHeader}.${encodedPayload}`;
  const signature = base64url(createHmac("sha256", secret).update(signingInput).digest());

  return `${signingInput}.${signature}`;
}

export async function GET() {
  const session = await getServerSession(authOptions);
  const userId = (session?.user as any)?.id;

  if (!userId) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }

  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    return NextResponse.json({ error: "Server misconfigured" }, { status: 500 });
  }

  return NextResponse.json({ token: signBackendToken(userId, secret) });
}
