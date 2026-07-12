import type { InstrumentCard, RootManifest } from "@/lib/data";

export type ModeBadge = {
  label: string;
  tone: "demo" | "local" | "sampled" | "complete";
  detail: string;
};

export function rootModeBadge(root: RootManifest): ModeBadge {
  if (root.dataset_mode === "demo") {
    return {
      label: "Demo",
      tone: "demo",
      detail: "Committed Cap. 614 fixtures; Cap. 599G unavailable in this mode.",
    };
  }
  return {
    label: "Local real-data",
    tone: "local",
    detail: "Generated from official local extracts (not a public release).",
  };
}

export function instrumentCompletenessBadge(
  inst: InstrumentCard,
): ModeBadge | null {
  if (!inst.available) {
    return {
      label: "Unavailable",
      tone: "demo",
      detail: inst.missing_reason || "Not available in this dataset mode.",
    };
  }
  if (inst.sampling && !inst.sampling.complete) {
    return {
      label: "Sampled",
      tone: "sampled",
      detail: `${inst.sampling.versions_included}/${inst.sampling.total_available_versions} snapshots included — not complete.`,
    };
  }
  return {
    label: "Complete",
    tone: "complete",
    detail: "All available English top-level snapshots in this export are included.",
  };
}
