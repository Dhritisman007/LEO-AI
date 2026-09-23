"use client";

// Tracks whether calls to the LEO API are currently failing with a network
// error (backend unreachable), and transparently retries them until the
// backend comes back — so the original caller's fetch() just resolves late
// instead of rejecting, and the rest of the app never has to know it happened.

type Listener = () => void;

const RETRY_DELAY_MS = 5000;

let offlineCount = 0;
let patched = false;
const listeners = new Set<Listener>();

function emit() {
  listeners.forEach((listener) => listener());
}

function markRetrying(delta: number) {
  const next = Math.max(0, offlineCount + delta);
  if (next !== offlineCount) {
    offlineCount = next;
    emit();
  }
}

export function subscribeNetworkStatus(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getNetworkOffline() {
  return offlineCount > 0;
}

export function getNetworkOfflineServerSnapshot() {
  return false;
}

/** Wraps window.fetch so any request to `apiOrigin` that fails with a
 * network error (backend unreachable) is retried every 5s until it
 * succeeds, resolving the original caller's promise once it does. Safe to
 * call multiple times — only patches once. */
export function initResilientFetch(apiOrigin: string) {
  if (patched || typeof window === "undefined") return;
  patched = true;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
        ? input.toString()
        : input.url;

    if (!url.startsWith(apiOrigin)) {
      return originalFetch(input, init);
    }

    try {
      return await originalFetch(input, init);
    } catch {
      // fetch only throws on genuine network failures (DNS, connection
      // refused, offline) — an HTTP error status resolves normally and
      // never reaches here.
      markRetrying(1);
      try {
        // eslint-disable-next-line no-constant-condition
        while (true) {
          await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
          try {
            return await originalFetch(input, init);
          } catch {
            // keep retrying
          }
        }
      } finally {
        markRetrying(-1);
      }
    }
  };
}
