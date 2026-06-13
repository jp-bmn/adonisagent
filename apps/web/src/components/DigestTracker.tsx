'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

const BASE_URL = 'https://adonisagents-production.up.railway.app/api/v1';
const DEFAULT_USER_ID = 'df7c14fd-cde3-4025-be00-ca42f4d31741';

// Fires POST /digest-views when the user arrives from a digest email link.
// Expects UTM params: ?utm_source=digest&digest_id=<uuid>
// Joel's Task 15 — scaffolded; endpoint may not be live yet, fails silently.
export default function DigestTracker() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const utmSource = searchParams.get('utm_source');
    const digestId = searchParams.get('digest_id');

    if (utmSource !== 'digest' || !digestId) return;

    fetch(`${BASE_URL}/digest-views`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': DEFAULT_USER_ID,
      },
      body: JSON.stringify({ digest_id: digestId }),
    }).catch(() => {});
  }, [searchParams]);

  return null;
}
