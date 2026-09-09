type Tone = "leaf" | "murram" | "grain" | "soft";

const tones: Record<Tone, string> = {
  leaf: "bg-leaf/15 text-leaf",
  murram: "bg-murram/10 text-murram",
  grain: "bg-grain/15 text-amber-800",
  soft: "bg-page text-soft",
};

export function Pill({ tone = "soft", children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${tones[tone]}`}>
      {children}
    </span>
  );
}
