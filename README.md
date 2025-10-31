# UAE Legal Agent – FastAPI + Next.js RAG MVP

本项目实现了基于 UAE 法律条文切片的最小可运行 RAG 原型，包含 FastAPI 后端、Next.js 前端以及带 pgvector 的 PostgreSQL 检索层，可通过 Docker Compose 一键启动。

## 架构概览

```
               ┌──────────────────────────────────────────────────────┐
               │                      Frontend                       │
               │  Next.js 14 · React 18 · TailwindCSS · SWR          │
               │  - / : 搜索与筛选                                   │
               │  - /results/[id] : 条文详情与引用块                 │
               └───────────────▲─────────────────────────────────────┘
                               │ REST / JSON
                               │
┌──────────────────────────────┴──────────────────────────────┐
│                         Backend                             │
│  FastAPI · SQLAlchemy · pgvector · pytest                   │
│  - /search  : 混合检索（关键字 + 向量）                     │
│  - /get_by_id/{id} : 条文全文                               │
│  - /answer  : 结构化引用回答                                │
│     │                                                      │
│     │ SQLAlchemy Session                                   │
│     ▼                                                      │
│  utils/seed_loader → data/seed_samples.json → legal_slice  │
└───────────────▲────────────────────────────────────────────┘
                │
                │ SQL / pgvector (vector(768))
                │
        ┌───────┴───────────────────────────┐
        │         PostgreSQL 15 + pgvector  │
        │  - legal_slice 表                 │
        │  - Hybrid 索引 + 过滤             │
        └────────────────────────────────────┘
```

## 快速开始

```bash
# 1) 复制环境变量样例
cp .env.example .env

# 2) 构建并启动三服务
docker compose up --build

# 3) 访问地址
# 前端:  http://localhost:3000
# 后端:  http://localhost:8000/docs

# 4) 导入示例数据（新终端）
docker compose exec backend python -m utils.seed_loader ./data/seed_samples.json
```

> 首次运行需等待 `frontend` 完成 Next.js 构建，终端日志显示 `ready - started server on 0.0.0.0:3000` 即可访问。

## 目录结构

- `backend/`：FastAPI 应用、RAG 检索逻辑、SQLAlchemy ORM、pgvector 混合检索与测试。
- `frontend/`：Next.js App Router 页面、搜索组件、Tailwind 样式。
- `data/seed_samples.json`：10+ 条 UAE 法规样例（联邦 / 迪拜 / DIFC / ADGM）。
- `docker-compose.yml`：数据库、后端、前端三容器协同启动。
- `.env.example` & `backend/.env.example`：统一配置入口。

## 后端说明

- `main.py`：FastAPI 实例 + CORS。启动时执行 `init_db()` 保证 pgvector 表结构。
- `search.py`：实现 `embed`（本地哈希向量占位）、`vector_search`、`keyword_search`、`hybrid_search`，并应用法域 / 状态 / 时间过滤，支持 `PGVECTOR_METRIC={cosine|ip|euclidean}`。
- `rag.py`：封装 `/search` 与 `/answer` 输出，生成 Citation 列表及固定免责声明。
- `utils/seed_loader.py`：从 JSON 读取条文切片，写入 Postgres 并生成占位向量，可重复执行实现 upsert。
- `utils/init_neon_pgvector.py`：Neon / Postgres 15 环境下一键创建 `legal_slices` 表、索引与 pgvector 扩展。
- `utils/upsert_slice.py`：命令行插入或更新单条 `legal_slices` 记录（支持自定义向量或占位生成）。
- `utils/search_vector.py`：向量近邻调试工具，支持 `<=> / <-> / <#>` 自动切换。
- `tests/test_search.py`：校验向量检索可返回结果与 `as_of` 过滤逻辑。

### Neon pgvector 工具脚本

```bash
# 初始化 Neon / Postgres pgvector 表结构（读取 PGVECTOR_DIM, PGVECTOR_METRIC 环境变量）
docker compose exec backend python -m backend.utils.init_neon_pgvector

# Upsert 单条样例（需提供基础字段；未提供 embedding 时根据 --text 生成占位向量）
docker compose exec backend python -m backend.utils.upsert_slice \
  --id sample#1 \
  --jurisdiction "Dubai" \
  --instrument-title "Dubai Landlord and Tenant Law" \
  --structure-path "Chapter 3 > Article 25" \
  --topics tenancy,real_estate \
  --text "tenancy deposit handling" \
  --effective-from 2020-01-01

# 使用文本查询最近邻
docker compose exec backend python -m backend.utils.search_vector --query "tenancy deposit"
```

### API 约定

- `POST /search` → `SearchResponse`：返回条文卡片（标题、结构路径、官方链接、公报号、摘要）。
- `GET /get_by_id/{id}` → `LegalSlice`：完整条文与元数据。
- `POST /answer` → `AnswerResponse`：基于 `/search` 结果给出强制引用回答与免责声明。
- 免责声明固定为：`信息检索工具，非法律意见；以官方文本为准（DIFC/ADGM 英文为权威；联邦英文多为参考译文）`。

## 前端说明

- `/` 页面：`SearchBar` + `FilterPanel` + `LawCard` 列表，支持法域、主题、日期筛选。
- `/results/[id]`：调用后端详情接口，展示全文与 `CitationBlock`（复制官方链接）。
- 静态枚举法域/主题；后续可改为从 API 下发。
- Tailwind 主题色：primary（蓝）、accent（青）、neutral（深灰），配合卡片式布局。

## RAG 流程

1. `SearchBar` 触发 `/search`。
2. 后端 `hybrid_search`：
   - `keyword_search`：`ILIKE` 匹配标题/路径/全文。
   - `vector_search`：pgvector 近邻（支持 cosine / inner product / euclidean）。
   - 分数融合 + 法域匹配加权，取前 8 条。
3. `rag.build_citation` 输出 200 字摘要、标题、路径、官方链接、公报号。
4. `/answer` 在上述结果上生成摘要回答，并附带强制引用与免责声明。

## 验收与测试

- `docker compose up --build` 后访问 `http://localhost:3000/` 可检索样例。
- `docker compose exec backend pytest`：运行后端单测。
- `docker compose exec backend python -m utils.seed_loader ./data/seed_samples.json`：重复执行将覆盖更新。

## 二次开发指引

- **替换嵌入模型**：在 `backend/search.py::embed` 中接入实际向量服务（如本地模型或 OpenAI 兼容接口），并确保 `vector_embedding` 保存维度一致。
- **关键字检索增强**：可引入 PostgreSQL `tsvector` 全文检索或独立 BM25 服务，替换 `keyword_search` 逻辑。
- **数据采集**：`data/seed_samples.json` 可扩展为爬虫输出，或对接官方 API。
- **前端 API**：若需代理或鉴权，可在 `NEXT_PUBLIC_API_BASE_URL` 指向网关服务。

## 可替换模块清单

1. 嵌入生成：`backend/search.py::embed`（当前为哈希伪向量）。
2. 关键字检索器：`backend/search.py::keyword_search`（可接入 Elastic / OpenSearch / BM25）。
3. 数据导入：`backend/utils/seed_loader.py`（可替换为 ETL / 爬虫 / 定时任务）。
4. 前端主题：`frontend/tailwind.config.ts`（颜色、组件风格可定制）。
5. Docker 基础镜像：可将 `backend/Dockerfile` 替换为企业内部 Python 基线镜像，或将 `frontend/Dockerfile` 改为生产多阶段构建。

## 调试技巧

- `docker compose logs -f backend` 观察 FastAPI 日志。
- `docker compose exec db psql -U postgres -d uae_legal -c "SELECT id, level, name FROM legal_slice LIMIT 5;"` 检查数据写入。
- `curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d '{"query": "tenancy deposit"}'` 进行 API smoke test。

## Render 部署提示

- 根目录已包含 `runtime.txt` 与 `render.yaml`，Render 会自动使用 Python `3.11.9`，避免 Pydantic 1.x 与 Python 3.13 的兼容问题。
- Render Web 服务配置示例：
  - Root Directory: `.`（整个仓库）
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
  - 可在 Render 控制台添加 `DB_URL`、`PGVECTOR_DIM` 等环境变量或导入 `.env`。
- 如果需部署前端，可额外创建一个 Static Site，使用 `frontend/` 目录运行 `npm install && npm run build`（deploy command `npm run build`，publish `frontend/out` 或使用 Next.js Serverless 方案）。

---

> 本工具用于资讯检索与内部评估，不构成法律意见；请以官方文本为准。DIFC/ADGM 英文文本具有权威效力，联邦英文译本仅供参考。
