/** Human-readable summaries of deterministic channel operations. */

export type Op = {
  op?: string;
  a_tokens?: string[];
  b_tokens?: string[];
  channel?: string;
};

function joinTokens(tokens: string[] | undefined): string {
  if (!tokens?.length) return "";
  return tokens
    .map((t) => t.replace(/^(CONTENT|LEADIN|HEADING|NUM|STATUS|ATTR)\|/, ""))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

export function summarizeMetadataOps(ops: Op[] | undefined): string[] {
  if (!ops?.length) return ["No metadata/status token changes in this transition."];
  const lines: string[] = [];
  for (const op of ops) {
    const a = joinTokens(op.a_tokens);
    const b = joinTokens(op.b_tokens);
    if (op.op === "replace" && (a || b)) {
      if (/status/i.test(a + b) || a !== b) {
        lines.push(
          a && b
            ? `Status/metadata changed from “${a}” to “${b}”.`
            : b
              ? `Status/metadata became “${b}”.`
              : `Status/metadata “${a}” was removed.`,
        );
        continue;
      }
    }
    if (op.op === "insert" && b) {
      lines.push(`Status/metadata added: “${b}”.`);
      continue;
    }
    if (op.op === "delete" && a) {
      lines.push(`Status/metadata removed: “${a}”.`);
      continue;
    }
    lines.push(`Metadata operation: ${op.op || "change"}.`);
  }
  return lines.length ? lines : ["No metadata/status token changes in this transition."];
}

export function summarizeStructuralOps(ops: Op[] | undefined): string[] {
  if (!ops?.length) return ["No structural token changes in this transition."];
  const lines: string[] = [];
  for (const op of ops) {
    const a = joinTokens(op.a_tokens);
    const b = joinTokens(op.b_tokens);
    if (op.op === "insert" && b) {
      if (/subsection|sub-section|\(\d+\)/i.test(b)) {
        lines.push(`Structural addition detected (e.g. subsection material): “${truncate(b, 120)}”.`);
      } else {
        lines.push(`Structural material added: “${truncate(b, 120)}”.`);
      }
      continue;
    }
    if (op.op === "delete" && a) {
      lines.push(`Structural material removed: “${truncate(a, 120)}”.`);
      continue;
    }
    if (op.op === "replace") {
      lines.push(
        `Structural replacement: “${truncate(a, 80)}” → “${truncate(b, 80)}”.`,
      );
      continue;
    }
    lines.push(`Structural operation: ${op.op || "change"}.`);
  }
  return lines;
}

export function summarizeRelationship(
  relationship: string,
  opts: {
    numA?: string | null;
    numB?: string | null;
    headingChanged?: boolean;
  } = {},
): string[] {
  const lines: string[] = [];
  switch (relationship) {
    case "added":
      lines.push("Classification: added — the section is not present in snapshot A.");
      break;
    case "removed":
      lines.push("Classification: removed — the section is not present in snapshot B.");
      break;
    case "status_changed":
      lines.push("Classification: status only — legal-text tokens are unchanged.");
      break;
    case "text_changed":
      lines.push("Classification: text changed — legal-text tokens differ.");
      break;
    case "text_and_status_changed":
      lines.push("Classification: text and status both changed.");
      break;
    case "section_number_changed":
      lines.push(
        "The section number changed while the stable source @id remained the same.",
      );
      break;
    default:
      lines.push(`Classification: ${relationship}.`);
  }
  if (opts.numA && opts.numB && opts.numA !== opts.numB) {
    lines.push(
      `The section number changed from § ${opts.numA} to § ${opts.numB} while the stable source @id remained the same.`,
    );
  }
  if (opts.headingChanged) {
    lines.push("The section heading changed.");
  }
  return lines;
}

export function countTokenDelta(ops: Op[] | undefined): {
  additions: number;
  deletions: number;
} {
  let additions = 0;
  let deletions = 0;
  for (const op of ops || []) {
    if (op.op === "insert") additions += (op.b_tokens || []).length;
    else if (op.op === "delete") deletions += (op.a_tokens || []).length;
    else if (op.op === "replace") {
      deletions += (op.a_tokens || []).length;
      additions += (op.b_tokens || []).length;
    }
  }
  return { additions, deletions };
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n - 1) + "…";
}
