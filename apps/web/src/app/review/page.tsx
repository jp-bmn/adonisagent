import { fetchPendingReview } from '@/lib/api';
import { ReviewQueue } from '@/components';

export default async function ReviewPage() {
  const signals = await fetchPendingReview();

  return (
    <div className="px-8 py-7">
      <header className="mb-6">
        <h1 className="font-serif text-2xl font-semibold text-brand">Review queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Low-confidence signals (under 70%) awaiting Danielle&apos;s approval before digest.
          {signals.length > 0 && (
            <span className="ml-2 font-semibold text-urgent">{signals.length} pending</span>
          )}
        </p>
      </header>

      <ReviewQueue initialSignals={signals} />
    </div>
  );
}
