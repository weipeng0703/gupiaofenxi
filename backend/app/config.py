"""应用配置 — 使用 Pydantic BaseSettings 管理"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    db_path: str = "data/gupiaofenxi.db"

    # AKShare 数据源
    akshare_refresh_interval: int = 15          # 实时行情刷新间隔（秒）
    akshare_hist_cache_hours: int = 4           # 历史 K 线缓存过期时间（小时）

    # 策略
    strategy_dir: str = "app/strategies"

    # WebSocket
    ws_heartbeat_interval: int = 30             # WebSocket 心跳间隔（秒）

    # 技术指标默认参数
    rsi_periods: list[int] = [6, 12, 14, 24]     # RSI 多周期（含 RSI14 供策略引擎使用）
    default_rsi_period: int = 14                # RSI 默认周期（策略引擎引用）
    default_kdj_period: int = 9
    default_kdj_smooth: int = 3
    ma_periods: list[int] = [5, 10, 20, 60]    # 默认显示的 MA 均线周期

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # 微信推送 — 企业微信机器人 Webhook URL（留空则不推送）
    wechat_webhook_url: str = ""

    # CORS — 存为字符串（逗号分隔），环境变量可直接传入，不会报解析错误
    cors_origins: str = "http://localhost:5173,http://localhost:8000,https://gupiaofenxi-bmep.vercel.app,https://paving-regular-wifi.ngrok-free.dev"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def get_cors_origins_list(self) -> list[str]:
        """将逗号分隔的 CORS 字符串转换为列表"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def get_abs_db_path(self) -> str:
        """将相对路径转换为绝对路径"""
        if not os.path.isabs(self.db_path):
            # 项目根目录：backend/app 的父级的父级
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(base, self.db_path)
        return self.db_path


settings = Settings()