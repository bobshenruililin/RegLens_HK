type Props = {
  lines: string[];
};

/** Multi-signal redline: colour + background + underline/strike + semantic ins/del. */
export function RedlineView({ lines }: Props) {
  if (!lines.length) {
    return (
      <p className="muted">No legal-text token operations for this transition.</p>
    );
  }
  return (
    <div className="redline statute" aria-label="Highlighted legal-text changes">
      {lines.map((line, i) => {
        if (line.startsWith("+ ")) {
          return (
            <div key={i} className="redline-line">
              <ins className="ins">
                <span className="visually-hidden">Addition: </span>
                <span aria-hidden="true">[+ ] </span>
                {line.slice(2)}
              </ins>
            </div>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <div key={i} className="redline-line">
              <del className="del">
                <span className="visually-hidden">Deletion: </span>
                <span aria-hidden="true">[− ] </span>
                {line.slice(2)}
              </del>
            </div>
          );
        }
        return (
          <div key={i} className="redline-line">
            {line}
          </div>
        );
      })}
    </div>
  );
}

export function StatuteText({ text }: { text: string }) {
  if (!text) {
    return <p className="muted">No section text in this snapshot.</p>;
  }
  return <pre className="redline statute">{text}</pre>;
}
