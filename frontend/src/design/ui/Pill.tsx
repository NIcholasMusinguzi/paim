type Tone = "leaf" | "murram" | "grain" | "soft";

const tones: Record<Tone, string> = {
  leaf: "bg-leaf/10 text-leaf",
  murram: "bg-murram/10 text-murram",
  grain: "bg-grain/10 text-grain",
  soft: "bg-rule text-soft",
};

export function Pill({ tone = "soft", children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}
