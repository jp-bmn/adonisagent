import { fetchPendingReview } from '@/lib/api';
import { ReviewQueue, ContactReviewQueue } from '@/components';

export default async function ReviewPage() {
  const signals = await fetchPendingReview();

  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7 space-y-10">
      {/* Signals */}
      <section>
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
      </section>

      {/* Contacts pending human verification */}
      <section>
        <header className="mb-4">
          <h2 className="font-serif text-xl font-semibold text-brand">Contact verification</h2>
          <p className="text-sm text-slate-500 mt-1">
            Contacts found by the AI agent with lower confidence — review and approve or reject.
          </p>
        </header>
        <ContactReviewQueue />
      </section>
    </div>
  );
}
