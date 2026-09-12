"use client";

import { useState } from "react";
import { generateQuiz, type MCQuestion } from "@/lib/api";

/**
 * The step after the ladder: apply the same concept cold, with no code in
 * front of you. Being told and having understood are different things.
 *
 * The backend pulls concept_gap from the session id, so the questions are
 * about the gap just closed. Each choice reveals at once — a delayed verdict
 * teaches nothing.
 */
export function Quiz({
  code,
  sessionId,
}: {
  code: string;
  sessionId: string | null;
}) {
  const [questions, setQuestions] = useState<MCQuestion[] | null>(null);
  const [chosen, setChosen] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answered = questions?.filter((q) => chosen[q.id]) ?? [];
  const right = answered.filter((q) => chosen[q.id] === q.correct_label).length;
  const done = questions !== null && answered.length === questions.length;

  async function load() {
    setBusy(true);
    setError(null);
    try {
      const r = await generateQuiz(code, sessionId);
      setQuestions(r.mc_questions ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not build the quiz.");
    } finally {
      setBusy(false);
    }
  }

  if (questions === null) {
    return (
      <div className="flex flex-col gap-3 border-t border-ink-line pt-7">
        <span className="eyebrow text-muted-dim">
          <span className="text-muted-dim">//</span> One more thing
        </span>
        <p className="max-w-[58ch] text-[0.95rem] leading-relaxed text-muted">
          You were just walked to that answer. Three questions on the same concept,
          with no code in front of you, will tell you whether it stuck.
        </p>
        {error && (
          <p className="max-w-[58ch] text-[0.88rem] text-[#FFC0C0]">{error}</p>
        )}
        <button
          type="button"
          onClick={load}
          disabled={busy}
          className="mt-1 self-start rounded bg-volt px-5 py-2.5 font-display text-[0.9rem] font-bold text-[#041020] hover:brightness-110 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt"
        >
          {busy ? "Writing your questions…" : "Prove it stuck"}
        </button>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <p className="border-t border-ink-line pt-7 text-[0.9rem] text-muted">
        The quiz came back empty. Nothing lost — the session report above stands.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-7 border-t border-ink-line pt-7">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <span className="eyebrow text-volt">
          <span className="text-muted-dim">//</span> Same concept, no code
        </span>
        <span className="font-mono text-xs tabular-nums text-muted">
          {done ? `${right} of ${questions.length} right` : `${answered.length} of ${questions.length} answered`}
        </span>
      </div>

      {questions.map((q, qi) => {
        const pick = chosen[q.id];
        const locked = Boolean(pick);
        return (
          <div key={q.id} className="flex flex-col gap-3">
            <div className="flex gap-3">
              <span className="font-mono text-[0.72rem] text-volt">
                {String(qi + 1).padStart(2, "0")}
              </span>
              <p className="max-w-[62ch] font-display text-[1.05rem] font-semibold leading-snug">
                {q.prompt}
              </p>
            </div>

            <div className="flex flex-col gap-1.5 pl-[1.9rem]">
              {q.options.map((o) => {
                const isPick = pick === o.label;
                const isRight = o.label === q.correct_label;
                let tone =
                  "bg-ink-raised ring-1 ring-inset ring-ink-line hover:ring-ink-line-2";
                if (locked && isRight) {
                  tone = "bg-good/[0.09] ring-1 ring-inset ring-good/50";
                } else if (locked && isPick) {
                  tone = "bg-crit/[0.08] ring-1 ring-inset ring-crit/45";
                } else if (locked) {
                  tone = "bg-ink-raised/50 ring-1 ring-inset ring-ink-line opacity-55";
                }
                return (
                  <button
                    key={o.label}
                    type="button"
                    disabled={locked}
                    onClick={() => setChosen((c) => ({ ...c, [q.id]: o.label }))}
                    className={`flex items-baseline gap-3 rounded px-4 py-2.5 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-volt ${tone}`}
                  >
                    <span className="font-mono text-[0.72rem] text-muted-dim">
                      {o.label}
                    </span>
                    <span className="text-[0.92rem] leading-snug">{o.text}</span>
                    {locked && isRight && (
                      <span className="ml-auto font-mono text-[0.7rem] text-good">
                        correct
                      </span>
                    )}
                    {locked && isPick && !isRight && (
                      <span className="ml-auto font-mono text-[0.7rem] text-crit">
                        you picked this
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {locked && (
              <p className="ml-[1.9rem] max-w-[62ch] border-l-2 border-volt-dim pl-4 text-[0.9rem] leading-relaxed text-paper/85">
                {q.explanation}
              </p>
            )}
          </div>
        );
      })}

      {done && (
        <p className="max-w-[58ch] text-[0.95rem] leading-relaxed text-muted">
          {right === questions.length
            ? "All three. You did not just get walked to an answer — you can use the idea."
            : "Worth another look at the concept above. Getting walked to an answer is not the same as owning it, which is the whole point of asking."}
        </p>
      )}
    </div>
  );
}
