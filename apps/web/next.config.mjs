/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@adonis/shared', '@adonis/db'],
  serverExternalPackages: ['@supabase/ssr', '@supabase/supabase-js'],
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'img.logo.dev' },
    ],
  },
};

export default nextConfig;
