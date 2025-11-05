"use client";

import { Fragment, useMemo } from "react";
import Link from "next/link";

export type Citation = {
  id: string;
  instrument_title: string;
  structure_path: string;
  source_url: string;
  gazette?: string | null;
  snippet: string;
};

type LawCardProps = {
  citation: Citation;
  highlightTerms?: string[];
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

export default function LawCard({ citation, highlightTerms }: LawCardProps) {
  const highlightedTitle = useMemo(
    () => highlightText(citation.instrument_title, highlightTerms),
    [citation.instrument_title, highlightTerms],
  );

  const highlightedPath = useMemo(
    () => highlightText(citation.structure_path, highlightTerms),
    [citation.structure_path, highlightTerms],
  );

  const highlightedSnippet = useMemo(
    () => highlightText(citation.snippet, highlightTerms),
    [citation.snippet, highlightTerms],
  );

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-primary/60 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-neutral">
            {highlightedTitle}
          </h3>
          <p className="text-sm text-muted">{highlightedPath}</p>
        </div>
        <Link
          href={`/results/${encodeURIComponent(citation.id)}`}
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
