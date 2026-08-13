/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",  // 生产部署：单文件 server.js，无需 node_modules
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
