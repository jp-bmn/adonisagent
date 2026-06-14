export default function HospitalProfileLoading() {
  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7 animate-pulse">
      {/* Back link */}
      <div className="h-3 w-24 bg-slate-100 rounded mb-3" />

      <div className="bg-white border border-line rounded-xl overflow-hidden mt-3">
        {/* Header */}
        <div className="px-4 md:px-6 py-5 border-b border-line flex flex-wrap gap-4">
          {/* Logo */}
          <div className="w-16 h-16 rounded-xl bg-slate-200 flex-none" />
          <div className="flex-1 min-w-0 space-y-2">
            <div className="h-6 w-48 bg-slate-200 rounded" />
            <div className="h-4 w-36 bg-slate-100 rounded" />
            <div className="h-3 w-28 bg-slate-100 rounded" />
            {/* Mobile stats */}
            <div className="flex gap-5 pt-1 md:hidden">
              <div className="space-y-1">
                <div className="h-6 w-8 bg-slate-200 rounded" />
                <div className="h-3 w-12 bg-slate-100 rounded" />
              </div>
              <div className="space-y-1">
                <div className="h-6 w-8 bg-slate-200 rounded" />
                <div className="h-3 w-16 bg-slate-100 rounded" />
              </div>
            </div>
          </div>
          {/* Desktop stats */}
          <div className="hidden md:flex gap-4 flex-none">
            <div className="space-y-1 text-right">
              <div className="h-8 w-10 bg-slate-200 rounded ml-auto" />
              <div className="h-3 w-12 bg-slate-100 rounded" />
            </div>
            <div className="space-y-1 text-right">
              <div className="h-8 w-10 bg-slate-200 rounded ml-auto" />
              <div className="h-3 w-20 bg-slate-100 rounded" />
            </div>
          </div>
        </div>

        {/* Body — two columns */}
        <div className="grid grid-cols-1 md:grid-cols-2">
          {/* Contacts */}
          <section className="p-4 md:p-6 border-b md:border-b-0 md:border-r border-line">
            <div className="h-3 w-40 bg-slate-100 rounded mb-4" />
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-1">
                  <div className="h-4 w-36 bg-slate-200 rounded" />
                  <div className="h-3 w-28 bg-slate-100 rounded" />
                  <div className="h-3 w-16 bg-slate-100 rounded" />
                </div>
              ))}
            </div>
          </section>

          {/* Signals */}
          <section className="p-4 md:p-6">
            <div className="h-3 w-32 bg-slate-100 rounded mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="bg-slate-50 border border-line rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-5 w-20 bg-slate-200 rounded-full" />
                    <div className="h-3 w-24 bg-slate-100 rounded" />
                  </div>
                  <div className="h-4 w-3/4 bg-slate-200 rounded" />
                  <div className="space-y-1.5">
                    <div className="h-3 w-full bg-slate-100 rounded" />
                    <div className="h-3 w-4/5 bg-slate-100 rounded" />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
