"use client";

import { useState } from "react";

const requestTranslation = async (texts: string[]): Promise<string[]> => {
  const response = await fetch("/api/translate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "翻译失败");
  }

  const data = (await response.json()) as { translations: string[] };
  return data.translations;
};

type TranslationPanelProps = {
  sourceText: string;
};

export default function TranslationPanel({ sourceText }: TranslationPanelProps) {
  const [translatedText, setTranslatedText] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const [translated] = await requestTranslation([sourceText]);
      setTranslatedText(translated ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "翻译失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold text-neutral">中文翻译</h2>
        <button
          type="button"
          onClick={handleTranslate}
          disabled={isLoading}
          className="rounded-md border border-primary px-3 py-2 text-sm font-medium text-primary hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "翻译中…" : translatedText ? "重新翻译" : "翻译成中文"}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      {translatedText !== null ? (
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed text-neutral">
          {translatedText || "暂无译文"}
        </p>
      ) : (
        <p className="mt-4 text-sm text-muted">点击“翻译成中文”即可查看机器翻译结果。</p>
      )}
    </section>
  );
}
