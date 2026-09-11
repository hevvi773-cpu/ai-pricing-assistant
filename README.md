# 🏷️ AI定价+风控助手

> AI-Native 二手商品智能定价 + 交易风控助手——输入商品信息，AI 输出价格区间 + 置信度 + 定价理由，支持对话式微调；同时识别定价异常与交易风险，辅助卖家规避低价抛售与骗局。

**AI-Native，不是 AI-First**：核心体验完全由 AI 驱动——自然语言输入、AI 生成定价理由、对话式价格调整。没有大模型，这个产品就不存在。

---

## 🎯 产品定位

校园二手交易中，卖家最常遇到的问题是"不知道挂多少钱"——挂高了卖不掉，挂低了自己亏。传统定价工具只给一个数字，没有理由、没有置信度、不能交互调整。

AI定价+风控助手用大模型 + RAG 检索解决这个问题：
- 输入商品名称/品类/成色/图片
- AI 检索同类商品历史成交数据
- 输出价格区间 + 置信度标签 + 自然语言定价理由
- 支持对话式微调（"我急售，便宜点""配件齐全，能贵点吗"）

---

## ✨ 核心功能

### AI 智能估价
- 输入商品名称、品类、成色（4 档）、图片（可选）
- AI 基于同类商品历史成交数据生成价格区间
- 输出建议价格、价格区间、置信度标签

### 置信度系统
- **高置信度（绿色）**：数据源充足，推荐参考
- **中置信度（黄色）**：数据有限，仅供参考
- **低置信度（灰色）**：数据源不足，区间自动拉宽，展示免责声明

### 双滑块微调
- 左右滑块分别控制最低价和最高价
- 默认锚定 AI 最佳猜测值（区间中间值）
- 实时显示调整后的价格

### 对话式微调
- 自然语言描述调整意图（"急售""配件齐全""成色比描述好"）
- AI 识别意图，动态调整价格并给出理由
- 体现 AI-Native 的交互体验

### AI 定价理由
- 不只是给一个数字，而是给出自然语言解释
- 参考了多少条同类成交记录
- 价格区间的计算依据

### 交易风控
- **异常定价识别**：当 AI 估价远高于/低于同类成交区间时，自动标记"可能虚高 / 疑似低价引流"，给出建议价
- **风险提示**：识别高风险交易特征（价格异常、卖家信息缺失等），在定价结果旁给出风险提示
- **定价→风控一体化**：同一套 RAG 数据源同时支撑定价基准与风控判定，风控不引入额外成本

---

## 🛠 技术栈

### 前端
| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 19.2 |
| 语言 | TypeScript | 5.9 |
| 构建 | Vite | 8 |
| 样式 | Tailwind CSS | 4.2 |
| 组件库 | shadcn/ui（Radix UI） | — |
| 路由 | react-router-dom | 7.13 |
| 动画 | framer-motion | 12.38 |
| 图标 | lucide-react | 0.577 |

### 后端
| 类别 | 技术 |
|------|------|
| 框架 | FastAPI |
| 服务器 | uvicorn |
| 数据验证 | Pydantic |
| 大模型 | 通义千问（DASHSCOPE_API_KEY） |
| 数据检索 | RAG（Mercari 公开数据集） |

### 数据
- **Mercari Price Suggestion Challenge**：Kaggle 公开数据集，150 万条二手商品成交记录
- 字段：商品标题、描述、品类、品牌、成色、价格
- 用途：RAG 检索库，为 AI 定价提供真实成交数据参考

---

## 📁 项目结构

```
ai-pricing-assistant/
├── frontend/                    # 前端 React 应用
│   ├── src/
│   │   ├── pages/
│   │   │   └── PricingPage/    # 定价主页（输入+结果+对话微调）
│   │   ├── services/
│   │   │   └── pricingService.ts  # API 服务封装
│   │   ├── components/ui/       # shadcn/ui 组件（55 个）
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── ...
├── backend/                     # 后端 FastAPI
│   ├── app/
│   │   └── main.py              # API 入口（/api/price, /api/price/adjust）
│   └── requirements.txt
├── data/                        # 数据集（Mercari train.tsv）
└── README.md
```

---

## 🚀 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 后端

```bash
cd backend
pip install -r requirements.txt

# 配置大模型 API Key（可选，未配置时使用 mock 数据）
export DASHSCOPE_API_KEY=your_api_key_here

python app/main.py
# API 运行在 http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 环境变量

```
# 前端 .env
VITE_API_BASE=http://localhost:8000

# 后端 .env
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

> 未配置 API Key 时，后端使用 mock 定价逻辑，前端可正常运行和演示。

---

## 🧠 AI-Native 设计说明

### 为什么是 AI-Native？

| 维度 | AI-First（前两个项目） | AI-Native（本项目） |
|------|----------------------|-------------------|
| 核心业务 | 移除 AI 后仍可完整运行 | 移除 AI 后产品不存在 |
| 输入方式 | 表单输入为主 | 自然语言 + 图片 + 表单 |
| 输出方式 | 结构化数据 | 自然语言理由 + 结构化数据 |
| 交互方式 | 点击操作 | 对话式微调 |
| 不确定性处理 | 功能要么有要么没有 | 置信度标签 + 区间 + 免责声明 |

### 三个核心产品决策

1. **独立定价模块，不内嵌发布流程**——降低使用门槛，覆盖"只是想查一下"的泛场景用户，查完价引导发布反哺转化
2. **AI 不确定时输出区间 + 置信度 + 免责声明**——用产品设计对冲技术不确定性，管理用户预期
3. **价格区间默认锚定中间值 + 双滑块微调**——降低用户决策成本，AI 给最佳猜测，用户在此基础上调整

---

## 📊 API 接口

### POST /api/price
AI 智能估价

**请求体**：
```json
{
  "product_name": "iPhone 13 128G 蓝色",
  "category": "手机数码",
  "condition": "几乎全新"
}
```

**响应**：
```json
{
  "suggested_price": 2800,
  "price_min": 2380,
  "price_max": 3220,
  "confidence": "high",
  "reasoning": "基于同类商品历史成交数据...",
  "comparables": [
    {"name": "iPhone 13 128G", "price": 2750, "condition": "几乎全新"}
  ]
}
```

### POST /api/price/adjust
对话式价格微调

**请求体**：
```json
{
  "product_name": "iPhone 13 128G 蓝色",
  "category": "手机数码",
  "condition": "几乎全新",
  "current_price": 2800,
  "message": "我急售，可以便宜点"
}
```

---

## ⚠️ 项目状态

- ✅ 前端核心页面完成（输入表单 + 结果展示 + 双滑块 + 对话微调）
- ✅ 后端 API 框架完成（FastAPI + mock 定价逻辑）
- ✅ 项目结构和技术栈确定
- 🚧 大模型接入（通义千问）——待开发
- 🚧 Mercari 数据集清洗和 RAG 检索——待开发（数据集下载中，Kaggle 身份验证审核中）
- 🚧 图片识别（多模态大模型）——待开发
- 🚧 部署上线——待开发

> 当前版本使用 mock 定价逻辑，可正常运行和演示。接入真实大模型和数据集后即可生产使用。

---

## 📄 License

MIT
