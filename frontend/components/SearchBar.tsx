'use client';

import { FormEvent, useState } from "react";

type SearchBarProps = {
  defaultQuery?: string;
  onSearch: (query: string) => void;
  isLoading?: boolean;
};

export default function SearchBar({ defaultQuery = "", onSearch, isLoading = false }: SearchBarProps) {
  const [value, setValue] = useState(defaultQuery);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }
    onSearch(value.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full gap-3">
      <input
        type="search"
        name="query"
        className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-base shadow-sm transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
        placeholder="搜索 UAE 法规条文（例如：tenancy deposit）"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="搜索法条"
      />
      <button
        type="submit"
        className="rounded-lg bg-primary px-6 py-3 font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-primary/60"
        disabled={isLoading}
      >
        {isLoading ? "检索中…" : "检索"}
      </button>
    </form>
  );
}
