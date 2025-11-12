import { Suspense } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import FilterPanel from "../components/FilterPanel";
import LawCard, { type Citation } from "../components/LawCard";
import SearchBar from "../components/SearchBar";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

type SearchResponse = {
  query: string;
  items: Citation[];
};

function HomeClient({ initialQuery }: { initialQuery: string }) {
  "use client";

  const router = useRouter();
  const searchParams = useSearchParams();

  const [query, setQuery] = useState(initialQuery);
  const [jurisdiction, setJurisdiction] = useState<string | undefined>();
  const [topics, setTopics] = useState<string[]>([]);
  const [asOf, setAsOf] = useState<string | undefined>();
  const [results, setResults] = useState<Citation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const runSearch = useCallback(
    async (body: {
      query: string;
      jurisdiction: string | undefined;
      topics: string[] | undefined;
      as_of: string | undefined;
    }) => {
      if (!body.query) {
        setResults([]);
        return;
      }
      try {
        setIsLoading(true);
        setError(undefined);
        const response = await fetch(`${API_BASE_URL}/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          throw new Error(`请求失败：${response.statusText}`);
        }
        const json = (await response.json()) as SearchResponse;
        setResults(json.items);
      } catch (fetchError) {
        setError(fetchError instanceof Error ? fetchError.message : "请求失败");
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  const handleSearch = useCallback(
    (value: string) => {
      const nextQuery = value.trim();
      if (!nextQuery) {
        return;
      }
      const params = new URLSearchParams(
        Array.from(searchParams.entries()),
      );
      params.set("q", nextQuery);
      router.push(`/?${params.toString()}`, { scroll: false });
      setQuery(nextQuery);
    },
    [router, searchParams],
  );

  useEffect(() => {
    if (!query) {
      return;
    }
    runSearch({
      query,
      jurisdiction,
      topics: topics.length ? topics : undefined,
      as_of: asOf,
    });
  }, [jurisdiction, topics, asOf, query, runSearch]);

  const highlightTerms = useMemo(
    () =>
      Array.from(
        new Set(
          query
            .trim()
            .split(/\s+/)
            .filter((term) => term.length > 0),
        ),
      ),
    [query],
  );

  return (
    <main className="min-h-screen bg-slate-50 pb-16">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-12 lg:flex-row">
        <div className="flex-1 space-y-6">
          <header className="space-y-3">
            <p className="text-xs uppercase text-primary">UAE Legal Agent</p>
            <h1 className="text-3xl font-bold text-neutral">
              UAE 法律检索与引用助手
            </h1>
            <p className="max-w-2xl text-sm text-muted">
              基于官方条文切片的本地 RAG 检索，覆盖联邦、酋长国与自由区法规，支持主题/日期筛选与强制引用。
            </p>
          </header>
          <SearchBar onSearch={handleSearch} defaultQuery={query || ""} isLoading={isLoading} />
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-neutral">
                检索结果
              </h2>
              <span className="text-sm text-muted">
                {isLoading
                  ? "检索中…"
                  : query
                    ? `共 ${results.length} 条匹配 “${query}”`
                    : `共 ${results.length} 条`}
              </span>
            </div>
            <div className="space-y-4">
              {results.map((item) => (
                <LawCard
                  key={item.id}
                  citation={item}
                  highlightTerms={highlightTerms}
                  currentQuery={query}
                />
              ))}
              {!results.length && !isLoading ? (
                <p className="rounded-lg border border-dashed border-gray-300 bg-white px-4 py-8 text-center text-sm text-muted">
                  暂无结果，请尝试更换关键词或筛选条件。
                </p>
              ) : null}
            </div>
          </section>
        </div>
        <div className="lg:w-80">
          <FilterPanel
            jurisdiction={jurisdiction}
            onJurisdictionChange={setJurisdiction}
            topics={topics}
            onTopicsChange={setTopics}
            asOf={asOf}
            onAsOfChange={setAsOf}
          />
          <p className="mt-6 text-xs text-muted">
            免责声明：信息检索工具，非法律意见；以官方文本为准（DIFC/ADGM 英文为权威；联邦英文多为参考译文）。
          </p>
        </div>
      </div>
    </main>
  );
}

function LoadingState() {
  return (
    <main className="min-h-screen bg-slate-50 pb-16">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-12">
        <div className="h-10 w-1/2 animate-pulse rounded bg-gray-200" />
        <div className="h-32 w-full animate-pulse rounded-xl border border-gray-200 bg-white" />
      </div>
    </main>
  );
}

type PageProps = { searchParams?: { q?: string } };

export default function HomePage({ searchParams }: PageProps) {
  const initialQuery = searchParams?.q ?? "";
  return (
    <Suspense fallback={<LoadingState />}>
      <HomeClient initialQuery={initialQuery} />
    </Suspense>
  );
}
