'use client';

type FilterPanelProps = {
  jurisdiction?: string;
  onJurisdictionChange: (value: string | undefined) => void;
  topics: string[];
  onTopicsChange: (value: string[]) => void;
  asOf?: string;
  onAsOfChange: (value: string | undefined) => void;
};

const JURISDICTIONS = [
  { label: "全部法域", value: "" },
  { label: "联邦 (Federal)", value: "federal" },
  { label: "迪拜 (Dubai)", value: "Dubai" },
  { label: "阿布扎比 (Abu Dhabi)", value: "Abu Dhabi" },
  { label: "DIFC", value: "DIFC" },
  { label: "ADGM", value: "ADGM" },
];

const TOPIC_OPTIONS = [
  { label: "Tenancy / Real Estate", value: "real_estate" },
  { label: "Financial Regulation", value: "finance" },
  { label: "Employment", value: "employment" },
  { label: "Compliance", value: "compliance" },
];

export default function FilterPanel({
  jurisdiction,
  onJurisdictionChange,
  topics,
  onTopicsChange,
  asOf,
  onAsOfChange,
}: FilterPanelProps) {
  const handleTopicToggle = (value: string) => {
    if (topics.includes(value)) {
      onTopicsChange(topics.filter((item) => item !== value));
    } else {
      onTopicsChange([...topics, value]);
    }
  };

  return (
    <aside className="w-full rounded-xl border border-gray-200 bg-white p-4 shadow-sm lg:max-w-xs">
      <h2 className="text-lg font-semibold text-neutral">筛选条件</h2>
      <div className="mt-4 space-y-4 text-sm text-muted">
        <div>
          <label className="mb-2 block font-medium text-neutral" htmlFor="jurisdiction">
            法域
          </label>
          <select
            id="jurisdiction"
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
            value={jurisdiction ?? ""}
            onChange={(event) =>
              onJurisdictionChange(event.target.value || undefined)
            }
          >
            {JURISDICTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <span className="mb-2 block font-medium text-neutral">主题</span>
          <div className="space-y-2">
            {TOPIC_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary/40"
                  checked={topics.includes(option.value)}
                  onChange={() => handleTopicToggle(option.value)}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <label className="mb-2 block font-medium text-neutral" htmlFor="as-of">
            截至日期 (as of)
          </label>
          <input
            id="as-of"
            type="date"
            value={asOf ?? ""}
            onChange={(event) => onAsOfChange(event.target.value || undefined)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>
    </aside>
  );
}
