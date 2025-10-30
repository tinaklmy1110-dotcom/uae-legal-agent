'use client';

import { useState } from "react";

type CitationBlockProps = {
  instrumentTitle: string;
  structurePath: string;
  sourceUrl: string;
  gazette?: string | null;
};

export default function CitationBlock({
  instrumentTitle,
  structurePath,
  sourceUrl,
  gazette,
}: CitationBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sourceUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-neutral">引用信息</h2>
      <div className="mt-3 space-y-2 text-sm text-neutral">
        <p className="font-medium">{instrumentTitle}</p>
        <p>{structurePath}</p>
        {gazette ? <p>官方公报：{gazette}</p> : null}
        <div className="flex items-center gap-3">
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="truncate text-primary hover:underline"
          >
            {sourceUrl}
          </a>
          <button
            type="button"
            onClick={handleCopy}
            className="rounded-md border border-gray-300 px-3 py-1 text-xs font-medium hover:border-primary hover:text-primary"
          >
            {copied ? "已复制" : "复制链接"}
          </button>
        </div>
      </div>
    </section>
  );
}
