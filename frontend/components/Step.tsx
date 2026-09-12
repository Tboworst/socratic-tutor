/**
 * One step of the entry flow. A step that is not reachable yet is dimmed and
 * inert rather than hidden, so the reader can see what is coming.
 */
export function Step({
  n,
  title,
  hint,
  locked = false,
  done = false,
  children,
}: {
  n: number;
  title: string;
  hint?: string;
  locked?: boolean;
  done?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      aria-disabled={locked}
      className={
        locked
          ? "pointer-events-none select-none opacity-35 transition-opacity"
          : "transition-opacity"
      }
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-baseline gap-3">
          <span
            className={`font-mono text-[0.72rem] font-medium ${
              done ? "text-good" : locked ? "text-muted-dim" : "text-volt"
            }`}
          >
            {done ? "done" : String(n).padStart(2, "0")}
          </span>
          <h2 className="font-display text-[1.15rem] font-bold tracking-[-0.01em]">
            {title}
          </h2>
          {hint && (
            <span className="text-[0.85rem] text-muted-dim">{hint}</span>
          )}
        </div>
        {children}
      </div>
    </section>
  );
}
