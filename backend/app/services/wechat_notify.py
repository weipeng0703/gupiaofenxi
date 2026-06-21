"""微信推送服务 — 通过企业微信机器人 Webhook 推送信号通知

使用项目已有的 curl_cffi 发送 HTTP 请求，无需额外依赖。
"""
import asyncio
import logging
from datetime import datetime, timedelta

from curl_cffi import requests as curl_requests

from app.config import settings

logger = logging.getLogger(__name__)

# 信号去重：记录最近推送过的信号，避免重复推送
_recent_signals: dict[str, datetime] = {}  # key: "stock_code:strategy_name", value: datetime对象
_DEDUP_INTERVAL_SECONDS = 600  # 同一信号 10 分钟内不重复推送


async def send_wechat_signal(signal: dict) -> bool:
    """通过企业微信机器人推送信号通知

    Args:
        signal: 信号字典，包含 stock_code, strategy_name, signal_type, confidence, price, timestamp 等

    Returns:
        bool: 是否推送成功
    """
    webhook_url = settings.wechat_webhook_url
    if not webhook_url:
        return False

    # 去重检查 — 基于10分钟过期时间
    dedup_key = f"{signal.get('stock_code', '')}:{signal.get('strategy_name', '')}"
    now = datetime.now()
    last_sent = _recent_signals.get(dedup_key)
    if last_sent and (now - last_sent) < timedelta(seconds=_DEDUP_INTERVAL_SECONDS):
        logger.debug(f"微信推送去重跳过: {dedup_key}, 上次推送 {last_sent}")
        return False

    # 构建消息
    signal_type = signal.get("signal_type", "BUY")
    stock_code = signal.get("stock_code", "")
    stock_name = signal.get("stock_name", "")
    strategy_name = signal.get("strategy_name", "")
    confidence = signal.get("confidence", 0)
    price = signal.get("price", 0)
    timestamp = signal.get("timestamp", "")
    indicator_values = signal.get("indicator_values", {})

    # 信号类型中文映射
    type_label = "🔴 高抛" if signal_type == "SELL" else "🟢 低吸"
    type_emoji = "📉" if signal_type == "SELL" else "📈"

    # 构建指标快照文本
    indicator_lines = []
    if indicator_values:
        for k, v in indicator_values.items():
            if v is not None:
                if isinstance(v, float):
                    indicator_lines.append(f"  {k}: {v:.2f}")
                else:
                    indicator_lines.append(f"  {k}: {v}")

    indicator_text = "\n".join(indicator_lines) if indicator_lines else "  无"

    content = (
        f"{type_emoji} 交易信号提醒\n\n"
        f"信号类型：{type_label}\n"
        f"股票：{stock_name}（{stock_code}）\n"
        f"策略名称：{strategy_name}\n"
        f"当前价格：{price:.2f}\n"
        f"置信度：{confidence * 100:.0f}%\n"
        f"触发时间：{timestamp}\n"
        f"\n指标快照：\n{indicator_text}"
    )

    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
        },
    }

    try:
        # 用 asyncio.to_thread 包装同步的 curl_cffi 调用
        def _post():
            return curl_requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                impersonate="chrome",
            )

        resp = await asyncio.to_thread(_post)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("errcode") == 0:
                _recent_signals[dedup_key] = now
                logger.info(f"微信推送成功: {stock_code} {strategy_name} {signal_type}")
                return True
            else:
                logger.warning(f"微信推送失败: {result}")
        else:
            logger.warning(f"微信推送 HTTP 错误: {resp.status_code}")
    except Exception as e:
        logger.warning(f"微信推送异常: {e}")

    return False


async def send_wechat_test() -> tuple[bool, str]:
    """发送测试消息，验证 Webhook 是否配置正确

    Returns:
        tuple[bool, str]: (是否成功, 结果消息)
    """
    webhook_url = settings.wechat_webhook_url
    if not webhook_url:
        return False, "未配置企业微信 Webhook URL"

    payload = {
        "msgtype": "text",
        "text": {
            "content": "✅ 股票分析助手 — 微信推送测试成功！\n\n配置正确，后续交易信号将自动推送到此群。",
        },
    }

    try:
        def _post():
            return curl_requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                impersonate="chrome",
            )

        resp = await asyncio.to_thread(_post)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("errcode") == 0:
                return True, "测试消息发送成功！请检查企业微信群是否收到。"
            else:
                errmsg = result.get("errmsg", "未知错误")
                return False, f"企业微信返回错误: {errmsg}"
        else:
            return False, f"HTTP 请求失败，状态码: {resp.status_code}"
    except Exception as e:
        return False, f"推送异常: {e}"