"""策略评估引擎 — 读取 YAML 配置，逐条评估条件，生成买卖信号"""
import os
import yaml
import logging
from datetime import datetime

from app.config import settings
from app.models import Signal, Strategy

logger = logging.getLogger(__name__)


class StrategyConfig:
    """策略配置对象"""

    def __init__(self, name: str, description: str, signal_type: str,
                 conditions: list, confidence_weights: list = None,
                 is_active: bool = True):
        self.name = name
        self.description = description
        self.signal_type = signal_type
        self.conditions = conditions
        self.confidence_weights = confidence_weights or []
        self.is_active = is_active


class StrategyEngine:
    """策略评估引擎

    读取 YAML 策略配置，对传入的指标数据逐条评估条件，
    所有条件满足则生成信号。
    """

    def __init__(self):
        self._strategies: dict[str, StrategyConfig] = {}
        self._load_presets()

    def _load_presets(self):
        """从 YAML 文件加载预设策略"""
        strategy_dir = settings.strategy_dir
        # 获取项目根目录的绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        abs_dir = os.path.join(base_dir, strategy_dir) if not os.path.isabs(strategy_dir) else strategy_dir

        if not os.path.exists(abs_dir):
            logger.warning(f"策略目录不存在: {abs_dir}")
            return

        for filename in os.listdir(abs_dir):
            if not filename.endswith(".yaml") and not filename.endswith(".yml"):
                continue
            filepath = os.path.join(abs_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    docs = yaml.safe_load_all(f)
                    for doc in docs:
                        if doc and "name" in doc:
                            config = StrategyConfig(
                                name=doc["name"],
                                description=doc.get("description", ""),
                                signal_type=doc.get("signal_type", "BUY"),
                                conditions=doc.get("conditions", []),
                                confidence_weights=doc.get("confidence_weights", []),
                            )
                            self._strategies[config.name] = config
                            logger.info(f"加载策略: {config.name}")
            except Exception as e:
                logger.warning(f"加载策略文件 {filename} 失败: {e}")

    def add_strategy(self, config: StrategyConfig):
        """动态添加策略"""
        self._strategies[config.name] = config

    def evaluate(self, stock_code: str, indicators: dict,
                 kline: list, strategy_id_map: dict = None) -> list[dict]:
        """对所有活跃策略评估，返回匹配的信号列表

        Args:
            stock_code: 股票代码
            indicators: IndicatorData 格式的指标字典
            kline: K 线数据列表
            strategy_id_map: 策略名称→数据库ID 的映射（用于创建 Signal 记录）

        Returns:
            list[dict]: 信号列表，每条包含 stock_code, strategy_name, signal_type, confidence 等
        """
        results = []
        for name, config in self._strategies.items():
            if not config.is_active:
                continue
            signal = self._evaluate_strategy(stock_code, name, config, indicators, kline)
            if signal:
                # 添加 strategy_id（如果有映射）
                if strategy_id_map and name in strategy_id_map:
                    signal["strategy_id"] = strategy_id_map[name]
                results.append(signal)
        return results

    def _evaluate_strategy(self, stock_code: str, name: str, config: StrategyConfig,
                           indicators: dict, kline: list) -> dict | None:
        """评估单个策略"""
        conditions_met = []
        for cond in config.conditions:
            result = self._check_condition(cond, indicators, kline)
            conditions_met.append(result)

        if all(conditions_met):
            confidence = self._compute_confidence(config.confidence_weights, indicators)
            # 获取当前价格
            current_price = kline[-1].get("close", 0) if kline else 0
            timestamp = kline[-1].get("date", datetime.now().strftime("%Y-%m-%d")) if kline else ""

            # 指标值快照
            indicator_snapshot = {}
            rsi_dict = indicators.get("rsi", {})
            kdj = indicators.get("kdj", {})
            ma = indicators.get("ma", {})
            # 策略引擎默认引用 RSI14（default_rsi_period）
            rsi14 = rsi_dict.get("RSI14", [])
            if rsi14 and rsi14[-1] is not None:
                indicator_snapshot["rsi"] = rsi14[-1]
            # 也快照 RSI6/12/24 供扩展使用
            for p in [6, 12, 24]:
                rsi_p = rsi_dict.get(f"RSI{p}", [])
                if rsi_p and rsi_p[-1] is not None:
                    indicator_snapshot[f"rsi{p}"] = rsi_p[-1]
            if kdj.get("K") and kdj["K"][-1] is not None:
                indicator_snapshot["kdj_k"] = kdj["K"][-1]
                indicator_snapshot["kdj_d"] = kdj["D"][-1] if kdj.get("D") else None
                indicator_snapshot["kdj_j"] = kdj["J"][-1] if kdj.get("J") else None

            return {
                "stock_code": stock_code,
                "strategy_name": name,
                "signal_type": config.signal_type,
                "confidence": confidence,
                "indicator_values": indicator_snapshot,
                "price": current_price,
                "timestamp": timestamp,
            }
        return None

    def _check_condition(self, cond: dict, indicators: dict, kline: list) -> bool:
        """检查单个条件"""
        cond_type = cond.get("type")
        params = cond.get("params", {})

        try:
            if cond_type == "threshold":
                return self._check_threshold(cond, indicators)
            elif cond_type == "cross":
                return self._check_cross(cond, indicators)
            elif cond_type == "price_vs_ma":
                return self._check_price_vs_ma(cond, indicators, kline)
            elif cond_type == "volume_confirm":
                return self._check_volume_confirm(cond, kline)
            else:
                logger.warning(f"未知条件类型: {cond_type}")
                return False
        except Exception as e:
            logger.debug(f"条件检查异常: {e}")
            return False

    def _check_threshold(self, cond: dict, indicators: dict) -> bool:
        """阈值条件：指标值高于/低于某个数值"""
        indicator_name = cond.get("indicator")
        params = cond.get("params", {})
        value = params.get("value", 0)
        direction = params.get("direction", "below")

        # 获取最新指标值
        current_val = self._get_latest_indicator_value(indicator_name, indicators)
        if current_val is None:
            return False

        if direction == "below":
            return current_val < value
        elif direction == "above":
            return current_val > value
        return False

    def _check_cross(self, cond: dict, indicators: dict) -> bool:
        """交叉条件：一个指标穿越另一个指标（金叉/死叉）"""
        indicator = cond.get("indicator")
        ref_indicator = cond.get("ref_indicator")
        params = cond.get("params", {})
        direction = params.get("direction", "up")
        lookback = params.get("lookback", 2)

        series_a = self._get_indicator_series(indicator, indicators)
        series_b = self._get_indicator_series(ref_indicator, indicators)

        if not series_a or not series_b:
            return False

        # 检查最近 lookback 个周期内是否发生了交叉
        for i in range(len(series_a) - lookback, len(series_a)):
            if i < 1:
                continue
            prev_a = series_a[i - 1]
            prev_b = series_b[i - 1]
            curr_a = series_a[i]
            curr_b = series_b[i]

            if any(v is None for v in [prev_a, prev_b, curr_a, curr_b]):
                continue

            if direction == "up" and prev_a <= prev_b and curr_a > curr_b:
                return True
            if direction == "down" and prev_a >= prev_b and curr_a < curr_b:
                return True

        return False

    def _check_price_vs_ma(self, cond: dict, indicators: dict, kline: list) -> bool:
        """价格 vs MA 条件"""
        ma_period = cond.get("ma_period", 20)
        params = cond.get("params", {})
        direction = params.get("direction", "above")

        ma_key = f"MA{ma_period}"
        ma_series = indicators.get("ma", {}).get(ma_key, [])

        if not ma_series or not kline:
            return False

        current_price = kline[-1].get("close", 0)
        current_ma = ma_series[-1]

        if current_ma is None:
            return False

        if direction == "above":
            return current_price > current_ma
        elif direction == "below":
            return current_price < current_ma
        return False

    def _check_volume_confirm(self, cond: dict, kline: list) -> bool:
        """成交量确认条件：当前成交量 > N倍均量"""
        params = cond.get("params", {})
        ratio = params.get("ratio", 1.5)
        avg_days = params.get("avg_days", 5)

        if len(kline) < avg_days + 1:
            return False

        volumes = [k.get("volume", 0) for k in kline[-avg_days - 1:]]
        avg_volume = sum(volumes[:-1]) / avg_days
        current_volume = volumes[-1]

        return current_volume > avg_volume * ratio

    def _get_latest_indicator_value(self, indicator_name: str, indicators: dict) -> float | None:
        """获取指标的最新值"""
        if indicator_name == "rsi":
            # 默认取 RSI14（策略 YAML 中 rsi 指标指 RSI14）
            rsi_dict = indicators.get("rsi", {})
            rsi14 = rsi_dict.get("RSI14", [])
            return rsi14[-1] if rsi14 else None
        elif indicator_name.startswith("rsi") and indicator_name not in ("rsi"):
            # 支持 rsi6 / rsi12 / rsi24 等精确周期
            rsi_dict = indicators.get("rsi", {})
            key = indicator_name.upper().replace("RSI", "RSI")
            series = rsi_dict.get(key, [])
            return series[-1] if series else None
        elif indicator_name.startswith("kdj_"):
            kdj_key = indicator_name.replace("kdj_", "").upper()
            kdj = indicators.get("kdj", {})
            series = kdj.get(kdj_key, [])
            return series[-1] if series else None
        return None

    def _get_indicator_series(self, indicator_name: str, indicators: dict) -> list:
        """获取指标的完整序列"""
        if indicator_name == "rsi":
            rsi_dict = indicators.get("rsi", {})
            rsi14 = rsi_dict.get("RSI14", [])
            return rsi14 if rsi14 else []
        elif indicator_name.startswith("rsi") and indicator_name not in ("rsi"):
            rsi_dict = indicators.get("rsi", {})
            series = rsi_dict.get(indicator_name.upper(), [])
            return series if series else []
        elif indicator_name.startswith("kdj_"):
            kdj_key = indicator_name.replace("kdj_", "").upper()
            kdj = indicators.get("kdj", {})
            return kdj.get(kdj_key, [])
        elif indicator_name.startswith("MA"):
            ma = indicators.get("ma", {})
            return ma.get(indicator_name, [])
        return []

    def _compute_confidence(self, weights: list, indicators: dict) -> float:
        """根据权重计算置信度"""
        if not weights:
            return 0.5  # 默认置信度

        total = 0.0
        for w in weights:
            indicator = w.get("indicator")
            weight = w.get("weight", 0.5)
            val = self._get_latest_indicator_value(indicator, indicators)
            if val is not None:
                total += weight

        return min(total, 1.0)