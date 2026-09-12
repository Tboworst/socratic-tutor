"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { java } from "@codemirror/lang-java";
import { cpp } from "@codemirror/lang-cpp";
import type { Extension } from "@codemirror/state";

// CodeMirror touches window on import, so keep it off the server render.
const CodeMirror = dynamic(() => import("@uiw/react-codemirror"), {
  ssr: false,
  loading: () => <div className="h-[300px] animate-pulse bg-ink-sunk" />,
});

function langExtension(language: string): Extension[] {
  switch (language) {
    case "javascript": return [javascript()];
    case "java":       return [java()];
    case "cpp":        return [cpp()];
    default:           return [python()];
  }
}

/**
 * The editor. Read-only while the tutor is asking, so the code can't change out
 * from under a diagnosis made from it, and open at the last rung so the student
 * can try the fix. The observation rung runs its snippet via RunThisPane.
 */
const FILE_LABEL: Record<string, string> = {
  python: "main.py",
  javascript: "main.js",
  java: "Main.java",
  cpp: "main.cpp",
};

export function EditorPane({
  code,
  onChange,
  running,
  onRun,
  language = "python",
  editable = true,
  lockNote,
  openNote,
  drifted,
  height = "300px",
}: {
  code: string;
  onChange: (v: string) => void;
  running: boolean;
  onRun: () => void;
  language?: string;
  editable?: boolean;
  lockNote?: string;
  openNote?: string;
  drifted?: boolean;
  height?: string;
}) {
  const fileLabel = FILE_LABEL[language] ?? "main.txt";
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="eyebrow text-muted-dim">{fileLabel}</span>
          {!editable && lockNote && (
            <span className="eyebrow text-muted-dim">{lockNote}</span>
          )}
          {editable && openNote && (
            <span className="eyebrow text-volt">{openNote}</span>
          )}
          {drifted && <span className="eyebrow text-warn/80">edited since diagnosis</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="rounded bg-paper/[0.07] px-3 py-1.5 font-mono text-xs text-muted ring-1 ring-inset ring-ink-line-2 transition-colors hover:text-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
          >
            {copied ? "copied!" : "copy"}
          </button>
          <button
            type="button"
            onClick={onRun}
            disabled={running}
            className="rounded bg-paper/[0.07] px-3.5 py-1.5 font-mono text-xs text-paper ring-1 ring-inset ring-ink-line-2 transition-colors hover:bg-volt/15 hover:text-volt hover:ring-volt-dim disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
          >
            {running ? "running…" : "▸ Run"}
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded border border-ink-line">
        <CodeMirror
          value={code}
          onChange={onChange}
          extensions={langExtension(language)}
          editable={editable}
          theme="dark"
          basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: true }}
          height={height}
        />
      </div>
    </div>
  );
}

/** A readout, not an object — hence a rule rather than a border. */
export function ConsolePane({ output }: { output: string | null }) {
  return (
    <div className="min-w-0 border-l-2 border-crit/50 bg-crit/[0.05] px-4 py-3">
      <span className="eyebrow text-crit/80">Console</span>
      <pre className="mt-2 min-h-[2.6rem] overflow-x-auto whitespace-pre-wrap font-mono text-[1.05rem] leading-snug text-[#FFC0C0]">
        {output ?? <span className="text-muted-dim">nothing yet — press Run</span>}
      </pre>
    </div>
  );
}

/**
 * The student's intent, so it is typed rather than derived — nothing in the
 * program says it was meant to print 15. Free text: an expected result can run
 * several lines, be an error message, or be "it should not crash".
 */
// Locked once the ladder starts: it's the student's stated expectation at
// diagnosis time, so it can't be edited to fit a hint received afterwards.
export function WantedPane({
  expected,
  onChange,
  editable = true,
  lockNote,
}: {
  expected: string;
  onChange: (v: string) => void;
  editable?: boolean;
  lockNote?: string;
}) {
  return (
    <label className="block min-w-0 border-l-2 border-good/50 bg-good/[0.045] px-4 py-3">
      <div className="flex items-baseline gap-3">
        <span className="eyebrow text-good/80">What you wanted</span>
        {!editable && lockNote && (
          <span className="eyebrow text-muted-dim">{lockNote}</span>
        )}
      </div>
      <textarea
        id="expected-output"
        value={expected}
        onChange={(e) => onChange(e.target.value)}
        readOnly={!editable}
        rows={Math.min(4, Math.max(2, expected.split("\n").length))}
        spellCheck={false}
        placeholder="what it should have printed"
        className={`mt-2 block w-full resize-none border-0 bg-transparent p-0 font-mono text-[1.05rem] leading-snug text-[#A8E8C9] placeholder:text-good/30 focus:outline-none ${
          editable ? "" : "cursor-not-allowed opacity-70"
        }`}
      />
    </label>
  );
}

/**
 * The observation rung's snippet. Runs alongside the file rather than being
 * pasted into it, so the diagnosed program stays exactly as it was.
 */
export function RunThisPane({
  snippet,
  onRun,
  running,
}: {
  snippet: string;
  onRun: () => void;
  running: boolean;
}) {
  return (
    <div className="border-l-2 border-volt bg-volt/[0.08] px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <span className="eyebrow text-volt">Run this and look</span>
        <button
          type="button"
          onClick={onRun}
          disabled={running}
          className="rounded bg-volt/20 px-3 py-1 font-mono text-[0.7rem] text-volt ring-1 ring-inset ring-volt-dim hover:bg-volt/30 disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
        >
          {running ? "running…" : "▸ Run it"}
        </button>
      </div>
      <pre className="mt-2 overflow-x-auto font-mono text-[0.85rem] text-paper/90">
        {snippet}
      </pre>
    </div>
  );
}
