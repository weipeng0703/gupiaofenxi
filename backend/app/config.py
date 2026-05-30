"""应用配置 — 使用 Pydantic BaseSettings 管理"""
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    db_path: str = "data/gupiaofenxi.db"

    # AKShare 数据源
    akshare_refresh_interval: int = 15          # 实时行情刷新间隔（秒）
    akshare_hist_cache_hours: int = 4           # 历史 K 线缓存过期时间（小时）

    # 策略
    strategy_dir: str = "backend/app/strategies"

    # WebSocket
    ws_heartbeat_interval: int = 30             # WebSocket 心跳间隔（秒）

    # 技术指标默认参数
    default_rsi_period: int = 14
    default_kdj_period: int = 9
    default_kdj_smooth: int = 3
    ma_periods: list[int] = [5, 10, 20, 60]    # 默认显示的 MA 均线周期

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000
    # CORS — 支持环境变量传入（逗号分隔字符串），默认本地开发
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """支持逗号分隔的字符串格式（从环境变量传入）"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def get_abs_db_path(self) -> str:
        """将相对路径转换为绝对路径"""
        if not os.path.isabs(self.db_path):
            # 项目根目录：backend/app 的父级的父级
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(base, self.db_path)
        return self.db_path


settings = Settings()