interface ResponsePanelProps {
  title: string;
  content: string;
  variant?: "response" | "followup";
}

export function ResponsePanel({
  title,
  content,
  variant = "response",
}: ResponsePanelProps) {
  const borderClass =
    variant === "followup" ? "border-yellow-500/30" : "border-accent/30";

  return (
    <div
      className={`rounded-lg border ${borderClass} bg-gray-50 p-4`}
    >
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-700">
        {title}
      </h2>
      <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
        {content}
      </div>
    </div>
  );
}
