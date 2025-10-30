"use client";

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
};

export default function LawCard({ citation }: LawCardProps) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-primary/60 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-neutral">
            {citation.instrument_title}
          </h3>
          <p className="text-sm text-muted">{citation.structure_path}</p>
        </div>
        <Link
          href={`/results/${encodeURIComponent(citation.id)}`}
          className="rounded-md border border-primary px-3 py-1 text-sm font-medium text-primary hover:bg-primary/10"
        >
          查看详情
        </Link>
      </div>
      <p className="mt-4 text-sm leading-relaxed text-neutral">{citation.snippet}</p>
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
