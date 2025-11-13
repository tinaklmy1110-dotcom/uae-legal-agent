export type StructureLocators = {
  part?: string | null;
  chapter?: string | null;
  section?: string | null;
  article?: string | null;
  rule?: string | null;
  clause?: string | null;
  item?: string | null;
};

const LOCATOR_LABELS: Record<keyof StructureLocators, string> = {
  part: "Part",
  chapter: "Chapter",
  section: "Section",
  article: "Article",
  rule: "Rule",
  clause: "Clause",
  item: "Item",
};

const LOCATOR_ORDER: Array<keyof StructureLocators> = [
  "item",
  "clause",
  "rule",
  "article",
  "section",
  "chapter",
  "part",
];

export function buildLocatorBreadcrumb(
  locators?: StructureLocators | null,
  fallback?: string,
): string {
  const segments = LOCATOR_ORDER.map((key) => {
    const value = locators?.[key];
    if (!value) {
      return null;
    }
    return `${LOCATOR_LABELS[key]} ${value}`;
  }).filter((segment): segment is string => Boolean(segment));

  if (segments.length) {
    return segments.join(" / ");
  }

  if (fallback) {
    const fallbackSegments = fallback
      .split(">")
      .map((part) => part.trim())
      .map((part) => (part.includes("–") ? part.split("–")[0].trim() : part))
      .filter((segment) => segment.length > 0);
    if (fallbackSegments.length) {
      return fallbackSegments.join(" / ");
    }
    return fallback;
  }

  return "";
}

export function extractHeadingFromPath(path?: string | null): string {
  if (!path) {
    return "";
  }
  const parts = path.split(">");
  const last = parts[parts.length - 1]?.trim() ?? "";
  if (!last) {
    return "";
  }
  const dashIndex = last.indexOf("–");
  if (dashIndex >= 0) {
    return last.slice(dashIndex + 1).trim();
  }
  return last;
}
