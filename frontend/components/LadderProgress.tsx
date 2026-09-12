"use client";

import { STAGE_ORDER, STAGE_LABEL, type SocraticStage } from "@/lib/api";

/**
 * The rung counter. Always visible, and that is the point: difficulty does not
 * frustrate people, open-ended interrogation does. Seeing "3 of 5" tells the
 * student this ends.
 */
export function LadderProgress({
  stageIndex,
  descents,
}: {
  stageIndex: number;
  descents: number;
}) {
  const current: SocraticStage = STAGE_ORDER[stageIndex] ?? "explain";

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <span className="eyebrow text-volt">
          Rung {stageIndex + 1} of {STAGE_ORDER.length} · {STAGE_LABEL[current]}
        </span>
        {descents > 0 && (
          <span className="eyebrow text-muted-dim">
            {descents} step{descents === 1 ? "" : "s"} of help
          </span>
        )}
      </div>

      <div className="flex gap-1.5" aria-hidden="true">
        {STAGE_ORDER.map((stage, i) => (
          <div
            key={stage}
            className={[
              "h-1 flex-1 rounded-full transition-colors",
              i < stageIndex ? "bg-volt-dim" : i === stageIndex ? "bg-volt" : "bg-ink-line",
            ].join(" ")}
          />
        ))}
      </div>
    </div>
  );
}
