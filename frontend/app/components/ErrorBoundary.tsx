"use client";
import { Component, type ErrorInfo, type ReactNode } from "react";
import { Zap } from "lucide-react";

type Props = { children: ReactNode };
type State = { hasError: boolean };

// Catches unexpected render-time crashes anywhere in the app (not network
// errors — fetch failures never throw during render, they're handled by
// NetworkStatusBanner/networkStatus.ts instead). A real render crash
// unmounts the broken subtree, so this can only show a minimal recovery
// screen, not the underlying chat history.
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("LEO crashed:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="leo-crash-screen">
          <Zap size={28} className="leo-crash-screen__icon" fill="currentColor" fillOpacity={0.2} />
          <h1 className="leo-crash-screen__title">Something went wrong</h1>
          <p className="leo-crash-screen__note">
            LEO hit an unexpected error. Reloading usually fixes it — your conversations are saved.
          </p>
          <button
            className="leo-crash-screen__button"
            onClick={() => window.location.reload()}
          >
            Reload
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
