"use client";
import { Circle, CircleDot, CheckCircle2, XCircle } from "lucide-react";
import { PlanStep } from "../types";

function statusIcon(status: string) {
    if (status === "done") return <CheckCircle2 size={14} className="text-emerald-400" />;
    if (status === "in_progress") return <CircleDot size={14} className="text-blue-400 animate-pulse" />;
    if (status === "failed") return <XCircle size={14} className="text-red-400" />;
    return <Circle size={14} className="text-zinc-600" />;
}

function statusTextColor(status: string) {
    if (status === "done") return "text-zinc-400 line-through";
    if (status === "in_progress") return "text-white font-medium";
    if (status === "failed") return "text-red-400";
    return "text-zinc-500";
}

export default function PlanTracker({ plan }: { plan: PlanStep[] }) {
    if (!plan || plan.length === 0) return null;

    const doneCount = plan.filter((p) => p.status === "done").length;

    return (
        <div className="border border-zinc-800 bg-zinc-900/50 rounded-lg p-3 mb-3">
            <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide">
                    Plan
                </span>
                <span className="text-[11px] text-zinc-500">
                    {doneCount}/{plan.length}
                </span>
            </div>
            <div className="flex flex-col gap-1.5">
                {plan.map((p) => (
                    <div key={p.id} className="flex items-start gap-2 text-xs">
                        {statusIcon(p.status)}
                        <span className={statusTextColor(p.status)}>{p.description}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}