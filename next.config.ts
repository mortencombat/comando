import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  
  distDir: process.env.NODE_ENV === 'production' 
  ? './server/comando/static'
  : '.next',
};

export default nextConfig;
