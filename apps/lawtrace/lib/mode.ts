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
    const n = inst.sampling.versions_included;
    const m = inst.sampling.total_available_versions;
    return {
      label: `Sampled ${n}/${m}`,
      tone: "sampled",
      detail: `Sampled collection — ${n} of ${m} available snapshots represented.`,
    };
  }
  if (inst.sampling) {
    const n = inst.sampling.versions_included;
    const m = inst.sampling.total_available_versions;
    return {
      label: `Complete ${n}/${m}`,
      tone: "complete",
      detail: `All ${n} of ${m} available English top-level snapshots in this export are included.`,
    };
  }
  return {
    label: "Complete",
    tone: "complete",
    detail: "All available English top-level snapshots in this export are included.",
  };
}
