'use client';

import { useState } from 'react';
import Image from 'next/image';

interface HospitalLogoProps {
  name: string;
  websiteUrl: string | null;
  size?: 'sm' | 'md' | 'lg';
}

function clearbitUrl(websiteUrl: string): string {
  try {
    const hostname = new URL(websiteUrl).hostname.replace(/^www\./, '');
    return `https://logo.clearbit.com/${hostname}`;
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
  const logoUrl = websiteUrl ? clearbitUrl(websiteUrl) : '';
  const { container, img } = sizes[size];

  if (logoUrl && !failed) {
    return (
      <div
        className={`${container} bg-white border border-line flex items-center justify-center overflow-hidden flex-none`}
      >
        <Image
          src={logoUrl}
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
