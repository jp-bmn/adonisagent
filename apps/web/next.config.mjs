/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@adonis/shared', '@adonis/db'],
  serverExternalPackages: [],
};

export default nextConfig;
