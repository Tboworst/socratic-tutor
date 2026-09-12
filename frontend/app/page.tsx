"use client";

import { useState } from "react";
import { Hero } from "@/components/Hero";
import { Step } from "@/components/Step";
import {
  ConsolePane,
  EditorPane,
  RunThisPane,
  WantedPane,
} from "@/components/Panes";
import { LadderProgress } from "@/components/LadderProgress";
import { BranchBanner } from "@/components/BranchBanner";
import { Quiz } from "@/components/Quiz";
import { STARTER } from "@/lib/examples";
import {
  ApiError,
  diagnose,
  respond,
  execute,
  STAGE_ORDER,
  type RespondResponse,
} from "@/lib/api";
import ReactMarkdown from "react-markdown";

type Phase = "setup" | "tutoring" | "done";

export default function Home() {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(STARTER);
  const [question, setQuestion] = useState("");
  const [expected, setExpected] = useState("");

  const [output, setOutput] = useState<string | null>(null);
  const [outputFor, setOutputFor] = useState("");
  const [running, setRunning] = useState(false);

  const [phase, setPhase] = useState<Phase>("setup");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [diagnosedCode, setDiagnosedCode] = useState("");
  const [stageIndex, setStageIndex] = useState(0);
  const [prompt, setPrompt] = useState("");
  const [last, setLast] = useState<RespondResponse | null>(null);
  const [runThis, setRunThis] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expired, setExpired] = useState(false);
  const [providerBusy, setProviderBusy] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);

  const canExecute = language === "python";
  const hasRun = output !== null;
  const readyToStart = canExecute ? hasRun : code.trim().length > 0 && code.trim() !== STARTER.trim();
  const drifted = phase === "tutoring" && code.trim() !== diagnosedCode.trim();

  const atExplain = stageIndex === STAGE_ORDER.length - 1;
  const editorEditable = phase !== "tutoring" || atExplain;

  async function handleRun() {
    setError(null);
    setRunning(true);
    try {
      const r = await execute(code);
      setOutput(`${r.stdout}${r.stderr}`.trim() || "(no output)");
      setOutputFor(code);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run the code.");
    } finally {
      setRunning(false);
    }
  }

  async function handleRunSnippet(snippet: string) {
    setError(null);
    setRunning(true);
    try {
      const combined = `${code}\n${snippet}\n`;
      const r = await execute(combined);
      setOutput(`${r.stdout}${r.stderr}`.trim() || "(no output)");
      setOutputFor(combined);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run that snippet.");
    } finally {
      setRunning(false);
    }
  }

  function fullQuestion(): string {
    const parts = [question.trim() || "I'm not sure what's wrong."];
    if (expected.trim()) parts.push(`Expected output:\n${expected.trim()}`);
    if (output) parts.push(`Actual output:\n${output}`);
    return parts.join("\n\n");
  }

  async function handleStart() {
    setBusy(true);
    setError(null);
    setProviderBusy(false);
    try {
      const d = await diagnose(code, fullQuestion(), language);
      setSessionId(d.session_id);
      setDiagnosedCode(code);
      setStageIndex(d.stage_index);
      setPrompt(d.first_message);
      setLast(null);
      setRunThis(null);
      setPhase("tutoring");
    } catch (e) {
      if (e instanceof ApiError && e.status === 503) setProviderBusy(true);
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
    setProviderBusy(false);
    try {
      const r = await respond(
        sessionId,
        iDontKnow ? "" : answer.trim(),
        iDontKnow,
      );
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
      if (e instanceof ApiError && e.status === 503) {
        setProviderBusy(true);
        setError(e.message);
      } else if (e instanceof ApiError && e.status === 404) {
        setExpired(true);
        setError(
          "This session is gone — the tutor server restarted, and sessions live in memory rather than a database. Your code is still here.",
        );
      } else {
        setError(
          e instanceof Error ? e.message : "Could not send your answer.",
        );
      }
    } finally {
      setBusy(false);
    }
  }

  function restart() {
    setPhase("setup");
    setSessionId(null);
    setDiagnosedCode("");
    setStageIndex(0);
    setPrompt("");
    setLast(null);
    setSummary(null);
    setRunThis(null);
    setAnswer("");
    setError(null);
    setExpired(false);
    setProviderBusy(false);
  }

  const banner = error ? (
    <div
      className={`flex flex-wrap items-center gap-4 rounded-lg border px-4 py-3 text-[0.9rem] backdrop-blur-sm ${
        expired || providerBusy
          ? "border-warn/40 bg-warn/[0.08] text-[#F0D6A0]"
          : "border-crit/40 bg-crit/[0.08] text-[#FFC0C0]"
      }`}
    >
      <span className="min-w-0 flex-1">{error}</span>
      {expired && (
        <button
          type="button"
          onClick={restart}
          className="rounded-md bg-warn px-3 py-1.5 font-mono text-xs font-semibold text-[#241A04] transition hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-warn"
        >
          Start over
        </button>
      )}
    </div>
  ) : null;

  /* ---------------------------------------------------------------- setup */

  if (phase === "setup") {
    return (
      <main className="mx-auto max-w-6xl px-6 py-14">
        <Hero />

        {banner && <div className="mt-8">{banner}</div>}

        <div className="mt-14 flex flex-col gap-16">
          <Step
            n={1}
            title="Paste the code that is misbehaving"
            hint="keep it small"
          >
            <div className="flex gap-2 flex-wrap">
              {(["python", "javascript", "java", "cpp"] as const).map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => { setLanguage(lang); setOutput(null); }}
                  className={`rounded px-3 py-1 font-mono text-xs ring-1 ring-inset transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt ${
                    language === lang
                      ? "bg-volt/20 text-volt ring-volt-dim"
                      : "text-muted ring-ink-line-2 hover:text-paper hover:ring-paper/30"
                  }`}
                >
                  {lang === "cpp" ? "C++" : lang.charAt(0).toUpperCase() + lang.slice(1)}
                </button>
              ))}
            </div>
            <EditorPane
              code={code}
              language={language}
              onChange={(v) => {
                setCode(v);
                if (v !== outputFor) setOutput(null);
              }}
              running={running}
              onRun={handleRun}
            />
          </Step>

          <Step
            n={2}
            title="Run it and look"
            hint={
              !canExecute
                ? "execution not available for this language — skip to step 3"
                : hasRun
                ? undefined
                : "press Run above"
            }
            locked={!code.trim() || code.trim() === STARTER.trim()}
            done={hasRun}
          >
            {canExecute ? (
              <>
                <ConsolePane output={output} />
                <p className="max-w-[62ch] text-[0.88rem] leading-relaxed text-muted">
                  Rung diagnoses from what your program actually does, not from
                  what the code looks like. Until it has run, there is nothing
                  to go on.
                </p>
              </>
            ) : (
              <p className="max-w-[62ch] text-[0.88rem] leading-relaxed text-muted">
                In-browser execution is only available for Python right now. The
                tutor can still walk through your {language} code — just skip to
                step 3.
              </p>
            )}
          </Step>

          <Step
            n={3}
            title="Say what you expected"
            locked={!hasRun}
            hint={hasRun ? undefined : "after you run it"}
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <WantedPane expected={expected} onChange={setExpected} />
              <label className="flex flex-col gap-2">
                <span className="eyebrow text-muted-dim">
                  What looks wrong to you?
                </span>
                <textarea
                  id="student-question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  rows={3}
                  placeholder="In your own words. Guessing is fine."
                  className="flex-1 rounded-lg border border-ink-line bg-ink-sunk px-3.5 py-2.5 text-[0.9rem] text-paper placeholder:text-muted-dim transition focus:border-volt-dim focus:outline-none focus:ring-2 focus:ring-volt/20"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-5">
              <button
                type="button"
                onClick={handleStart}
                disabled={busy || !readyToStart}
                className="rounded-lg bg-volt px-6 py-3 font-display text-[0.95rem] font-bold text-[#041020] shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_8px_24px_-8px_rgba(0,0,0,0.6)] transition hover:brightness-110 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
              >
                {busy ? "Reading your code…" : "Start the five questions"}
              </button>
              <p className="max-w-[38ch] text-[0.85rem] leading-snug text-muted-dim">
                It will not fix your code, and it will not hand you the answer.
              </p>
            </div>
          </Step>
        </div>
      </main>
    );
  }

  /* ------------------------------------------------- tutoring and report */

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="sticky top-0 z-10 -mx-6 flex flex-wrap items-baseline justify-between gap-4 border-b border-ink-line bg-ink/80 px-6 pb-5 pt-4 backdrop-blur-md">
        <div className="flex items-baseline gap-4">
          <span className="font-display text-2xl font-extrabold tracking-[-0.03em]">
            Rung
          </span>
          <span className="eyebrow text-muted-dim">
            a tutor that never answers
          </span>
        </div>
        <button
          type="button"
          onClick={restart}
          className="font-mono text-xs text-muted underline decoration-ink-line-2 underline-offset-4 transition hover:text-volt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
        >
          start over
        </button>
      </header>

      {banner && <div className="mt-6">{banner}</div>}

      <section className="mt-7 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <EditorPane
          code={code}
          language={language}
          onChange={(v) => {
            setCode(v);
            if (v !== outputFor) setOutput(null);
          }}
          running={running}
          onRun={handleRun}
          editable={editorEditable}
          lockNote="read-only while the tutor is asking"
          openNote={atExplain ? "open — try the fix and run it" : undefined}
          drifted={drifted}
        />
        <div className="flex min-w-0 flex-col gap-2">
          {runThis && (
            <RunThisPane
              snippet={runThis}
              running={running}
              onRun={() => handleRunSnippet(runThis)}
            />
          )}
          <ConsolePane output={output} />
          <WantedPane
            expected={expected}
            onChange={setExpected}
            editable={false}
            lockNote="locked — set before the first question"
          />
        </div>
      </section>

      <section className="mt-10 border-t border-ink-line pt-8">
        {phase === "tutoring" ? (
          <div className="flex flex-col gap-7">
            <LadderProgress
              stageIndex={stageIndex}
              descents={last?.descents ?? 0}
            />

            {last && (
              <BranchBanner
                branch={last.branch}
                message={last.message}
                saidIDontKnow={last.said_i_dont_know}
              />
            )}

            <div className="rounded-2xl border border-ink-line bg-ink/40 p-6 backdrop-blur-sm">
              <span className="eyebrow text-volt">
                <span className="text-muted-dim">//</span> Question
              </span>
              <p className="mt-3 max-w-[64ch] font-display text-[1.45rem] font-semibold leading-[1.35] tracking-[-0.015em] text-white">
                {prompt}
              </p>

              <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
                <label className="flex flex-col gap-2">
                  <span className="eyebrow text-muted-dim">Your answer</span>
                  <textarea
                    id="answer"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey))
                        submit(false);
                    }}
                    rows={3}
                    placeholder="Say what you think, even if you're not sure. Ctrl + Enter to send."
                    className="rounded-lg border border-ink-line bg-ink-sunk px-3.5 py-2.5 text-[0.95rem] text-paper placeholder:text-muted-dim transition focus:border-volt-dim focus:outline-none focus:ring-2 focus:ring-volt/20"
                  />
                </label>

                <div className="flex flex-col gap-2">
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() => submit(false)}
                      disabled={busy || !answer.trim()}
                      className="rounded-lg bg-volt px-5 py-2.5 font-display text-[0.9rem] font-bold text-[#041020] shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_8px_24px_-8px_rgba(0,0,0,0.6)] transition hover:brightness-110 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
                    >
                      {busy ? "thinking…" : "Answer"}
                    </button>
                    <button
                      type="button"
                      onClick={() => submit(true)}
                      disabled={busy}
                      className="rounded-lg px-4 py-2.5 font-mono text-xs text-muted ring-1 ring-inset ring-ink-line-2 transition hover:text-volt hover:ring-volt-dim disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
                    >
                      I don&apos;t know
                    </button>
                  </div>
                  <p className="max-w-[34ch] text-[0.8rem] leading-snug text-muted-dim">
                    Saying you don&apos;t know drops you a rung. It is never
                    counted against you.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-8">
            <span className="eyebrow text-volt">
              <span className="text-muted-dim">//</span> Session report
            </span>

            <div className="grid gap-3 sm:grid-cols-3">
              <Stat
                label="Rungs used"
                value={`${stageIndex + 1} / ${STAGE_ORDER.length}`}
              />
              <Stat label="Steps of help" value={String(last?.descents ?? 0)} />
              <Stat
                label="Reasoning held up"
                value={last?.reasoning_correct ? "yes" : "not yet"}
                tone={last?.reasoning_correct ? "good" : "warn"}
              />
            </div>

            <div className="rounded-2xl border border-ink-line bg-ink/40 p-6 backdrop-blur-sm">
              <div className="max-w-[74ch] text-[0.97rem] leading-relaxed text-paper/90">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => (
                      <p className="mb-4 last:mb-0">{children}</p>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-white">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-paper/90">{children}</em>
                    ),
                    code: ({ children }) => (
                      <code className="rounded bg-ink-sunk px-1.5 py-0.5 font-mono text-[0.85em] text-volt">
                        {children}
                      </code>
                    ),
                    ul: ({ children }) => (
                      <ul className="mb-4 list-disc pl-5">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="mb-4 list-decimal pl-5">{children}</ol>
                    ),
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                  }}
                >
                  {summary || "No summary returned."}
                </ReactMarkdown>
              </div>
            </div>

            <Quiz code={code} sessionId={sessionId} />

            <button
              type="button"
              onClick={restart}
              className="self-start rounded-lg px-5 py-2.5 font-mono text-xs text-muted ring-1 ring-inset ring-ink-line-2 transition hover:text-volt hover:ring-volt-dim focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
            >
              bring another bug
            </button>
          </div>
        )}
      </section>
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
    tone === "good"
      ? "text-good"
      : tone === "warn"
        ? "text-warn"
        : "text-paper";
  return (
    <div className="rounded-xl border border-ink-line bg-ink/30 p-4 backdrop-blur-sm">
      <span className="eyebrow text-muted-dim">{label}</span>
      <span
        className={`mt-2 block font-display text-3xl font-bold tabular-nums tracking-[-0.02em] ${color}`}
      >
        {value}
      </span>
    </div>
  );
}
