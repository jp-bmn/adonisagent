export default function HospitalsLoading() {
  return (
    <div className="px-8 py-7 animate-pulse">
      <div className="space-y-2 mb-6">
        <div className="h-7 w-28 bg-slate-200 rounded" />
        <div className="h-4 w-40 bg-slate-100 rounded" />
      </div>

      <div className="bg-white border border-line rounded-xl overflow-hidden">
        <div className="bg-paper border-b border-line px-5 py-3 flex gap-8">
          <div className="h-3 w-20 bg-slate-200 rounded" />
          <div className="h-3 w-24 bg-slate-200 rounded" />
          <div className="h-3 w-16 bg-slate-200 rounded" />
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="border-b border-line last:border-b-0 px-5 py-4 flex gap-8 items-center">
            <div className="h-4 w-48 bg-slate-200 rounded" />
            <div className="h-4 w-32 bg-slate-100 rounded" />
            <div className="h-4 w-40 bg-slate-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
