"use client";

import { useState } from "react";

async function requestTranslation(texts: string[]): Promise<string[]> {
  const response = await fetch("/api/translate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts }),
  });

  if (!response.ok) {
    throw new Error((await response.json()).detail ?? "Translation failed");
  }

  const data = (await response.json()) as { translations: string[] };
  return data.translations;
}

type TranslateButtonProps = {
  sourceText: string;
  onTranslated: (translated: string) => void;
};

export default function TranslateButton({ sourceText, onTranslated }: TranslateButtonProps) {
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    if (!sourceText.trim()) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const [translated] = await requestTranslation([sourceText]);
      onTranslated(translated ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "翻译失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 space-y-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={isLoading}
        className="rounded-md border border-primary px-3 py-2 text-sm font-medium text-primary hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? "翻译中…" : "翻译成中文"}
      </button>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
