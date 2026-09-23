"use client";
import { useState, type ReactElement } from "react";
import { Check, Copy } from "lucide-react";
import SyntaxHighlighter from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="code-block">
      <div className="code-block__header">
        <span className="code-block__lang">{language || "code"}</span>
        <button className="code-block__copy" onClick={handleCopy}>
          {copied
            ? <><Check size={11} /> Copied</>
            : <><Copy size={11} /> Copy</>
          }
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={atomOneDark}
        customStyle={{
          margin: 0,
          padding: "14px 16px",
          background: "#0d0d0d",
          fontSize: "12.5px",
          lineHeight: "1.65",
          borderRadius: "0 0 10px 10px",
          border: "none",
        }}
        showLineNumbers={code.split("\n").length > 5}
        lineNumberStyle={{
          color: "#333",
          minWidth: "2.5em",
          paddingRight: "12px",
          userSelect: "none",
        }}
      >
        {code.trim()}
      </SyntaxHighlighter>
    </div>
  );
}

function InlineCode({ code }: { code: string }) {
  return <code className="inline-code">{code}</code>;
}

function Heading({ level, keyNum, children }: { level: number; keyNum: number; children: (string | ReactElement)[] }) {
  const className = `msg-heading msg-heading--${level}`;
  switch (level) {
    case 1: return <h1 key={keyNum} className={className}>{children}</h1>;
    case 2: return <h2 key={keyNum} className={className}>{children}</h2>;
    case 3: return <h3 key={keyNum} className={className}>{children}</h3>;
    case 4: return <h4 key={keyNum} className={className}>{children}</h4>;
    case 5: return <h5 key={keyNum} className={className}>{children}</h5>;
    default: return <h6 key={keyNum} className={className}>{children}</h6>;
  }
}

function parseLine(line: string, key: number) {
  // Handle bold: **text**
  const boldRegex = /\*\*(.*?)\*\*/g;
  // Handle inline code: `code`
  const codeRegex = /`([^`]+)`/g;

  let result: (string | ReactElement)[] = [];
  let lastIndex = 0;
  let match;

  // Combined regex for both patterns
  const combined = /\*\*(.*?)\*\*|`([^`]+)`/g;

  while ((match = combined.exec(line)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      result.push(line.slice(lastIndex, match.index));
    }

    if (match[1] !== undefined) {
      // Bold
      result.push(<strong key={`b-${key}-${match.index}`} className="msg-bold">{match[1]}</strong>);
    } else if (match[2] !== undefined) {
      // Inline code
      result.push(<InlineCode key={`c-${key}-${match.index}`} code={match[2]} />);
    }

    lastIndex = match.index + match[0].length;
  }

  // Remaining text
  if (lastIndex < line.length) {
    result.push(line.slice(lastIndex));
  }

  return result.length > 0 ? result : [line];
}

export default function MessageContent({ content }: { content: string }) {
  if (!content) return null;

  const parts: ReactElement[] = [];
  const lines = content.split("\n");
  let i = 0;
  let partKey = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block: ```language
    if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;

      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```

      parts.push(
        <CodeBlock
          key={partKey++}
          code={codeLines.join("\n")}
          language={language}
        />
      );
      continue;
    }

    // Headers: # through ######
    const headerMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      parts.push(
        <Heading key={partKey} level={level} keyNum={partKey}>
          {parseLine(headerMatch[2], partKey)}
        </Heading>
      );
      partKey++;
      i++;
      continue;
    }

    // Numbered list: 1. item
    if (/^\d+\.\s/.test(line)) {
      parts.push(
        <div key={partKey++} className="msg-list-item">
          <span className="msg-list-num">{line.match(/^\d+/)?.[0]}.</span>
          <span>{parseLine(line.replace(/^\d+\.\s/, ""), partKey)}</span>
        </div>
      );
      i++;
      continue;
    }

    // Bullet: - item or • item
    if (/^[-•]\s/.test(line)) {
      parts.push(
        <div key={partKey++} className="msg-bullet">
          <span className="msg-bullet-dot">·</span>
          <span>{parseLine(line.replace(/^[-•]\s/, ""), partKey)}</span>
        </div>
      );
      i++;
      continue;
    }

    // Empty line → spacing
    if (!line.trim()) {
      parts.push(<div key={partKey++} className="msg-spacer" />);
      i++;
      continue;
    }

    // Regular paragraph line
    parts.push(
      <p key={partKey++} className="msg-paragraph">
        {parseLine(line, partKey)}
      </p>
    );
    i++;
  }

  return <div className="msg-content">{parts}</div>;
}
