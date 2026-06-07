export default function ReviewLoading() {
  return (
    <div className="px-8 py-7 animate-pulse">
      <div className="space-y-2 mb-6">
        <div className="h-7 w-36 bg-slate-200 rounded" />
        <div className="h-4 w-64 bg-slate-100 rounded" />
      </div>

      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white border border-line rounded-xl p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex gap-2">
                  <div className="h-3 w-24 bg-slate-100 rounded" />
                  <div className="h-3 w-28 bg-slate-100 rounded" />
                </div>
                <div className="h-5 w-3/4 bg-slate-200 rounded" />
                <div className="h-4 w-full bg-slate-100 rounded" />
                <div className="h-3 w-32 bg-slate-100 rounded" />
              </div>
              <div className="flex gap-2 flex-none">
                <div className="h-8 w-20 bg-slate-100 rounded-lg" />
                <div className="h-8 w-20 bg-slate-100 rounded-lg" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
