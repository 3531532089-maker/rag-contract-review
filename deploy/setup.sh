#!/bin/bash
# ============================================
# 智能合同审查系统 — 阿里云一键初始化脚本
# ============================================
# 在服务器上执行:
#   chmod +x setup.sh
#   sudo ./setup.sh
#
# 这个脚本会：
#   1. 安装所有系统依赖 (Python, Node.js, Nginx)
#   2. 创建 Python 虚拟环境并安装依赖
#   3. 构建前端
#   4. 配置 Nginx + systemd
#   5. 启动所有服务

set -e  # 遇到错误立即退出

APP_USER="${SUDO_USER:-ubuntu}"
APP_DIR="/home/$APP_USER/contract-review"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

echo "========================================"
echo "  智能合同审查系统 — 一键部署"
echo "  用户: $APP_USER"
echo "  目录: $APP_DIR"
echo "========================================"

# ===== 1. 安装系统依赖 =====
echo ""
echo "[1/6] 安装系统依赖..."
sudo apt update -qq
sudo apt install -y -qq python3 python3-pip python3-venv nginx curl

# 安装 Node.js 20 (通过 NodeSource)
if ! command -v node &>/dev/null; then
    echo "安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y -qq nodejs
fi
echo "  ✓ Python: $(python3 --version)"
echo "  ✓ Node:   $(node --version)"
echo "  ✓ Nginx:  $(nginx -v 2>&1)"

# ===== 2. 配置 Python 虚拟环境 =====
echo ""
echo "[2/6] 配置 Python 虚拟环境..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 创建上传目录
mkdir -p uploads logs

echo "  ✓ Python 依赖安装完成"

# ===== 3. 构建前端 =====
echo ""
echo "[3/6] 构建前端 (standalone 模式)..."
cd "$FRONTEND_DIR"
npm install --quiet
npm run build

# 确认 standalone 输出
if [ -f .next/standalone/server.js ]; then
    # 复制 static 文件到 standalone
    cp -r .next/static .next/standalone/.next/static 2>/dev/null || true
    echo "  ✓ 前端构建完成 (standalone)"
else
    echo "  ⚠ standalone 未启用，在 next.config.js 中添加: output: 'standalone'"
    echo "    使用 production 模式启动替代方案"
fi

# ===== 4. 安装 systemd 服务 =====
echo ""
echo "[4/6] 安装 systemd 服务..."

# 修改 service 文件中的用户和路径
sed -i "s|User=.*|User=$APP_USER|" "$APP_DIR/deploy/contract-backend.service"
sed -i "s|User=.*|User=$APP_USER|" "$APP_DIR/deploy/contract-frontend.service"

sudo cp "$APP_DIR/deploy/contract-backend.service" /etc/systemd/system/
sudo cp "$APP_DIR/deploy/contract-frontend.service" /etc/systemd/system/
sudo systemctl daemon-reload
echo "  ✓ systemd 服务已安装"

# ===== 5. 配置 Nginx =====
echo ""
echo "[5/6] 配置 Nginx..."

# 先跑 HTTP 模式（注释掉 SSL 相关行）
cp "$APP_DIR/deploy/nginx.conf" /tmp/nginx-contract.conf
# 只需要 HTTP server block，去掉 SSL server block 和重定向
cat > /tmp/nginx-contract-http.conf << 'NGINX'
server {
    listen 80;
    server_name _;  # 接受所有域名/IP

    client_max_body_size 30M;

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 130s;
        proxy_connect_timeout 10s;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

sudo cp /tmp/nginx-contract-http.conf /etc/nginx/sites-available/contract-review
sudo ln -sf /etc/nginx/sites-available/contract-review /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # 去默认站点

sudo nginx -t && sudo systemctl reload nginx
echo "  ✓ Nginx 配置完成"

# ===== 6. 启动服务 =====
echo ""
echo "[6/6] 启动服务..."

# 先下载 Embedding 模型（避免首次请求等太久）
echo "  下载 Embedding 模型 (首次约 2-3 分钟)..."
cd "$BACKEND_DIR"
source venv/bin/activate
timeout 120 python3 -c "
from app.services.vector_store import get_or_create_collection
get_or_create_collection()
print('Model ready')
" 2>&1 || echo "  ⚠ 模型下载超时，将在首次请求时继续下载"

# 启动后端
sudo systemctl enable contract-backend
sudo systemctl start contract-backend
echo "  ✓ 后端已启动"

# 启动前端
sudo systemctl enable contract-frontend
sudo systemctl start contract-frontend
echo "  ✓ 前端已启动"

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "  访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '你的公网IP')"
echo ""
echo "  常用命令："
echo "    sudo systemctl status contract-backend   # 后端状态"
echo "    sudo systemctl status contract-frontend  # 前端状态"
echo "    sudo journalctl -u contract-backend -f   # 后端日志"
echo "    sudo journalctl -u contract-frontend -f  # 前端日志"
echo "    sudo nginx -t && sudo systemctl reload nginx  # 重载 Nginx"
echo ""
