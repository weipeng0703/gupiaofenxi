# 股票分析助手 (gupiaofenxi)

A 股自选股实时分析工具 — K 线图表 + 技术指标 + 策略信号

## 功能

- 📊 **四面板 K 线图**：蜡烛图 + 成交量 + RSI + KDJ，联动缩放
- ⚡ **实时行情**：交易日实时获取自选股行情数据（15秒刷新）
- 🎯 **策略信号**：基于 RSI/KDJ/均线等指标的买卖信号自动检测
- 📋 **自选股管理**：搜索添加、分组管理自选股列表
- 🔔 **信号通知**：前端实时显示策略触发的买卖信号
- 🔧 **可配置策略**：YAML 格式策略配置，支持阈值/交叉/均线突破等条件

## 技术栈

- **后端**: Python FastAPI + AKShare + pandas-ta + SQLite + WebSocket
- **前端**: Vue 3 + TypeScript + Pinia + ECharts + Axios

## 快速开始

### 前置条件

- **Python 3.11+**（从 [python.org](https://python.org) 下载，勾选 "Add to PATH"）
- **Node.js 18+**

### 安装依赖

```bash
# 方式一：双击 scripts/setup.bat（Windows）

# 方式二：手动安装
cd backend
pip install -r requirements.txt

cd frontend
npm install
```

### 启动服务

```bash
# 方式一：双击 scripts/start.bat（Windows）

# 方式二：手动启动
# 后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（另一个终端）
cd frontend
npm run dev
```

访问 http://localhost:5173 使用前端页面

API 文档访问 http://localhost:8000/docs

## 使用流程

1. 在左侧搜索框输入股票代码或名称（如 "平安" 或 "000001"）
2. 点击搜索结果添加到自选股列表
3. 点击自选股查看 K 线图表和指标数据
4. 通过 ChartToolbar 切换日K/周K/5分钟等周期
5. 右侧信号面板显示策略触发的买卖信号

## 策略配置

策略使用 YAML 格式定义，位于 `backend/app/strategies/` 目录：

- `rsi_reversal.yaml` — RSI 超买超卖策略
- `kdj_golden_cross.yaml` — KDJ 金叉死叉策略
- `ma_breakout.yaml` — MA 均线突破策略
- `combined_signals.yaml` — 多指标共振策略

支持的条件类型：
- `threshold` — 阈值条件（RSI < 30 / RSI > 70 等）
- `cross` — 交叉条件（K 上穿 D 金叉 / K 下穿 D 死叉）
- `price_vs_ma` — 价格 vs MA 均线
- `volume_confirm` — 成交量确认

## 项目结构

```
gupiaofenxi/
├── backend/app/           # Python 后端
│   ├── main.py            # FastAPI 入口
│   ├── config.py          # 配置
│   ├── database.py        # SQLite 数据库
│   ├── models.py          # ORM 模型
│   ├── schemas.py         # Pydantic 模型
│   ├── api/               # REST API 路由
│   ├── services/          # 数据源/指标/策略/推送
│   ├── ws/                # WebSocket 处理
│   ├── strategies/        # YAML 策略配置
├── frontend/src/          # Vue 3 前端
│   ├── components/        # 组件
│   ├── views/             # 页面
│   ├── services/          # API/WebSocket 服务
│   ├── stores/            # Pinia 状态管理
│   ├── types/             # TypeScript 类型
│   ├── utils/             # 工具函数
├── data/                  # SQLite 数据库文件
├── scripts/               # 启动/安装脚本
```

## API 接口

| 端点 | 说明 |
|------|------|
| `GET /api/stocks/search?keyword=xxx` | 搜索股票 |
| `GET /api/stocks/{code}/full` | 获取 K线+指标+信号完整数据 |
| `GET /api/stocks/{code}/quote` | 实时行情 |
| `GET /api/watchlist` | 自选股列表 |
| `POST /api/watchlist` | 添加自选股 |
| `GET /api/signals` | 信号列表 |
| `GET /api/strategies` | 策略列表 |
| `WS /ws` | WebSocket 实时推送 |

## 扩展计划

- 港美股支持（通过 DataSourceInterface 抽象层添加新数据源）
- 微信/邮件推送通知
- 更多技术指标（MACD、布林带等）
- 策略回测功能