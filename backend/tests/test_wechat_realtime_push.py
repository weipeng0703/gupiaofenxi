"""实时推送测试 — 获取真实行情数据，生成分析报告并通过微信推送

直接运行即可发送分析报告到企业微信群：
    cd backend
    python -m tests.test_wechat_realtime_push

可选参数：
    --code 000001       指定单只股票
    --all               推送全部自选股分析
"""
import asyncio
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from curl_cffi import requests as curl_requests

from app.config import settings
from app.services.akshare_source import AKShareSource
from app.services.indicator_calc import IndicatorCalculator
from app.services.strategy_engine import StrategyEngine


def build_analysis_message(stock_code: str, kline: list, indicators: dict, signals: list, quote: dict | None = None) -> str:
    """根据指标和策略结果构建分析报告"""
    latest = kline[-1]
    price = latest["close"]
    prev_close = kline[-2]["close"] if len(kline) >= 2 else price
    change_pct = (price - prev_close) / prev_close * 100

    # 指标值
    rsi14 = indicators["rsi"]["RSI14"][-1] if indicators["rsi"]["RSI14"] else None
    rsi6 = indicators["rsi"]["RSI6"][-1] if indicators["rsi"]["RSI6"] else None
    kdj_k = indicators["kdj"]["K"][-1] if indicators["kdj"]["K"] else None
    kdj_d = indicators["kdj"]["D"][-1] if indicators["kdj"]["D"] else None
    kdj_j = indicators["kdj"]["J"][-1] if indicators["kdj"]["J"] else None
    ma5 = indicators["ma"]["MA5"][-1] if indicators["ma"]["MA5"] else None
    ma10 = indicators["ma"]["MA10"][-1] if indicators["ma"]["MA10"] else None
    ma20 = indicators["ma"]["MA20"][-1] if indicators["ma"]["MA20"] else None
    ma60 = indicators["ma"]["MA60"][-1] if indicators["ma"]["MA60"] else None

    # 涨跌标识
    trend_emoji = "📈" if change_pct >= 0 else "📉"
    change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

    # 综合评估
    recommendation = _generate_recommendation(price, rsi14, rsi6, kdj_k, kdj_d, kdj_j, ma5, ma10, ma20, ma60, signals)

    # 构建消息
    lines = [
        f"{trend_emoji} 【{stock_code}】实时分析报告",
        f"{'═' * 28}",
        f"",
        f"📊 行情数据",
        f"  收盘价：{price:.2f}  ({change_str})",
        f"  最高：{latest['high']:.2f}  最低：{latest['low']:.2f}",
        f"  成交量：{latest['volume'] / 10000:.0f}万手",
        f"",
        f"📐 技术指标",
        f"  RSI(6): {rsi6:.2f}" + (_rsi_label(rsi6)) if rsi6 else "",
        f"  RSI(14): {rsi14:.2f}" + (_rsi_label(rsi14)) if rsi14 else "",
        f"  KDJ: K={kdj_k:.2f} D={kdj_d:.2f} J={kdj_j:.2f}" if kdj_k else "",
        f"  MA5={ma5:.2f} MA10={ma10:.2f} MA20={ma20:.2f}" if ma5 else "",
    ]

    # MA 多空排列判断
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            lines.append(f"  均线：多头排列 ↑")
        elif ma5 < ma10 < ma20:
            lines.append(f"  均线：空头排列 ↓")
        else:
            lines.append(f"  均线：交叉整理 ↔")

    lines.append(f"")

    # 策略信号
    if signals:
        lines.append(f"🚨 策略触发信号")
        for s in signals:
            sig_icon = "🟢 买入" if s["signal_type"] == "BUY" else "🔴 卖出"
            lines.append(f"  {sig_icon} | {s['strategy_name']} | 置信度 {s['confidence'] * 100:.0f}%")
        lines.append(f"")

    # 综合建议
    lines.append(f"{'═' * 28}")
    lines.append(f"💡 综合建议：{recommendation}")
    lines.append(f"{'═' * 28}")
    lines.append(f"⏰ 数据日期：{latest['date']}")

    return "\n".join([l for l in lines if l is not None])


def _rsi_label(rsi: float) -> str:
    if rsi >= 80:
        return "  ⚠️极度超买"
    elif rsi >= 70:
        return "  ⚠️超买区"
    elif rsi <= 20:
        return "  🔥极度超卖"
    elif rsi <= 30:
        return "  🔥超卖区"
    elif rsi <= 40:
        return "  偏弱"
    elif rsi >= 60:
        return "  偏强"
    return "  中性"


def _generate_recommendation(price, rsi14, rsi6, kdj_k, kdj_d, kdj_j, ma5, ma10, ma20, ma60, signals) -> str:
    """综合多指标生成买卖建议"""
    buy_score = 0
    sell_score = 0
    reasons = []

    # RSI 判断
    if rsi14 is not None:
        if rsi14 < 30:
            buy_score += 2
            reasons.append("RSI超卖")
        elif rsi14 < 40:
            buy_score += 1
            reasons.append("RSI偏低")
        elif rsi14 > 70:
            sell_score += 2
            reasons.append("RSI超买")
        elif rsi14 > 60:
            sell_score += 1
            reasons.append("RSI偏高")

    # KDJ 判断
    if kdj_k is not None and kdj_d is not None:
        if kdj_j is not None and kdj_j < 0:
            buy_score += 1
            reasons.append("KDJ-J值超卖")
        elif kdj_j is not None and kdj_j > 100:
            sell_score += 1
            reasons.append("KDJ-J值超买")
        if kdj_k > kdj_d:
            buy_score += 1
            reasons.append("KDJ金叉形态")
        else:
            sell_score += 1
            reasons.append("KDJ死叉形态")

    # 均线判断
    if price and ma20:
        if price > ma20:
            buy_score += 1
            reasons.append("站上MA20")
        else:
            sell_score += 1
            reasons.append("跌破MA20")

    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            buy_score += 1
            reasons.append("多头排列")
        elif ma5 < ma10 < ma20:
            sell_score += 1
            reasons.append("空头排列")

    # 策略信号
    for s in signals:
        if s["signal_type"] == "BUY":
            buy_score += 2
        else:
            sell_score += 2

    # 生成建议
    reason_str = "、".join(reasons[:4])
    if buy_score >= 4 and buy_score > sell_score + 2:
        return f"强烈建议关注买入 ({reason_str})"
    elif buy_score > sell_score + 1:
        return f"偏多，可考虑逢低布局 ({reason_str})"
    elif sell_score >= 4 and sell_score > buy_score + 2:
        return f"建议减仓或离场 ({reason_str})"
    elif sell_score > buy_score + 1:
        return f"偏空，注意风险控制 ({reason_str})"
    else:
        return f"震荡观望，暂不操作 ({reason_str})"


async def push_stock_analysis(stock_code: str, ds: AKShareSource, engine: StrategyEngine) -> bool:
    """对单只股票执行完整分析并推送微信"""
    webhook_url = settings.wechat_webhook_url
    if not webhook_url:
        print(f"[错误] 未配置 WECHAT_WEBHOOK_URL")
        return False

    print(f"\n{'─' * 40}")
    print(f"分析 {stock_code} ...")

    raw_kline = await ds.get_hist_kline(stock_code, period="daily")
    if not raw_kline:
        print(f"  [失败] 无法获取K线数据")
        return False

    df = pd.DataFrame(raw_kline)
    df = df.sort_values("date").reset_index(drop=True)
    indicators = IndicatorCalculator.compute_all(df)

    signals = engine.evaluate(stock_code, indicators, raw_kline)

    message = build_analysis_message(stock_code, raw_kline, indicators, signals)

    print(f"  RSI14={indicators['rsi']['RSI14'][-1]:.2f}, "
          f"KDJ=({indicators['kdj']['K'][-1]:.2f},{indicators['kdj']['D'][-1]:.2f},{indicators['kdj']['J'][-1]:.2f})")
    print(f"  信号数: {len(signals)}")

    # 推送到微信
    payload = {"msgtype": "text", "text": {"content": message}}
    try:
        resp = curl_requests.post(webhook_url, json=payload, timeout=10, impersonate="chrome")
        if resp.status_code == 200 and resp.json().get("errcode") == 0:
            print(f"  ✅ 微信推送成功")
            return True
        else:
            print(f"  ❌ 推送失败: {resp.text}")
            return False
    except Exception as e:
        print(f"  ❌ 推送异常: {e}")
        return False


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="实时分析推送测试")
    parser.add_argument("--code", type=str, help="指定股票代码")
    parser.add_argument("--all", action="store_true", help="推送全部自选股")
    args = parser.parse_args()

    ds = AKShareSource()
    engine = StrategyEngine()

    print(f"已加载策略: {list(engine._strategies.keys())}")
    print(f"Webhook: {settings.wechat_webhook_url[:50]}...")

    if args.code:
        codes = [args.code]
    elif args.all:
        from app.database import async_session
        from sqlalchemy import text
        async with async_session() as session:
            result = await session.execute(text("SELECT stock_code FROM watchlist WHERE is_active = 1"))
            codes = [row[0] for row in result.fetchall()]
        print(f"自选股列表: {len(codes)} 只")
    else:
        # 默认测试：选几只有代表性的
        codes = ["000001", "600036", "159995"]
        print(f"默认测试: {codes}")

    success_count = 0
    for code in codes:
        ok = await push_stock_analysis(code, ds, engine)
        if ok:
            success_count += 1
        await asyncio.sleep(1)  # 避免请求过快

    print(f"\n{'═' * 40}")
    print(f"完成: {success_count}/{len(codes)} 只推送成功")


if __name__ == "__main__":
    asyncio.run(main())
