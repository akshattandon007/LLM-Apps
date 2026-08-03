import { Persona, getRandomPersona } from "@/lib/personas";
import PersonaCard from "./PersonaCard";

interface PersonaGridProps {
  personas: Persona[];
  selectedId: string | null;
  loading: boolean;
  onSelect: (persona: Persona) => void;
}

export default function PersonaGrid({
  personas,
  selectedId,
  loading,
  onSelect,
}: PersonaGridProps) {
  const handleSurprise = () => {
    const p = getRandomPersona();
    onSelect(p);
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold">Pick a Persona</h2>
        <button
          className="btn btn-sm btn-outline btn-secondary gap-1"
          onClick={handleSurprise}
          disabled={loading}
        >
          <span>🎲</span>
          Surprise Me
        </button>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {personas.map((p) => (
          <PersonaCard
            key={p.id}
            persona={p}
            selected={p.id === selectedId}
            loading={loading}
            onClick={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
