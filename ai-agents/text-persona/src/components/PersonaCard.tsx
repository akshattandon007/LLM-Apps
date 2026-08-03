import { Persona } from "@/lib/personas";

interface PersonaCardProps {
  persona: Persona;
  selected: boolean;
  loading: boolean;
  onClick: (persona: Persona) => void;
}

export default function PersonaCard({
  persona,
  selected,
  loading,
  onClick,
}: PersonaCardProps) {
  return (
    <button
      onClick={() => onClick(persona)}
      disabled={loading}
      className={`
        relative flex flex-col items-center gap-2 p-4 rounded-xl border-2
        transition-all duration-200 cursor-pointer w-full
        hover:scale-105 hover:shadow-lg
        active:scale-95
        disabled:opacity-50 disabled:cursor-not-allowed
        ${selected
          ? "border-primary bg-primary/10 shadow-md"
          : "border-base-300 bg-base-100 hover:border-primary/50"
        }
      `}
    >
      <span className="text-3xl select-none">{persona.emoji}</span>
      <span className="font-semibold text-sm text-center select-none">
        {persona.name}
      </span>
      <span className="text-xs text-center text-base-content/60 leading-tight select-none">
        {persona.tagline}
      </span>
      {selected && loading && (
        <span className="absolute top-2 right-2 loading loading-spinner loading-sm text-primary" />
      )}
    </button>
  );
}
