'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

// Fires POST /api/digest-view when an AE arrives from a digest link.
// Expected URL params: ?utm_source=digest&digest_id=<uuid>&ae_id=<uuid>
export default function DigestTracker() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const utmSource = searchParams.get('utm_source');
    const digestId = searchParams.get('digest_id');
    const aeId = searchParams.get('ae_id');

    if (utmSource !== 'digest' || !aeId) return;

    fetch('/api/digest-view', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ae_id: aeId, digest_id: digestId }),
    }).catch(() => {});
  }, [searchParams]);

  return null;
}
