# 基于 RAG 的智能合同审查系统

一个使用 **RAG(检索增强生成)** 技术的智能合同审查平台。用户上传合同 PDF/Word,系统自动解析、切片、向量化并建立知识库,随后可通过大语言模型进行 **风险分析、智能问答和合同审查**。

## 功能特性

- 📄 **文件解析** —— 支持 PDF(PyMuPDF)与 Word(python-docx),自动检测加密文件与扫描件
- 🧩 **文本切片** —— 按中文语义分隔符递归切块,支持重叠,保证上下文完整
- 🔍 **向量检索** —— 中文 Embedding 模型(`text2vec-base-chinese`)+ ChromaDB 语义检索
- 💬 **RAG 问答** —— 检索相关合同段落 → 组装 Prompt → LLM 生成回答,并返回引用来源
- ⚖️ **一键风险审查** —— 从 8 个维度(主体/义务/价款/期限/违约/知产/解除/争议)扫描合同,输出结构化 JSON 风险报告
- 🔐 **安全防护** —— JWT 管理员认证、接口限流、安全响应头、文件名与路径校验、重复上传检测

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React / Next.js + Tailwind CSS |
| 后端 | Python 3.11+ / FastAPI |
| AI 编排 | LangChain |
| 大语言模型 | 任意兼容 OpenAI 接口的服务(DeepSeek / OpenAI / 通义 / Kimi / Ollama) |
| 向量数据库 | ChromaDB |
| 关系数据库 | SQLite(默认)/ PostgreSQL(生产) |
| 文本解析 | PyMuPDF / python-docx |
| Embedding | shibing624/text2vec-base-chinese |

## 项目结构

```
rag-contract-review/
├── backend/                          # Python 后端（FastAPI）
│   ├── app/
│   │   ├── main.py                   # 应用入口：路由注册、中间件、生命周期、健康检查
│   │   ├── config.py                 # 集中配置：从 .env 读取全部配置项
│   │   ├── routes/                   # API 路由层（接口层）
│   │   │   ├── upload.py             #   合同上传 / 列表 / 详情 / 删除
│   │   │   ├── chat.py               #   RAG 智能问答
│   │   │   ├── review.py             #   一键风险审查
│   │   │   └── auth.py               #   管理员登录
│   │   ├── services/                 # 业务逻辑层（核心）
│   │   │   ├── pdf_parser.py         #   PDF / Word 文本提取
│   │   │   ├── text_splitter.py      #   中文语义文本切片
│   │   │   ├── vector_store.py       #   ChromaDB 向量存储与检索
│   │   │   ├── rag_service.py        #   RAG 问答（检索 → 组装 → 生成）
│   │   │   ├── review_service.py     #   风险审查（多角度检索 → LLM 结构化分析）
│   │   │   └── auth_service.py       #   JWT 令牌生成与校验
│   │   ├── models/                   # SQLAlchemy ORM 模型
│   │   │   └── contract.py           #   合同实体
│   │   ├── schemas/                  # Pydantic 数据校验模型
│   │   │   └── contract.py           #   请求 / 响应结构
│   │   ├── database/                 # 数据库连接与会话管理
│   │   │   └── session.py
│   │   ├── dependencies/             # FastAPI 依赖注入
│   │   │   └── auth.py               #   require_auth 鉴权依赖
│   │   └── middleware/               # 中间件
│   │       ├── security.py           #   安全响应头
│   │       └── rate_limit.py         #   接口限流
│   ├── requirements.txt              # Python 依赖清单
│   ├── .env.example                  # 环境变量配置模板
│   ├── Dockerfile                    # 后端容器镜像
│   └── test_all.py                   # 冒烟测试脚本
├── frontend/                         # 前端（Next.js）
│   └── src/
│       ├── app/                      # 页面路由
│       ├── components/               # 可复用组件
│       └── lib/                      # 工具函数 & 类型定义
├── deploy/                           # 生产部署配置
│   ├── docker-compose.yml
│   ├── nginx.conf
│   ├── setup.sh
│   └── contract-*.service            # systemd 服务单元
├── docker-compose.yml                # 本地基础设施容器
└── README.md
```

### 后端分层设计

```
routes（接口层）
   ↓ 调用
services（业务逻辑层）
   ↓ 调用
models / schemas / database（数据层）
```

- **routes** 只负责接收请求、参数校验、调用 service、返回响应
- **services** 承载 RAG、审查、解析等核心业务逻辑
- **models** 定义数据库表结构,**schemas** 定义接口数据结构,二者解耦

## 环境配置

复制环境变量模板并填入真实值:

```bash
cd backend
cp .env.example .env
```

必填配置项(缺失会导致启动失败):

| 变量 | 说明 | 生成方式 |
|------|------|----------|
| `LLM_API_KEY` | 大语言模型 API Key | 前往服务商申请 |
| `ADMIN_PASSWORD_HASH` | 管理员密码的 SHA-256 哈希 | `python -c "import hashlib; print(hashlib.sha256(b'密码').hexdigest())"` |
| `JWT_SECRET` | JWT 签名密钥 | `python -c "import secrets; print(secrets.token_hex(32))"` |

其余配置项(数据库、切片参数、CORS 等)均有默认值,详见 `.env.example` 注释。

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env,填入 LLM_API_KEY、ADMIN_PASSWORD_HASH、JWT_SECRET
```

### 3. 启动后端

```bash
uvicorn app.main:app --reload
```

启动后访问 `http://localhost:8000/docs` 查看交互式 API 文档。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

## API 接口

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| `GET` | `/health` | 健康检查(数据库 / 向量库 / LLM 状态) | 无 |
| `POST` | `/api/auth/login` | 管理员登录,返回 JWT | 无 |
| `POST` | `/api/upload/contract` | 上传合同并建立向量索引 | ✅ |
| `GET` | `/api/upload/contracts` | 合同列表(分页) | 无 |
| `GET` | `/api/upload/contracts/{id}` | 合同详情 | 无 |
| `DELETE` | `/api/upload/contracts/{id}` | 删除合同(软删除 + 清理向量) | ✅ |
| `POST` | `/api/chat` | RAG 智能问答 | ✅ |
| `POST` | `/api/review/{id}` | 触发一键风险审查 | ✅ |
| `GET` | `/api/review/{id}` | 查看审查结果 | 无 |

## 部署

### 本地(Docker Compose)

```bash
docker-compose up -d
```

### 生产环境

`deploy/` 目录提供了生产部署配置(Nginx 反向代理 + systemd 服务),详见 `deploy/setup.sh`。

## 许可

MIT License(如适用)。
