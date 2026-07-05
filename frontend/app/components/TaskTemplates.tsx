"use client";

const TEMPLATES = [
  {
    label: "🔢 Sort a list",
    prompt: "Write a Python script that sorts [5, 2, 8, 1, 9, 3] and prints the result. Run it."
  },
  {
    label: "🌐 Build a REST API",
    prompt: "Write a simple Python Flask REST API with one endpoint GET /hello that returns {message: 'Hello from LEO'}. Save it as app.py."
  },
  {
    label: "🧪 Write unit tests",
    prompt: "Write a Python function called multiply(a, b) and write 3 unit tests for it using pytest. Save as test_multiply.py and run the tests."
  },
  {
    label: "📊 Data analysis",
    prompt: "Write a Python script that takes [23, 45, 12, 67, 34, 89, 11, 56] and prints the mean, median, max, min, and standard deviation. Run it."
  },
  {
    label: "🔍 Web scraper",
    prompt: "Write a Python script using requests and BeautifulSoup that scrapes the titles from https://news.ycombinator.com and prints the first 5. Save as scraper.py."
  },
  {
    label: "🔐 Password generator",
    prompt: "Write a Python script that generates a secure random password with 16 characters including uppercase, lowercase, numbers, and symbols. Run it."
  },
  {
    label: "📁 File organizer",
    prompt: "Write a Python script that creates 5 sample files with different extensions (.txt, .py, .json, .csv, .md) in the workspace, then organizes them into subfolders by extension."
  },
  {
    label: "🧮 Fibonacci",
    prompt: "Write a Python function that generates the first 20 Fibonacci numbers and prints them. Save as fib.py and run it."
  },
];

export default function TaskTemplates({
  onSelect,
  visible,
}: {
  onSelect: (prompt: string) => void;
  visible: boolean;
}) {
  if (!visible) return null;

  return (
    <div className="px-4 pb-3">
      <p className="text-[11px] text-zinc-600 uppercase tracking-widest mb-2 ml-1">
        Quick start
      </p>
      <div className="flex flex-wrap gap-2">
        {TEMPLATES.map((t) => (
          <button
            key={t.label}
            onClick={() => onSelect(t.prompt)}
            className="text-xs bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-500 text-zinc-300 rounded-lg px-3 py-1.5 transition whitespace-nowrap"
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}
