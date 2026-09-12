"use client";

import dynamic from "next/dynamic";
import { python } from "@codemirror/lang-python";

// CodeMirror touches window on import, so keep it off the server render.
const CodeMirror = dynamic(() => import("@uiw/react-codemirror"), {
  ssr: false,
  loading: () => (
    <div className="h-full min-h-[220px] bg-ink-sunk animate-pulse" />
  ),
});

export function CodePanel({
  code,
  onChange,
  output,
  expected,
  running,
  onRun,
  editable,
  runThis,
}: {
  code: string;
  onChange: (v: string) => void;
  output: string | null;
  expected: string;
  running: boolean;
  onRun: () => void;
  editable: boolean;
  runThis: string | null;
}) {
  return (
    <div className="flex flex-col gap-3 min-w-0">
      <div className="flex items-center justify-between gap-3">
        <span className="eyebrow text-muted-dim">main.py</span>
        <button
          type="button"
          onClick={onRun}
          disabled={running}
          className="rounded border border-ink-line bg-ink-raised px-3 py-1.5 font-mono text-xs text-paper hover:border-volt-dim hover:text-volt disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
        >
          {running ? "running…" : "▸ Run"}
        </button>
      </div>

      <div className="overflow-hidden rounded border border-ink-line">
        <CodeMirror
          value={code}
          onChange={onChange}
          extensions={[python()]}
          editable={editable}
          theme="dark"
          basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: true }}
          height="240px"
        />
      </div>

      {runThis && (
        <div className="rounded border border-volt-dim bg-volt/[0.07] px-4 py-3">
          <span className="eyebrow text-volt">Run this and look at the output</span>
          <pre className="mt-2 overflow-x-auto font-mono text-[0.8rem] text-paper/90">
            {runThis}
          </pre>
        </div>
      )}

      <div className="grid gap-2 sm:grid-cols-2">
        <div className="rounded border border-crit/25 bg-crit/[0.06] px-4 py-3 min-w-0">
          <span className="eyebrow text-crit/80">What it prints</span>
          <pre className="mt-2 overflow-x-auto font-mono text-[0.85rem] text-[#FFC0C0]">
            {output ?? "—"}
          </pre>
        </div>
        <div className="rounded border border-good/25 bg-good/[0.05] px-4 py-3 min-w-0">
          <span className="eyebrow text-good/80">What you wanted</span>
          <pre className="mt-2 overflow-x-auto font-mono text-[0.85rem] text-[#A8E8C9]">
            {expected}
          </pre>
        </div>
      </div>
    </div>
  );
}
