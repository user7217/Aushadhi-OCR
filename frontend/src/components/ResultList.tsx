import type { Match } from "../types/api";

export function ResultList({ items }: { items: Match[] }) {
  return (
    <ul>
      {items.map((m, i) => (
        <li key={i}>
          {m.name} — {m.score.toFixed(1)}% {m.generic ? \`— \${m.generic}\` : ""} {m.manufacturer ? \`— \${m.manufacturer}\` : ""}
        </li>
      ))}
    </ul>
  );
}
