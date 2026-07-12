export function relationshipLabel(rel: string): string {
  switch (rel) {
    case "unchanged":
      return "Unchanged";
    case "text_changed":
      return "Text changed";
    case "status_changed":
      return "Status only";
    case "text_and_status_changed":
      return "Text and status";
    case "added":
      return "Added";
    case "removed":
      return "Removed";
    case "section_number_changed":
      return "Section number changed";
    default:
      return rel;
  }
}

export function shortFile(name: string): string {
  return name.replace(/^cap_[^_]+_/, "").replace(/_en_[cp]\.xml$/i, "");
}
