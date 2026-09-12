"use client";

import { useState } from "react";
import { CodePanel } from "@/components/CodePanel";
import { LadderProgress } from "@/components/LadderProgress";
import { BranchBanner } from "@/components/BranchBanner";
import { EXAMPLES, findExample, type Example } from "@/lib/examples";
import {
  diagnose,
  respond,
  execute,
  STAGE_ORDER,
  type RespondResponse,
} from "@/lib/api";

type Phase = "setup" | "tutoring" | "done";

export default function Home() {
  const [example, setExample] = useState<Example>(EXAMPLES[0]);
  const [code, setCode] = useState(EXAMPLES[0].code);
  const [question, setQuestion] = useState(EXAMPLES[0].studentQuestion);

  // The page opens on a program that has already been run and is already wrong.
  const [output, setOutput] = useState<string | null>(EXAMPLES[0].actualOutput);
  const [running, setRunning] = useState(false);

  const [phase, setPhase] = useState<Phase>("setup");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [last, setLast] = useState<RespondResponse | null>(null);
  const [runThis, setRunThis] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);

  function pickExample(ex: Example) {
    setExample(ex);
    setCode(ex.code);
    setQuestion(ex.studentQuestion);
    setOutput(ex.actualOutput);
    setError(null);
  }

  async function handleRun() {
    setError(null);
    // Seeded examples carry their verified output, so this is instant and
    // cannot be broken by the execution service being slow or rate-limited.
    const seeded = findExample(code);
    if (seeded) {
      setOutput(seeded.actualOutput);
      return;
    }
    setRunning(true);
    try {
      const r = await execute(code);
      setOutput(r.stderr ? `${r.stdout}${r.stderr}`.trim() : r.stdout.trim() || "(no output)");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run the code.");
    } finally {
      setRunning(false);
    }
  }

  async function handleStart() {
    setBusy(true);
    setError(null);
    try {
      const d = await diagnose(code, question);
      setSessionId(d.session_id);
      setStageIndex(d.stage_index);
      setPrompt(d.first_message);
      setLast(null);
      setRunThis(null);
      setPhase("tutoring");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start the session.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(iDontKnow: boolean) {
    if (!sessionId) return;
    if (!iDontKnow && !answer.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const r = await respond(sessionId, iDontKnow ? "" : answer.trim(), iDontKnow);
      setLast(r);
      setStageIndex(r.stage_index);
      setRunThis(r.run_this);
      setAnswer("");
      if (r.is_complete) {
        setSummary(r.summary ?? "");
        setPhase("done");
      } else if (r.question) {
        setPrompt(r.question);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not send your answer.");
    } finally {
      setBusy(false);
    }
  }

  function restart() {
    setPhase("setup");
    setSessionId(null);
    setStageIndex(0);
    setPrompt("");
    setLast(null);
    setSummary(null);
    setRunThis(null);
    setAnswer("");
    setError(null);
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="flex flex-col gap-3 border-b border-ink-line pb-7">
        <span className="eyebrow text-volt">
          <span className="text-muted-dim">//</span> LILO Summer Academy · Track 02
        </span>
        <h1 className="font-display text-4xl font-extrabold tracking-tight sm:text-5xl">
          Rung
        </h1>
        <p className="max-w-[52ch] text-[0.98rem] leading-relaxed text-paper/75">
          A tutor that never answers. It diagnoses your bug in silence, then walks you
          down five questions until you find it — and checks you found it for the{" "}
          <span className="text-volt">right reason</span>.
        </p>
      </header>

      {error && (
        <div className="mt-6 rounded border border-crit/40 bg-crit/[0.08] px-4 py-3 text-[0.9rem] text-[#FFC0C0]">
          {error}
        </div>
      )}

      {phase === "done" ? (
        <section className="mt-8 flex flex-col gap-5">
          <span className="eyebrow text-volt">
            <span className="text-muted-dim">//</span> Session report
          </span>
          <div className="rounded border border-ink-line bg-ink-raised px-6 py-5">
            <pre className="whitespace-pre-wrap font-sans text-[0.95rem] leading-relaxed text-paper/90">
              {summary || "No summary returned."}
            </pre>
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            <Stat label="Rungs used" value={`${stageIndex + 1} / ${STAGE_ORDER.length}`} />
            <Stat label="Steps of help" value={String(last?.descents ?? 0)} />
            <Stat
              label="Reasoning held up"
              value={last?.reasoning_correct ? "yes" : "not yet"}
              tone={last?.reasoning_correct ? "good" : "warn"}
            />
          </div>
          <button
            type="button"
            onClick={restart}
            className="self-start rounded bg-volt px-4 py-2 font-mono text-xs font-semibold text-[#041020] hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
          >
            Try another
          </button>
        </section>
      ) : (
        <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_1fr]">
          <CodePanel
            code={code}
            onChange={setCode}
            output={output}
            expected={example.expectedOutput}
            running={running}
            onRun={handleRun}
            editable={phase === "setup"}
            runThis={runThis}
          />

          <section className="flex min-w-0 flex-col gap-4">
            {phase === "setup" ? (
              <>
                <span className="eyebrow text-muted-dim">
                  <span className="text-muted-dim">//</span> Pick something broken
                </span>
                <div className="flex flex-col gap-2">
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex.id}
                      type="button"
                      onClick={() => pickExample(ex)}
                      className={[
                        "rounded border px-4 py-3 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt",
                        ex.id === example.id
                          ? "border-volt-dim bg-volt/[0.07]"
                          : "border-ink-line bg-ink-raised hover:border-ink-line/80",
                      ].join(" ")}
                    >
                      <span className="font-display text-[0.95rem] font-bold">{ex.label}</span>
                      <span className="mt-1 block text-[0.85rem] text-muted">
                        prints <span className="font-mono text-[#FFC0C0]">{ex.actualOutput.split("\n")[0]}</span>
                        {" · wanted "}
                        <span className="font-mono text-[#A8E8C9]">{ex.expectedOutput.split("\n")[0]}</span>
                      </span>
                    </button>
                  ))}
                </div>

                <label className="mt-1 flex flex-col gap-2">
                  <span className="eyebrow text-muted-dim">What looks wrong to you?</span>
                  <textarea
                    id="student-question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    rows={3}
                    className="rounded border border-ink-line bg-ink-sunk px-3 py-2 text-[0.9rem] text-paper placeholder:text-muted-dim focus:border-volt-dim focus:outline-none"
                  />
                </label>

                <button
                  type="button"
                  onClick={handleStart}
                  disabled={busy}
                  className="self-start rounded bg-volt px-5 py-2.5 font-mono text-xs font-semibold text-[#041020] hover:brightness-110 disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
                >
                  {busy ? "diagnosing…" : "Help me understand it"}
                </button>
                <p className="text-[0.82rem] text-muted-dim">
                  It will not fix your code and it will not hand you the answer.
                </p>
              </>
            ) : (
              <>
                <LadderProgress stageIndex={stageIndex} descents={last?.descents ?? 0} />

                {last && (
                  <BranchBanner
                    branch={last.branch}
                    message={last.message}
                    saidIDontKnow={last.said_i_dont_know}
                  />
                )}

                <div className="rounded border border-ink-line bg-ink-raised px-5 py-4">
                  <p className="text-[1.02rem] font-medium leading-relaxed text-white">
                    {prompt}
                  </p>
                </div>

                <label className="flex flex-col gap-2">
                  <span className="eyebrow text-muted-dim">Your answer</span>
                  <textarea
                    id="answer"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(false);
                    }}
                    rows={4}
                    placeholder="Say what you think, even if you're not sure."
                    className="rounded border border-ink-line bg-ink-sunk px-3 py-2 text-[0.92rem] text-paper placeholder:text-muted-dim focus:border-volt-dim focus:outline-none"
                  />
                </label>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => submit(false)}
                    disabled={busy || !answer.trim()}
                    className="rounded bg-volt px-5 py-2.5 font-mono text-xs font-semibold text-[#041020] hover:brightness-110 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
                  >
                    {busy ? "thinking…" : "Answer"}
                  </button>
                  <button
                    type="button"
                    onClick={() => submit(true)}
                    disabled={busy}
                    className="rounded border border-ink-line bg-ink-raised px-4 py-2.5 font-mono text-xs text-muted hover:border-volt-dim hover:text-volt disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
                  >
                    I don&apos;t know
                  </button>
                </div>
                <p className="text-[0.82rem] text-muted-dim">
                  Saying you don&apos;t know drops you a rung. It is never counted against you.
                </p>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "good" | "warn";
}) {
  const color =
    tone === "good" ? "text-good" : tone === "warn" ? "text-warn" : "text-paper";
  return (
    <div className="rounded border border-ink-line bg-ink-sunk px-4 py-3">
      <span className="eyebrow text-muted-dim">{label}</span>
      <span className={`mt-1 block font-display text-xl font-bold tabular-nums ${color}`}>
        {value}
      </span>
    </div>
  );
}
