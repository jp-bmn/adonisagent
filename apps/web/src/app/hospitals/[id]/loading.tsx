export default function HospitalProfileLoading() {
  return (
    <div className="px-8 py-7 animate-pulse">
      <div className="h-3 w-24 bg-slate-100 rounded mb-3" />

      <div className="bg-white border border-line rounded-xl overflow-hidden">
        <div className="px-6 py-5 border-b border-line flex gap-5">
          <div className="w-14 h-14 rounded-xl bg-slate-200 flex-none" />
          <div className="flex-1 space-y-2">
            <div className="h-7 w-56 bg-slate-200 rounded" />
            <div className="h-4 w-72 bg-slate-100 rounded" />
            <div className="h-3 w-32 bg-slate-100 rounded" />
          </div>
          <div className="flex gap-6 flex-none">
            <div className="space-y-1 text-right">
              <div className="h-8 w-8 bg-slate-200 rounded ml-auto" />
              <div className="h-3 w-12 bg-slate-100 rounded" />
            </div>
            <div className="space-y-1 text-right">
              <div className="h-8 w-8 bg-slate-200 rounded ml-auto" />
              <div className="h-3 w-16 bg-slate-100 rounded" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2">
          <div className="p-6 border-r border-line space-y-3">
            <div className="h-3 w-40 bg-slate-200 rounded" />
            <div className="h-4 w-full bg-slate-100 rounded" />
            <div className="h-4 w-3/4 bg-slate-100 rounded" />
          </div>
          <div className="p-6 space-y-3">
            <div className="h-3 w-32 bg-slate-200 rounded" />
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="bg-slate-50 border border-line rounded-xl p-4 space-y-2">
                <div className="h-4 w-2/3 bg-slate-200 rounded" />
                <div className="h-3 w-full bg-slate-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
