/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output mode for Docker
  output: "standalone",
  
  // Optimize for production
  experimental: {
    outputFileTracingRoot: process.cwd(),
  },
  
  // API configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production' 
          ? 'http://backend:8000/:path*'
          : 'http://localhost:8000/:path*',
      },
    ];
  },
  
  // Environment variables
  env: {
    BACKEND_URL: process.env.NODE_ENV === 'production' 
      ? 'http://backend:8000'
      : 'http://localhost:8000',
    RTSP_URL: process.env.NODE_ENV === 'production'
      ? 'http://rtsp-server:8080/video'
      : 'http://localhost:8080/video',
  },
  
  // Image optimization
  images: {
    domains: ['localhost', 'backend', 'rtsp-server'],
    unoptimized: true, // For Docker environment
  },
  
  // Headers for RTSP streaming
  async headers() {
    return [
      {
        source: '/video',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
          {
            key: 'Pragma',
            value: 'no-cache',
          },
          {
            key: 'Expires',
            value: '0',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
