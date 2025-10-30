import Link from "next/link";

import CitationBlock from "../../../components/CitationBlock";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type LegalSlice = {
  id: string;
  jurisdiction: {
    level: string;
    name: string;
    emirate?: string | null;
    freezone?: string | null;
  };
  source: {
    portal: string;
    url: string;
    gazette?: string | null;
  };
  instrument: {
    type: string;
    number: string;
    year: number;
    title: string;
    issuer?: string | null;
    official_language: string;
  };
  structure: {
    granularity: string;
    path: string;
    locators: Record<string, string | null>;
  };
  text_content: string;
  primary_lang: string;
  topics: string[];
  state: string;
  effective: {
    from_date: string;
    to_date?: string | null;
  };
};

async function fetchLegalSlice(id: string): Promise<LegalSlice> {
  const response = await fetch(`${API_BASE_URL}/get_by_id/${encodeURIComponent(id)}`, {
    next: { revalidate: 0 },
  });

  if (response.status === 404) {
    throw new Error("NOT_FOUND");
  }

  if (!response.ok) {
    throw new Error("FAILED_TO_FETCH");
  }

  return (await response.json()) as LegalSlice;
}

type PageProps = {
  params: { id: string };
};

export default async function ResultDetailPage({ params }: PageProps) {
  let data: LegalSlice | null = null;
  try {
    data = await fetchLegalSlice(params.id);
  } catch (error) {
    if (error instanceof Error && error.message === "NOT_FOUND") {
      return (
        <main className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-16">
          <h1 className="text-2xl font-semibold text-neutral">未找到条文</h1>
          <p className="text-muted">请返回检索页并尝试其他关键词。</p>
        </main>
      );
    }
    throw error;
  }

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-12">
      <div>
        <Link href="/" className="text-sm text-primary hover:underline">
          ← 返回检索
        </Link>
        <h1 className="mt-4 text-3xl font-bold text-neutral">
          {data.instrument.title}
        </h1>
        <p className="mt-2 text-sm text-muted">
          {data.structure.path} · {data.jurisdiction.name} · {data.instrument.year}
        </p>
      </div>

      <CitationBlock
        instrumentTitle={data.instrument.title}
        structurePath={data.structure.path}
        sourceUrl={data.source.url}
        gazette={data.source.gazette ?? undefined}
      />

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-neutral">条文全文</h2>
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed text-neutral">
          {data.text_content}
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm text-neutral">
          <h3 className="mb-2 font-semibold text-neutral">生效信息</h3>
          <p>生效日期：{data.effective.from_date}</p>
          <p>
            失效日期：{data.effective.to_date ? data.effective.to_date : "暂无"}
          </p>
          <p>状态：{data.state}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm text-neutral">
          <h3 className="mb-2 font-semibold text-neutral">法域 / 主题</h3>
          <p>法域：{data.jurisdiction.name}</p>
          <p>级别：{data.jurisdiction.level}</p>
          {data.topics.length ? (
            <p>主题：{data.topics.join("，")}</p>
          ) : (
            <p>主题：未标注</p>
          )}
          <p>主语言：{data.primary_lang}</p>
        </div>
      </section>
      <p className="text-xs text-muted">
        免责声明：信息检索工具，非法律意见；以官方文本为准（DIFC/ADGM 英文为权威；联邦英文多为参考译文）。
      </p>
    </main>
  );
}
