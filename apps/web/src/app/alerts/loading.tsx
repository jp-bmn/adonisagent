export default function AlertsLoading() {
  return (
    <div className="px-8 py-7 animate-pulse">
      <div className="space-y-2 mb-6">
        <div className="h-7 w-20 bg-slate-200 rounded" />
        <div className="h-4 w-48 bg-slate-100 rounded" />
      </div>

      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white border border-line rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-5 w-14 bg-slate-200 rounded" />
                <div className="h-4 w-24 bg-slate-100 rounded" />
              </div>
              <div className="h-4 w-28 bg-slate-100 rounded" />
            </div>
            <div className="h-5 w-3/4 bg-slate-200 rounded" />
            <div className="h-4 w-full bg-slate-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
