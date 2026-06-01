"""微信推送配置 API"""
from fastapi import APIRouter

from app.config import settings
from app.services.wechat_notify import send_wechat_test

router = APIRouter()


@router.get("/status")
async def wechat_status():
    """查看微信推送配置状态"""
    return {
        "configured": bool(settings.wechat_webhook_url),
        "webhook_url_set": bool(settings.wechat_webhook_url),
    }


@router.post("/test")
async def wechat_test():
    """发送测试消息验证 Webhook 配置"""
    success, message = await send_wechat_test()
    return {"success": success, "message": message}