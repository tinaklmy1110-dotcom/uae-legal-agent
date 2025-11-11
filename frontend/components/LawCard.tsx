"use client";

import { Fragment, useMemo } from "react";
import Link from "next/link";

import {
  buildLocatorBreadcrumb,
  extractHeadingFromPath,
  type StructureLocators,
} from "../lib/structure";

export type Citation = {
  id: string;
  instrument_title: string;
  structure_path: string;
  structure_locators?: StructureLocators | null;
  source_url: string;
  gazette?: string | null;
  snippet: string;
};

type LawCardProps = {
  citation: Citation;
  highlightTerms?: string[];
  currentQuery?: string;
};

const escapeRegExp = (value: string) =>
  value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function highlightText(text: string, terms: string[] | undefined) {
  if (!text || !terms || terms.length === 0) {
    return text;
  }

  const cleanedTerms = terms
    .map((term) => term.trim())
    .filter((term) => term.length > 0);
  if (!cleanedTerms.length) {
    return text;
  }

  const escaped = cleanedTerms.map(escapeRegExp).join("|");
  if (!escaped) {
    return text;
  }

  const regex = new RegExp(`(${escaped})`, "gi");
  const lowerTerms = new Set(cleanedTerms.map((term) => term.toLowerCase()));

  return text.split(regex).map((segment, index) => {
    const isMatch = lowerTerms.has(segment.toLowerCase());
    if (isMatch) {
      return (
        <mark
          key={`${segment}-${index}`}
          className="rounded bg-yellow-200/70 px-0.5 py-0 text-neutral"
        >
          {segment}
        </mark>
      );
    }
    return <Fragment key={index}>{segment}</Fragment>;
  });
}

const JURIS_LABELS: Record<string, string> = {
  federal: "联邦法",
  abu_dhabi: "阿布扎比",
  dubai: "迪拜",
  sharjah: "沙迦",
  ajman: "阿治曼",
  fujairah: "富查伊拉",
  rak: "哈伊马角",
};

function getJurisdictionLabel(id: string): string {
  const prefix = id.split("#")[0]?.toLowerCase();
  if (!prefix) {
    return "";
  }
  return JURIS_LABELS[prefix] ?? prefix.replace(/_/g, " ");
}

export default function LawCard({ citation, highlightTerms, currentQuery }: LawCardProps) {
  const jurisdictionLabel = useMemo(
    () => getJurisdictionLabel(citation.id),
    [citation.id],
  );

  const locatorPath = useMemo(
    () =>
      buildLocatorBreadcrumb(
        citation.structure_locators,
        citation.structure_path,
      ),
    [citation.structure_locators, citation.structure_path],
  );

  const highlightedPath = useMemo(
    () => highlightText(locatorPath, highlightTerms),
    [locatorPath, highlightTerms],
  );

  const headingText = useMemo(
    () => extractHeadingFromPath(citation.structure_path),
    [citation.structure_path],
  );

  const highlightedHeading = useMemo(
    () => (headingText ? highlightText(headingText, highlightTerms) : null),
    [headingText, highlightTerms],
  );

  const highlightedTitle = useMemo(
    () => highlightText(citation.instrument_title, highlightTerms),
    [citation.instrument_title, highlightTerms],
  );

  const highlightedSnippet = useMemo(
    () => highlightText(citation.snippet, highlightTerms),
    [citation.snippet, highlightTerms],
  );

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-primary/60 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {highlightedPath}
          </p>
          {highlightedHeading ? (
            <h3 className="text-lg font-semibold text-neutral">
              {highlightedHeading}
            </h3>
          ) : (
            <h3 className="text-lg font-semibold text-neutral">
              {highlightedTitle}
            </h3>
          )}
          <p className="text-sm text-muted">
            {highlightedTitle}
            {jurisdictionLabel ? ` · ${jurisdictionLabel}` : null}
          </p>
        </div>
        <Link
          href={
            currentQuery
              ? `/results/${encodeURIComponent(citation.id)}?q=${encodeURIComponent(currentQuery)}`
              : `/results/${encodeURIComponent(citation.id)}`
          }
          className="rounded-md border border-primary px-3 py-1 text-sm font-medium text-primary hover:bg-primary/10"
        >
          查看详情
        </Link>
      </div>
      <p className="mt-4 text-sm leading-relaxed text-neutral">
        {highlightedSnippet}
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted">
        <a
          href={citation.source_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-primary hover:underline"
        >
          官方来源
        </a>
        {citation.gazette ? (
          <span className="rounded-full bg-gray-100 px-3 py-1 font-medium">
            {citation.gazette}
          </span>
        ) : null}
      </div>
    </article>
  );
}
