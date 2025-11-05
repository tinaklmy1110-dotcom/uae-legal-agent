import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { texts?: string[] };
    if (!body?.texts || !Array.isArray(body.texts) || body.texts.length === 0) {
      return NextResponse.json({ detail: "texts must not be empty" }, { status: 400 });
    }

    const response = await fetch(`${API_BASE_URL}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts: body.texts }),
    });

    if (!response.ok) {
      return NextResponse.json(
        { detail: `翻译服务异常：${await response.text()}` },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { detail: (error instanceof Error ? error.message : "翻译失败") },
      { status: 502 },
    );
  }
}
