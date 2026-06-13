'use client';

import { useState } from 'react';
import Image from 'next/image';

interface HospitalLogoProps {
  name: string;
  websiteUrl: string | null;
  size?: 'sm' | 'md' | 'lg';
}

// Fallback domain map for known hospitals — used when website_url is not in the API response
const KNOWN_DOMAINS: Record<string, string> = {
  ascension: 'ascension.org',
  commonspirit: 'commonspirithealth.org',
  'newyork-presbyterian': 'nyp.org',
  'umass memorial': 'umassmemorial.org',
  'university of arkansas medical sciences': 'uams.edu',
  uams: 'uams.edu',
};

function logoUrl(name: string, websiteUrl: string | null): string {
  const token = process.env.NEXT_PUBLIC_LOGODEV_TOKEN;
  if (!token) return '';
  try {
    let domain = '';
    if (websiteUrl) {
      domain = new URL(websiteUrl).hostname.replace(/^www\./, '');
    } else {
      const key = Object.keys(KNOWN_DOMAINS).find((k) => name.toLowerCase().includes(k));
      if (key) domain = KNOWN_DOMAINS[key] || '';
    }
    if (!domain) return '';
    return `https://img.logo.dev/${domain}?token=${token}&size=64`;
  } catch {
    return '';
  }
}

const sizes = {
  sm: { container: 'w-9 h-9 rounded-lg text-base', img: 36 },
  md: { container: 'w-11 h-11 rounded-xl text-lg', img: 44 },
  lg: { container: 'w-14 h-14 rounded-xl text-2xl', img: 56 },
};

export default function HospitalLogo({ name, websiteUrl, size = 'lg' }: HospitalLogoProps) {
  const [failed, setFailed] = useState(false);
  const url = logoUrl(name, websiteUrl);
  const { container, img } = sizes[size];

  if (url && !failed) {
    return (
      <div
        className={`${container} bg-white border border-line flex items-center justify-center overflow-hidden flex-none`}
      >
        <Image
          src={url}
          alt={`${name} logo`}
          width={img}
          height={img}
          className="object-contain p-1"
          onError={() => setFailed(true)}
          unoptimized
        />
      </div>
    );
  }

  return (
    <div
      className={`${container} bg-gradient-to-br from-navy-900 to-navy-700 text-white flex items-center justify-center font-serif font-bold flex-none`}
    >
      {name[0]}
    </div>
  );
}
