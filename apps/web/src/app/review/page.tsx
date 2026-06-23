import { fetchPendingReview } from '@/lib/api';
import { ReviewQueue } from '@/components';

const HOSPITAL_NAMES: Record<string, string> = {
  'a4725891-7354-4187-a6c1-93d7ea9a078f': 'Ascension',
  '7b836e62-3ee8-4d10-b30e-028734a5f812': 'CommonSpirit Health',
  'a17f653f-8479-4159-9149-63e65d2d50a2': 'Jefferson Health',
  'f0f6b915-3e9d-4040-ba4d-c89339a1e134': 'NewYork-Presbyterian',
  'f3ab9c05-4b2b-42e9-9653-2e9dc8f98476': 'UMass Memorial',
  '3aebd89a-1d2c-465c-a22b-08ced9613027': 'University of Arkansas Medical Sciences',
};

export default async function ReviewPage() {
  const rawSignals = await fetchPendingReview();
  const signals = rawSignals.map((s) => ({
    ...s,
    hospital_name: HOSPITAL_NAMES[s.hospital_id] ?? s.hospital_id,
  }));

  return (
    <div className="px-4 py-5 md:px-8 md:py-7 pb-20 md:pb-7">
      <header className="mb-6">
        <h1 className="font-serif text-2xl font-semibold text-brand">Review Queue</h1>
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
