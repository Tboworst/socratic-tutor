"use client";

import type { Branch } from "@/lib/api";

/**
 * The four outcomes as four distinct states. counter_example gets the loudest
 * treatment: a right answer with wrong reasoning is the symptom of leaning on
 * AI, and a normal tutor just says "correct!" and moves on.
 */
const STYLES: Record<
  Branch,
  { label: string; ring: string; text: string; dot: string }
> = {
  advance: {
    label: "Right — and for the right reason",
    ring: "border-good/40 bg-good/[0.07]",
    text: "text-good",
    dot: "bg-good",
  },
  counter_example: {
    label: "Right answer. Wrong reason.",
    ring: "border-warn/50 bg-warn/[0.09]",
    text: "text-warn",
    dot: "bg-warn",
  },
  nudge: {
    label: "Good thinking — wrong conclusion",
    ring: "border-volt/40 bg-volt/[0.07]",
    text: "text-volt",
    dot: "bg-volt",
  },
  descend: {
    label: "Not it — here's more help",
    ring: "border-ink-line bg-ink-raised",
    text: "text-muted",
    dot: "bg-muted-dim",
  },
  terminate: {
    label: "Session complete",
    ring: "border-volt/40 bg-volt/[0.07]",
    text: "text-volt",
    dot: "bg-volt",
  },
};

export function BranchBanner({
  branch,
  message,
  saidIDontKnow,
}: {
  branch: Branch;
  message: string;
  saidIDontKnow: boolean;
}) {
  const s = STYLES[branch] ?? STYLES.descend;
  const label = saidIDontKnow ? "Honest — that helps" : s.label;

  return (
    <div className={`rounded border px-4 py-3 flex flex-col gap-2 ${s.ring}`}>
      <div className="flex items-center gap-2">
        <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
        <span className={`eyebrow ${s.text}`}>{label}</span>
      </div>
      <p className="text-[0.92rem] leading-relaxed text-paper/90 whitespace-pre-wrap">
        {message}
      </p>
    </div>
  );
}
