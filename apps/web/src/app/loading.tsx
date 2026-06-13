export default function HomeLoading() {
  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7 animate-pulse">
      {/* Header */}
      <div className="flex items-end justify-between mb-6 flex-wrap gap-3">
        <div className="space-y-2">
          <div className="h-7 w-36 bg-slate-200 rounded" />
          <div className="h-4 w-52 bg-slate-100 rounded" />
        </div>
        <div className="h-8 w-40 bg-slate-100 rounded-lg" />
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="bg-white border border-line rounded-xl p-4 space-y-2 overflow-hidden relative"
          >
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-slate-200" />
            <div className="h-8 w-12 bg-slate-200 rounded" />
            <div className="h-3 w-28 bg-slate-100 rounded" />
          </div>
        ))}
      </div>

      {/* Filter chips row */}
      <div className="flex items-center gap-2 mb-4 overflow-hidden">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-7 w-24 bg-slate-100 rounded-full flex-none" />
        ))}
      </div>

      {/* Section label */}
      <div className="h-3 w-40 bg-slate-100 rounded mb-3" />

      {/* Signal card skeletons */}
      <div className="space-y-5">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white border border-line rounded-xl p-5 space-y-3">
            {/* Pill + date row */}
            <div className="flex items-center gap-2">
              <div className="h-5 w-20 bg-slate-200 rounded-full" />
              <div className="h-4 w-28 bg-slate-100 rounded" />
            </div>
            {/* Headline */}
            <div className="h-5 w-3/4 bg-slate-200 rounded" />
            {/* Summary lines */}
            <div className="space-y-2">
              <div className="h-3.5 w-full bg-slate-100 rounded" />
              <div className="h-3.5 w-5/6 bg-slate-100 rounded" />
            </div>
            {/* Footer */}
            <div className="flex items-center justify-between pt-1">
              <div className="h-3.5 w-32 bg-slate-100 rounded" />
              <div className="h-3.5 w-24 bg-slate-100 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
