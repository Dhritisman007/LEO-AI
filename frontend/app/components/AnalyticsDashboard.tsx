"use client";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, LineChart, Line, Cell,
} from "recharts";
import {
  X, TrendingUp, Zap, Clock, DollarSign,
  CheckCircle2, XCircle, Wrench, Code,
  RefreshCw, Activity,
} from "lucide-react";
import { API_URL } from "../lib/api";

type Overview = {
  period_days: number;
  tasks: { total: number; success: number; error: number; pass_rate: number };
  performance: { avg_duration_seconds: number; avg_steps: number };
  tool_calls: { total: number; success: number; success_rate: number };
  cost: { estimated_usd: number; per_task_avg: number };
};

type DailyData = {
  date: string; total: number; success: number; error: number; cost: number;
};

type Tool = {
  tool: string; total: number; success: number;
  success_rate: number; avg_duration_ms: number;
};

type Task = {
  id: string; task: string; language: string; status: string;
  steps_taken: number; duration_seconds: number;
  tools_used: string[]; created_at: number;
};

type Language = {
  language: string; total: number; success: number; pass_rate: number;
};

const TOOL_COLORS: Record<string, string> = {
  write_file: "#6366f1",
  run_code: "#22c55e",
  run_python: "#22c55e",
  web_search: "#3b82f6",
  read_file: "#a78bfa",
  run_shell: "#f59e0b",
  list_files: "#8b5cf6",
  git_commit_changes: "#ec4899",
  git_push_branch: "#ec4899",
};

const LANG_COLORS: Record<string, string> = {
  python: "#3b82f6",
  javascript: "#f59e0b",
  typescript: "#60a5fa",
  java: "#ef4444",
  cpp: "#8b5cf6",
  go: "#22c55e",
  rust: "#f97316",
  general: "#6b7280",
};

function StatCard({ icon, label, value, sub, color = "#6366f1" }: {
  icon: React.ReactNode; label: string; value: string | number;
  sub?: string; color?: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="stat-card">
      <div className="stat-card__icon" style={{ color, background: `${color}15` }}>{icon}</div>
      <div className="stat-card__body">
        <p className="stat-card__value">{value}</p>
        <p className="stat-card__label">{label}</p>
        {sub && <p className="stat-card__sub">{sub}</p>}
      </div>
    </motion.div>
  );
}

function SectionTitle({ title, icon }: { title: string; icon: React.ReactNode }) {
  return (
    <div className="analytics-section-title">
      {icon}
      <span>{title}</span>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip__label">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }} className="chart-tooltip__value">
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
};

export default function AnalyticsDashboard({
  userId, onClose,
}: {
  userId: string; onClose: () => void;
}) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [daily, setDaily] = useState<DailyData[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(14);
  const [activeTab, setActiveTab] = useState<"overview" | "tasks" | "tools" | "cost">("overview");

  async function fetchAll() {
    setLoading(true);
    try {
      const [ov, da, to, ta, la] = await Promise.all([
        fetch(`${API_URL}/analytics/overview?user_id=${userId}&days=${period}`).then(r => r.json()),
        fetch(`${API_URL}/analytics/daily?user_id=${userId}&days=${period}`).then(r => r.json()),
        fetch(`${API_URL}/analytics/tools?user_id=${userId}&days=${period}`).then(r => r.json()),
        fetch(`${API_URL}/analytics/tasks?user_id=${userId}&limit=20`).then(r => r.json()),
        fetch(`${API_URL}/analytics/languages?user_id=${userId}&days=${period}`).then(r => r.json()),
      ]);
      setOverview(ov);
      setDaily(da.data || []);
      setTools(to.tools || []);
      setTasks(ta.tasks || []);
      setLanguages(la.languages || []);
    } catch (e) {
      console.error("Analytics fetch failed:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchAll(); }, [period]);

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  function timeAgo(ts: number): string {
    const diff = Date.now() - ts * 1000;
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(diff / 3600000);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  }

  return (
    <div className="analytics-overlay">
      <motion.div
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 40 }}
        transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
        className="analytics-panel"
      >
        {/* Header */}
        <div className="analytics-header">
          <div className="analytics-header__left">
            <Activity size={18} className="analytics-header__icon" />
            <span className="analytics-header__title">Analytics</span>
            <div className="analytics-period-select">
              {[7, 14, 30].map((d) => (
                <button
                  key={d}
                  className={`analytics-period-btn ${period === d ? "analytics-period-btn--active" : ""}`}
                  onClick={() => setPeriod(d)}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>
          <div className="analytics-header__right">
            <button onClick={fetchAll} className="analytics-refresh" title="Refresh">
              <RefreshCw size={14} className={loading ? "spin" : ""} />
            </button>
            <button onClick={onClose} className="analytics-close">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="analytics-tabs">
          {(["overview", "tasks", "tools", "cost"] as const).map((tab) => (
            <button
              key={tab}
              className={`analytics-tab ${activeTab === tab ? "analytics-tab--active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="analytics-body">
          {loading ? (
            <div className="analytics-loading">
              <RefreshCw size={20} className="spin" />
              <span>Loading analytics...</span>
            </div>
          ) : !overview || overview.tasks.total === 0 ? (
            <div className="analytics-empty">
              <Activity size={32} />
              <p>No data yet</p>
              <span>Complete a few tasks and come back to see your stats.</span>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
                className="analytics-content"
              >
                {/* ── OVERVIEW TAB ── */}
                {activeTab === "overview" && (
                  <>
                    <div className="stat-grid">
                      <StatCard icon={<Zap size={16} />} label="Total tasks" value={overview.tasks.total} sub={`last ${period} days`} color="#6366f1" />
                      <StatCard icon={<CheckCircle2 size={16} />} label="Pass rate" value={`${overview.tasks.pass_rate}%`} sub={`${overview.tasks.success} succeeded`} color="#22c55e" />
                      <StatCard icon={<Clock size={16} />} label="Avg duration" value={`${overview.performance.avg_duration_seconds}s`} sub={`${overview.performance.avg_steps} steps avg`} color="#f59e0b" />
                      <StatCard icon={<Wrench size={16} />} label="Tool calls" value={overview.tool_calls.total} sub={`${overview.tool_calls.success_rate}% success rate`} color="#3b82f6" />
                    </div>

                    <div className="analytics-chart-card">
                      <SectionTitle title="Daily activity" icon={<TrendingUp size={14} />} />
                      <ResponsiveContainer width="100%" height={160}>
                        <BarChart data={daily} barSize={8} barGap={2}>
                          <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false} interval={Math.floor(daily.length / 5)} />
                          <YAxis hide />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar dataKey="success" name="Success" fill="#22c55e" radius={[3, 3, 0, 0]} />
                          <Bar dataKey="error" name="Error" fill="#ef4444" radius={[3, 3, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {languages.length > 0 && (
                      <div className="analytics-chart-card">
                        <SectionTitle title="Languages used" icon={<Code size={14} />} />
                        <div className="lang-breakdown">
                          {languages.map((lang) => (
                            <div key={lang.language} className="lang-item">
                              <div className="lang-item__header">
                                <div className="lang-item__dot" style={{ background: LANG_COLORS[lang.language] || "#666" }} />
                                <span className="lang-item__name">{lang.language}</span>
                                <span className="lang-item__count">{lang.total} tasks</span>
                                <span className="lang-item__rate">{lang.pass_rate}%</span>
                              </div>
                              <div className="lang-item__bar">
                                <div className="lang-item__fill" style={{ width: `${lang.pass_rate}%`, background: LANG_COLORS[lang.language] || "#666" }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* ── TASKS TAB ── */}
                {activeTab === "tasks" && (
                  <div className="analytics-chart-card">
                    <SectionTitle title="Recent tasks" icon={<Activity size={14} />} />
                    <div className="task-list">
                      {tasks.length === 0 ? (
                        <p className="task-list__empty">No tasks yet</p>
                      ) : tasks.map((t) => (
                        <div key={t.id} className="task-row">
                          <div className={`task-row__status task-row__status--${t.status}`}>
                            {t.status === "success" ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                          </div>
                          <div className="task-row__body">
                            <p className="task-row__task">{t.task}</p>
                            <div className="task-row__meta">
                              {t.language && <span className="task-row__tag task-row__tag--lang">{t.language}</span>}
                              <span className="task-row__tag">{t.steps_taken} steps</span>
                              <span className="task-row__tag">{t.duration_seconds}s</span>
                              <span className="task-row__time">{timeAgo(t.created_at)}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── TOOLS TAB ── */}
                {activeTab === "tools" && (
                  <div className="analytics-chart-card">
                    <SectionTitle title="Tool usage" icon={<Wrench size={14} />} />
                    {tools.length === 0 ? (
                      <p className="task-list__empty">No tool calls recorded yet</p>
                    ) : (
                      <>
                        <ResponsiveContainer width="100%" height={Math.max(180, tools.length * 28)}>
                          <BarChart data={tools} layout="vertical" barSize={10}>
                            <XAxis type="number" hide />
                            <YAxis type="category" dataKey="tool" tick={{ fill: "#555", fontSize: 11 }} axisLine={false} tickLine={false} width={130} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="total" name="Total calls" radius={[0, 4, 4, 0]}>
                              {tools.map((t, i) => (
                                <Cell key={i} fill={TOOL_COLORS[t.tool] || "#6366f1"} opacity={0.85} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                        <div className="tool-table">
                          {tools.map((t) => (
                            <div key={t.tool} className="tool-row">
                              <div className="tool-row__dot" style={{ background: TOOL_COLORS[t.tool] || "#6366f1" }} />
                              <span className="tool-row__name">{t.tool}</span>
                              <span className="tool-row__calls">{t.total}×</span>
                              <span className={`tool-row__rate ${t.success_rate < 70 ? "tool-row__rate--bad" : ""}`}>{t.success_rate}%</span>
                              <span className="tool-row__time">{t.avg_duration_ms}ms</span>
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* ── COST TAB ── */}
                {activeTab === "cost" && (
                  <>
                    <div className="stat-grid">
                      <StatCard icon={<DollarSign size={16} />} label={`Total cost (${period}d)`} value={`$${overview.cost.estimated_usd}`} sub="Gemini API estimate" color="#22c55e" />
                      <StatCard icon={<DollarSign size={16} />} label="Cost per task" value={`$${overview.cost.per_task_avg}`} sub="average" color="#f59e0b" />
                    </div>

                    <div className="analytics-chart-card">
                      <SectionTitle title="Daily cost" icon={<TrendingUp size={14} />} />
                      <ResponsiveContainer width="100%" height={160}>
                        <LineChart data={daily}>
                          <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false} interval={Math.floor(daily.length / 5)} />
                          <YAxis tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v.toFixed(4)}`} width={60} />
                          <Tooltip formatter={(v) => [`$${Number(v).toFixed(5)}`, "Cost"]} contentStyle={{ background: "#161616", border: "1px solid #2a2a2a", borderRadius: "8px", fontSize: "12px" }} />
                          <Line type="monotone" dataKey="cost" stroke="#22c55e" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#22c55e" }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="analytics-chart-card">
                      <SectionTitle title="Pricing reference" icon={<DollarSign size={14} />} />
                      <div className="cost-note">
                        <p>Estimates based on Gemini Flash pricing:</p>
                        <div className="cost-table">
                          <div className="cost-row"><span>Input tokens</span><span>$0.075 / 1M</span></div>
                          <div className="cost-row"><span>Output tokens</span><span>$0.30 / 1M</span></div>
                          <div className="cost-row cost-row--total"><span>Your {period}d total</span><span>${overview.cost.estimated_usd}</span></div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </motion.div>
    </div>
  );
}
