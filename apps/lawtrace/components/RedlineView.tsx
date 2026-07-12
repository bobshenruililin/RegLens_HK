type Props = {
  lines: string[];
};

/** Multi-signal redline: colour + background + underline/strike + prefix labels. */
export function RedlineView({ lines }: Props) {
  if (!lines.length) {
    return <p className="muted">No legal-text token operations for this transition.</p>;
  }
  return (
    <div className="redline" aria-label="Highlighted legal-text changes">
      {lines.map((line, i) => {
        if (line.startsWith("+ ")) {
          return (
            <div key={i}>
              <span className="visually-hidden">Addition: </span>
              <span className="ins">[+ ] {line.slice(2)}</span>
            </div>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <div key={i}>
              <span className="visually-hidden">Deletion: </span>
              <span className="del">[− ] {line.slice(2)}</span>
            </div>
          );
        }
        return <div key={i}>{line}</div>;
      })}
    </div>
  );
}
