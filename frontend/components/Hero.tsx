import { STAGE_LABEL, STAGE_ORDER } from "@/lib/api";

/** What each rung hands over. The bars grow because each gives more than the last. */
const GIVES: Record<string, string> = {
  orientation: "points at the neighbourhood",
  localization: "narrows it to one line",
  observation: "makes you run it and look",
  naming: "names the concept, not the fix",
  explain: "explains, then retests you",
};

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-ink-line pb-20">
      {/* ambient glows */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-32 left-[-10%] h-[480px] w-[480px] rounded-full bg-volt/[0.07] blur-[130px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-20%] right-[-5%] h-[420px] w-[420px] rounded-full bg-volt/[0.05] blur-[120px]"
      />

      <div className="relative flex flex-col gap-14">
        {/* ── SITE IDENTITY ───────────────────────────── */}
        <header className="flex flex-col items-center gap-6 pt-10 text-center">
          <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-ink-line bg-ink/40 px-4 py-1.5 text-muted backdrop-blur-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-volt" />
            LILO Summer Academy · Track 02
          </span>

          <h1 className="font-display text-[7rem] font-extrabold leading-[0.85] tracking-[-0.06em] sm:text-[9rem] lg:text-[11rem]">
            <span className="bg-gradient-to-b from-paper via-paper to-paper/30 bg-clip-text text-transparent">
              Rung
            </span>
          </h1>

          <div className="flex items-center gap-3 text-muted-dim">
            <span className="h-px w-12 bg-ink-line" />
            <span className="font-mono text-[0.7rem] uppercase tracking-[0.35em]">
              a tutor that never answers
            </span>
            <span className="h-px w-12 bg-ink-line" />
          </div>
        </header>

        {/* ── PITCH + RUNGS ───────────────────────────── */}
        <div className="grid gap-12 lg:grid-cols-[1.15fr_1fr] lg:gap-20">
          {/* LEFT — pitch */}
          <div className="flex flex-col gap-7">
            <p className="max-w-[30ch] font-display text-2xl font-semibold leading-[1.25] tracking-[-0.02em] text-paper sm:text-[1.75rem]">
              Everyone is learning to make AI write their code.{" "}
              <span className="relative inline-block text-volt">
                Nobody is learning to do without it.
                <span
                  aria-hidden
                  className="absolute -bottom-0.5 left-0 h-[2px] w-full bg-volt/40"
                />
              </span>
            </p>

            <p className="max-w-[54ch] text-[0.97rem] leading-relaxed text-muted">
              Rung is a tutor that never answers. It reads your broken program,
              works out which idea you are missing, and then asks you five
              questions — one at a time, each giving a little more away than the
              last — until you find it yourself.
            </p>

            <p className="max-w-[54ch] rounded-r-lg border-l-2 border-volt bg-volt/[0.04] py-3 pl-4 pr-3 text-[0.95rem] leading-relaxed text-paper/85">
              And it checks your reasoning, not just your answer. Getting it
              right for the wrong reason is the exact symptom of leaning on AI,
              so that is the one case Rung refuses to let pass.
            </p>
          </div>

          {/* RIGHT — the five rungs */}
          <div className="flex flex-col gap-5">
            <span className="eyebrow flex items-center gap-2 text-muted-dim">
              <span className="text-muted-dim">//</span>
              <span className="tracking-[0.18em]">The five rungs</span>
            </span>

            <ol className="flex flex-col divide-y divide-ink-line overflow-hidden rounded-xl border border-ink-line bg-ink/40 backdrop-blur-sm">
              {STAGE_ORDER.map((stage, i) => (
                <li
                  key={stage}
                  className="group flex flex-col gap-2 px-4 py-4 transition-colors hover:bg-volt/[0.03]"
                >
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-[0.7rem] tabular-nums text-volt">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-display text-[1rem] font-bold tracking-[-0.01em]">
                      {STAGE_LABEL[stage]}
                    </span>
                  </div>

                  <p className="pl-[1.9rem] text-[0.85rem] leading-snug text-muted">
                    {GIVES[stage]}
                  </p>

                  <div
                    className="ml-[1.9rem] h-[3px] rounded-full bg-volt transition-[width,opacity] duration-300"
                    style={{
                      width: `${30 + i * 17}%`,
                      opacity: 0.35 + i * 0.16,
                    }}
                  />
                </li>
              ))}
            </ol>

            <p className="pl-1 text-[0.8rem] leading-snug text-muted-dim">
              Each rung gives more than the one above. You stop as soon as you
              see it.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
