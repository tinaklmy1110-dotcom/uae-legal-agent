"use client";

import { Suspense } from "react";

import HomeClient from "../components/HomeClient";

export const dynamic = "force-dynamic";

type PageProps = { searchParams?: { q?: string } };

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

export default function HomePage({ searchParams }: PageProps) {
  const initialQuery = searchParams?.q ?? "";
  return (
    <Suspense fallback={<LoadingState />}>
      <HomeClient initialQuery={initialQuery} />
    </Suspense>
  );
}
