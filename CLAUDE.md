# 股票分析助手 (gupiaofenxi) — 项目文档

> A 股自选股实时分析工具 — K 线图表 + 技术指标 + 策略信号

## 项目概述

本项目是一个 **A 股实时分析系统**，采用前后端分离架构：
- 后端提供 REST API + WebSocket 实时推送
- 前端展示四面板 K 线图表 + 自选股管理 + 信号通知

核心功能：搜索添加自选股 → 查看 K 线图和指标 → 自动检测买卖信号 → 实时推送行情

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Python FastAPI + Uvicorn |
| 数据源 | AKShare（东方财富 A 股数据） |
| 数据库 | SQLite（aiosqlite 异步） + SQLAlchemy 2 ORM |
| 策略引擎 | YAML 配置 + 自定义评估引擎 |
| 实时推送 | WebSocket（FastAPI 内建） |
| 前端框架 | Vue 3 + TypeScript + Pinia 状态管理 |
| 图表库 | ECharts 6（四面板联动 K 线图） |
| HTTP 客户端 | Axios |

## 项目结构详解

```
gupiaofenxi/
├── .gitignore                 # Git 忽略规则（Python/Node/数据/IDE/OS/日志）
├── README.md                  # 项目说明文档（功能、技术栈、启动方式、API列表）
├── CLAUDE.md                  # 本文件 — 项目级文档供 Claude Code 使用
├── data/                      # SQLite 数据库文件目录（运行时自动创建）
├── scripts/                   # 便捷脚本
│   ├── setup.bat              # Windows 一键安装依赖脚本（pip + npm install）
│   └── start.bat              # Windows 一键启动脚本（同时启动后端+前端）
│
├── backend/                   # ── Python 后端 ──
│   ├── requirements.txt       # Python 依赖清单
│   ├── start.py               # Uvicorn 启动入口（python start.py 即可启动）
│   └── app/                   # FastAPI 应用包
│       ├── __init__.py        # 包标识（空）
│       ├── main.py            # ★ FastAPI 入口 — 组装所有模块（CORS/路由/WS/lifespan）
│       ├── config.py          # ★ 应用配置 — Pydantic BaseSettings 管理（DB路径/刷新间隔/策略目录/WS心跳/指标参数/CORS）
│       ├── database.py        # ★ 数据库管理 — 异步引擎+会话工厂+建表SQL（watchlist/strategies/signals/kline_cache）+WAL模式
│       ├── models.py          # ★ ORM 模型 — Watchlist/Strategy/Signal/KlineCache 四表
│       ├── schemas.py         # ★ Pydantic 模型 — 全部请求/响应数据结构（KlinePoint/IndicatorData/StockFullResponse/RealtimeQuote/WatchlistAdd/SignalItem/StrategyItem/WSMessage 等）
│       │
│       ├── api/               # REST API 路由
│       │   ├── __init__.py    # 包标识（空）
│       │   ├── stocks.py      # ★ 股票数据 API — 搜索/历史K线/完整数据(K线+指标+信号)/实时行情/分钟K线
│       │   ├── watchlist.py   # ★ 自选股 CRUD — 列表/添加/删除(软删除)/更新备注
│       │   ├── signals.py     # ★ 信号查询 API — 列表(筛选)/详情/标记已读
│       │   ├── strategies.py  # ★ 策略 CRUD — 列表/详情/创建/更新/删除
│       │
│       ├── services/          # 业务服务层
│       │   ├── __init__.py    # 包标识（空）
│       │   ├── data_source.py # ★ 抽象数据源接口 — DataSourceInterface（get_hist_kline/get_realtime_quote/get_realtime_quotes_batch/get_intraday_minutes/search_stock），方便未来扩展港美股
│       │   ├── akshare_source.py # ★ AKShare A股数据源实现 — 继承DataSourceInterface，核心设计：asyncio.to_thread包装同步调用+spot_em全市场缓存+限速机制+中文列名映射
│       │   ├── indicator_calc.py # ★ 技术指标计算器 — 纯Python实现（MA/RSI/KDJ），compute_all统一入口，参数来自config.py
│       │   ├── strategy_engine.py # ★ 策略评估引擎 — 读取YAML策略配置+逐条评估条件+生成信号，支持threshold/cross/price_vs_ma/volume_confirm四种条件类型，confidence权重计算
│       │   ├── realtime_push.py # ★ 实时推送服务 — 后台定时任务(periodic_refresh)：拉取行情→推送quote_update→计算指标→评估策略→推送signal_alert
│       │
│       ├── ws/                # WebSocket 模块
│       │   ├── __init__.py    # 包标识（空）
│       │   ├── protocol.py   # ★ WS消息协议 — 消息类型常量+make_message/make_quote_update/make_signal_alert/make_hist_data/make_error构造函数
│       │   ├── handler.py    # ★ WS连接管理器 — ConnectionManager(connect/disconnect/subscribe/unsubscribe/broadcast)+websocket_endpoint入口（处理subscribe/unsubscribe/request_hist/ping）
│       │
│       ├── strategies/        # YAML 策略配置文件
│       │   ├── __init__.py    # 包标识（空）
│       │   ├── rsi_reversal.yaml    # RSI超买超卖策略（BUY: RSI<30 / SELL: RSI>70）
│       │   ├── kdj_golden_cross.yaml # KDJ金叉死叉策略（BUY: K上穿D+J>0 / SELL: K下穿D+J<100）
│       │   ├── ma_breakout.yaml     # MA均线突破策略（BUY: 价格>MA20+量比>1.5）
│       │   ├── combined_signals.yaml # 多指标共振策略（BUY: RSI<35+KDJ金叉+价格>MA20）
│
├── frontend/                  # ── Vue 3 前端 ──
│   ├── package.json           # Node 依赖+脚本（dev/build/lint/format）
│   ├── index.html             # HTML 入口
│   ├── vite.config.ts         # Vite 构建配置（隐含）
│   ├── tsconfig.json          # TypeScript 配置
│   ├── env.d.ts               # Vite 环境类型声明
│   ├── src/
│   │   ├── main.ts            # ★ Vue 应用入口 — createApp + Pinia + Router
│   │   ├── App.vue            # ★ 根组件 — 顶部导航栏(标题+连接状态)+RouterView
│   │   │
│   │   ├── router/
│   │   │   └ index.ts         # ★ 路由配置 — 单路由 '/' → HomeView
│   │   │
│   │   ├── views/
│   │   │   ├── HomeView.vue   # ★ 主页面 — 三栏布局(左:自选股面板 / 中:K线图表 / 右:信号面板)，挂载时加载自选股+信号+连接WS+订阅行情
│   │   │   ├── AboutView.vue  # 关于页面（Vue CLI 脚手架残留）
│   │   │
│   │   ├── components/        # 业务组件
│   │   │   ├── stock/         # 股票相关组件
│   │   │   │   ├── KlineChart.vue    # ★ K线图表组件 — ECharts四面板(candlestick+volume+RSI+KDJ)+信号标记(markPoint)+数据watch自动更新+窗口resize响应
│   │   │   │   ├── ChartToolbar.vue  # ★ 图表工具栏 — 周期切换按钮(5分/15分/30分/60分/日K/周K/月K)+刷新/全屏按钮
│   │   │   │   ├── StockSearch.vue   # ★ 股票搜索组件 — 输入框+搜索按钮+下拉结果列表，选中后emit('select')
│   │   │   │   ├── StockQuote.vue    # ★ 实时行情卡片 — 股票名/代码/价格/涨跌幅/涨跌额/开盘/最高/最低/昨收/成交量/成交额，红涨绿跌
│   │   │   │
│   │   │   ├── watchlist/
│   │   │   │   ├── WatchlistPanel.vue # ★ 自选股面板 — 搜索框+自选股列表(名称/代码/实时行情)+点击选中+删除按钮
│   │   │   │
│   │   │   ├── signal/
│   │   │   │   ├── SignalPanel.vue    # ★ 信号面板 — 信号列表(买入↑/卖出↓)+策略名称+价格+置信度+时间+未读badge+点击标记已读
│   │   │   │
│   │   │   ├── HelloWorld.vue        # 脚手架残留组件
│   │   │   ├── TheWelcome.vue        # 脚手架残留组件
│   │   │   ├── WelcomeItem.vue       # 脚手架残留组件
│   │   │   ├── icons/                # 脚手架残留图标组件
│   │   │   ├── __tests__/            # HelloWorld 单元测试（脚手架残留）
│   │   │
│   │   ├── services/          # 前端服务层
│   │   │   ├── api.ts         # ★ Axios HTTP 客户端 — stocksApi/watchlistApi/signalsApi/strategiesApi 四组API方法
│   │   │   ├── websocket.ts   # ★ WebSocket管理器 — 自动重连(指数退避)+心跳(30s)+消息分发(on/off)+subscribe/unsubscribe/requestHist
│   │   │   ├── chartConfig.ts # ★ ECharts配置构建器 — buildKlineOption四面板布局+MA线叠加+RSI超买超卖线+KDJ三线+dataZoom联动缩放+tooltip格式化+PERIOD_OPTIONS常量
│   │   │
│   │   ├── stores/            # Pinia 状态管理
│   │   │   ├── stockStore.ts  # ★ 股票Store — currentStock/currentCode/currentPeriod/realtimeQuotes(Map)/loadStock/updateQuotes/getQuote/clear
│   │   │   ├── watchlistStore.ts # ★ 自选股Store — items/load/add/remove/getStockCodes(供WS订阅)
│   │   │   ├── signalStore.ts # ★ 信号Store — signals/unreadCount/load/addSignal(来自WS)/markRead/getByStock
│   │   │   ├── wsStore.ts     # ★ WS连接状态Store — connected/reconnecting/lastMessageTime/setConnected/setReconnecting/updateLastMessage
│   │   │   ├── counter.ts     # 脚手架残留
│   │   │
│   │   ├── types/
│   │   │   ├── stock.ts       # ★ TypeScript类型定义 — KlinePoint/IndicatorData/StockFullResponse/RealtimeQuote/StockSearchResult/WatchlistItem/WatchlistAdd/SignalItem/StrategyItem/WSMessage 全部数据结构
│   │   │
│   │   ├── utils/
│   │   │   ├── colorUtils.ts  # ★ 颜色工具 — STOCK_COLORS(红涨绿跌)/INDICATOR_COLORS/getStockColor/getVolumeColor/formatChange/formatPrice/formatVolume
│   │   │
│   │   ├── assets/            # CSS + SVG 资源（main.css/base.css/logo.svg）
│
│   ├── public/                 # 静态资源（favicon.ico）
│   ├── .vscode/                # VSCode 工作区配置
│   ├── .editorconfig           # 编辑器统一配置
│   ├── .gitattributes          # Git 属性配置
│   ├── .gitignore              # 前端专用 Git 忽略
│   ├── .prettierrc.json        # Prettier 格式化配置
│   ├── .oxlintrc.json          # OxLint 配置
│   ├── eslint.config.ts        # ESLint 配置
│   ├── vitest.config.ts        # Vitest 单元测试配置
│   ├── tsconfig.json           # TypeScript 主配置
│   ├── tsconfig.app.json       # App TypeScript 配置
│   ├── tsconfig.node.json      # Node TypeScript 配置
│   ├── tsconfig.vitest.json    # Vitest TypeScript 配置
```

## 数据库表结构

| 表 | 用途 | 关键字段 |
|---|---|---|
| `watchlist` | 自选股列表 | stock_code(唯一), stock_name, market, is_active(软删除), notes |
| `strategies` | 策略配置 | name(唯一), config_yaml, is_active |
| `signals` | 买卖信号 | stock_code, strategy_id(外键→strategies), signal_type(BUY/SELL), confidence, indicator_values(JSON), is_read |
| `kline_cache` | K线缓存 | stock_code+period+date(联合主键), open/close/high/low/volume/amount/turnover |

数据库采用 **WAL 模式** 提升并发读写性能，建表在 `init_db()` 中自动执行。

## API 接口清单

### REST API

| 路径 | 方法 | 说明 | 关键参数 |
|---|---|---|---|
| `/api/stocks/search` | GET | 搜索股票 | keyword(必填) |
| `/api/stocks/{code}/hist` | GET | 历史 K 线 | period, start_date, end_date, adjust |
| `/api/stocks/{code}/full` | GET | ★ 完整数据(K线+指标+信号) | period, start_date, end_date, adjust |
| `/api/stocks/{code}/quote` | GET | 实时行情 | - |
| `/api/stocks/{code}/intraday` | GET | 分钟级 K 线 | period(1/5/15/30/60) |
| `/api/watchlist` | GET | 自选股列表 | - |
| `/api/watchlist` | POST | 添加自选股 | stock_code, stock_name, market, notes |
| `/api/watchlist/{id}` | DELETE | 移除(软删除) | - |
| `/api/watchlist/{id}` | PATCH | 更新备注/状态 | notes, is_active |
| `/api/signals` | GET | 信号列表 | stock_code, signal_type, strategy_id, unread_only, limit, offset |
| `/api/signals/{id}` | GET | 信号详情 | - |
| `/api/signals/{id}/read` | PATCH | 标记已读 | - |
| `/api/strategies` | GET | 策略列表 | - |
| `/api/strategies/{id}` | GET | 策略详情 | - |
| `/api/strategies` | POST | 创建策略 | name, description, config_yaml |
| `/api/strategies/{id}` | PATCH | 更新策略 | description, config_yaml, is_active |
| `/api/strategies/{id}` | DELETE | 删除策略 | - |

### WebSocket (`/ws`)

| 消息类型 | 方向 | 说明 |
|---|---|---|
| `subscribe` | 客户端→服务端 | 订阅股票代码列表 |
| `unsubscribe` | 客户端→服务端 | 取消订阅 |
| `request_hist` | 客户端→服务端 | 请求历史 K 线数据 |
| `ping` | 客户端→服务端 | 心跳 |
| `pong` | 服务端→客户端 | 心跳回复 |
| `quote_update` | 服务端→客户端 | 实时行情推送(15秒周期) |
| `signal_alert` | 服务端→客户端 | 买卖信号推送 |
| `hist_data` | 服务端→客户端 | 历史数据回复 |

## 策略系统

### 四种条件类型

| 类型 | 说明 | YAML 示例参数 |
|---|---|---|
| `threshold` | 指标值高于/低于阈值 | `indicator: rsi, value: 30, direction: below` |
| `cross` | 指标交叉（金叉/死叉） | `indicator: kdj_k, ref_indicator: kdj_d, direction: up, lookback: 2` |
| `price_vs_ma` | 价格 vs MA 均线 | `ma_period: 20, direction: above` |
| `volume_confirm` | 成交量确认 | `ratio: 1.5, avg_days: 5` |

### 预设策略

| 策略 | 信号类型 | 条件 |
|---|---|---|
| RSI超卖反弹 | BUY | RSI < 30 |
| RSI超买卖出 | SELL | RSI > 70 |
| KDJ金叉买入 | BUY | K 上穿 D + J > 0 |
| KDJ死叉卖出 | SELL | K 下穿 D + J < 100 |
| MA20突破买入 | BUY | 价格 > MA20 + 成交量 > 1.5倍均量 |
| 多指标共振买入 | BUY | RSI < 35 + KDJ金叉 + 价格 > MA20 |

策略文件使用 `---` 分隔符支持多策略（YAML multi-document）。

## 关键设计决策

1. **数据源抽象**：`DataSourceInterface` 接口隔离 AKShare 具体实现，方便未来添加港美股数据源
2. **异步架构**：后端全异步（async/await + aiosqlite），AKShare 同步调用用 `asyncio.to_thread()` 包装
3. **行情缓存+限速**：AKShareSource 内部 `_spot_cache` 缓存全市场行情，配合 `_realtime_lock` 限速避免反爬
4. **软删除**：自选股使用 `is_active` 字段软删除，删除后可重新激活
5. **四面板联动**：ECharts dataZoom + axisPointer 联动 4 个 grid，实现缩放同步
6. **中国股市配色**：红涨绿跌（STOCK_COLORS.up=#ef232a, down=#14b143）
7. **自动重连**：WebSocket 前端指数退避重连（3s × 1.5^n，最多10次）
8. **策略热加载**：策略引擎启动时从 YAML 文件加载预设，也可通过 API 动态创建

## 运行方式

```bash
# 安装依赖
cd backend && pip install -r requirements.txt
cd frontend && npm install

# 启动后端
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端
cd frontend && npm run dev

# 或 Windows 一键脚本
scripts/setup.bat  # 安装
scripts/start.bat  # 启动
```

访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 注意事项

- `frontend/src/components/HelloWorld.vue`、`TheWelcome.vue`、`WelcomeItem.vue`、`icons/`、`AboutView.vue`、`stores/counter.ts` 为 Vue CLI 脚手架残留，不影响功能
- `indicator_values` 字段在数据库中存为 JSON 字符串，读取时用 `eval()` 解析（后端 signals.py/stocks.py），有潜在安全风险，建议改用 `json.loads()`
- AKShare 是同步库，所有调用必须通过 `asyncio.to_thread()` 包装
- `data/` 目录运行时自动创建，存放 SQLite 数据库文件
- 前端 `api.ts` 中 baseURL 硬编码为 `http://localhost:8000/api`，生产部署需修改
- WebSocket URL 硬编码为 `ws://localhost:8000/ws`，生产部署需修改

## 扩展计划（来自 README）

- 港美股支持（通过 DataSourceInterface 抽象层添加新数据源）
- 微信/邮件推送通知
- 更多技术指标（MACD、布林带等）
- 策略回测功能