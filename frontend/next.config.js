/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",  // 生产部署：单文件 server.js，无需 node_modules
  // 代理超时：扫描件 OCR 识别需几分钟，Next.js 14 默认 30s 会掐断连接，调到 15 分钟
  experimental: {
    proxyTimeout: 900000,
  },
  // 将 /api 请求代理到 FastAPI 后端
  // 开发环境: localhost:8000，Docker 环境: backend:8000
  async rewrites() {
    const apiHost = process.env.API_HOST || "localhost";
    return [
      {
        source: "/api/:path*",
        destination: `http://${apiHost}:8000/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
