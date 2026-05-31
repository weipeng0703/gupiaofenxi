<template>
  <div class="rules-page">
    <header class="rules-header">
      <h1>📚 交易规则手册</h1>
      <p class="rules-desc">记录消息通知提示的触发规则，供参考与回测使用</p>
    </header>

    <div class="rules-sections">
      <!-- ── RSI 规则 ── -->
      <section class="rule-section">
        <div class="section-title">
          <span class="section-icon">📈</span>
          <h2>RSI 指标规则</h2>
          <span class="section-badge active">已启用</span>
        </div>

        <!-- 规则 1: 超买超卖 -->
        <div class="rule-card">
          <div class="rule-header">
            <span class="rule-number">1</span>
            <h3>超买超卖阈值</h3>
            <span class="rule-status on">通知提醒</span>
          </div>
          <div class="rule-body">
            <div class="rule-condition sell">
              <div class="condition-label">高抛信号</div>
              <div class="condition-detail">
                RSI ≥ <strong>80</strong> → 买方过多，进入<strong>超买区</strong>，股价到顶风险大，应<strong>高抛</strong>
              </div>
            </div>
            <div class="rule-condition buy">
              <div class="condition-label">低吸信号</div>
              <div class="condition-detail">
                RSI ≤ <strong>20</strong> → 卖方过多，进入<strong>超卖区</strong>，股价到底概率高，应<strong>低吸</strong>
              </div>
            </div>
          </div>
          <div class="rule-note">
            💡 适用场景：所有趋势环境均可作为辅助参考
          </div>
        </div>

        <!-- 规则 2: 顶底背离 -->
        <div class="rule-card">
          <div class="rule-header">
            <span class="rule-number">2</span>
            <h3>顶底背离</h3>
            <span class="rule-status pending">待开发</span>
          </div>
          <div class="rule-body">
            <div class="rule-condition sell">
              <div class="condition-label">顶背离 → 高抛</div>
              <div class="condition-detail">
                价格<strong>越来越高</strong>，RSI 在顶部却<strong>越来越低</strong> → 卖方力量增强，趋势即将反转，应<strong>高抛</strong>
              </div>
            </div>
            <div class="rule-condition buy">
              <div class="condition-label">底背离 → 低吸</div>
              <div class="condition-detail">
                价格<strong>越来越低</strong>，RSI 在底部却<strong>越来越高</strong> → 买方抄底增多，反弹即将到来，应<strong>低吸</strong>
              </div>
            </div>
          </div>
          <div class="rule-note">
            💡 适用场景：<strong>震荡期间</strong>用方法2最准确
          </div>
        </div>

        <!-- 规则 3: 钝化与趋势适配 -->
        <div class="rule-card">
          <div class="rule-header">
            <span class="rule-number">3</span>
            <h3>趋势环境适配</h3>
            <span class="rule-status info">参考指南</span>
          </div>
          <div class="rule-body">
            <div class="rule-condition sell">
              <div class="condition-label">上升趋势中</div>
              <div class="condition-detail">
                底背离<strong>一定准</strong>（低吸可信）<br/>
                顶背离容易<strong>钝化不准</strong>（高抛用<strong>方法1</strong>更稳）
              </div>
            </div>
            <div class="rule-condition buy">
              <div class="condition-label">下行趋势中</div>
              <div class="condition-detail">
                顶背离<strong>一定准</strong>（高抛可信）<br/>
                底背离容易<strong>钝化不准</strong>（低吸用<strong>方法1</strong>更稳）
              </div>
            </div>
            <div class="rule-condition neutral">
              <div class="condition-label">震荡趋势中</div>
              <div class="condition-detail">
                方法2（背离）最准确，方法1（阈值）作为辅助
              </div>
            </div>
          </div>
        </div>

        <!-- 规则 4: 金叉死叉 -->
        <div class="rule-card">
          <div class="rule-header">
            <span class="rule-number">4</span>
            <h3>RSI 金叉 / 死叉</h3>
            <span class="rule-status on">通知提醒</span>
          </div>
          <div class="rule-body">
            <div class="rule-condition sell">
              <div class="condition-label">死叉 → 高抛</div>
              <div class="condition-detail">
                RSI6<strong>黑线</strong>垂直下降途中，与 RSI12<strong>黄线</strong>、RSI24<strong>紫线</strong>形成交叉 → 短期动能急剧转弱，应<strong>高抛</strong>
              </div>
            </div>
            <div class="rule-condition buy">
              <div class="condition-label">金叉 → 低吸</div>
              <div class="condition-detail">
                RSI6<strong>黑线</strong>垂直上升途中，与 RSI12<strong>黄线</strong>、RSI24<strong>紫线</strong>形成交叉 → 短期动能急剧转强，适合<strong>低吸</strong>
              </div>
            </div>
          </div>
          <div class="rule-note">
            💡 图表中：<strong>黑线 = RSI6</strong>（快速）、<strong>黄线 = RSI12</strong>（中速）、<strong>紫线 = RSI24</strong>（慢速）
          </div>
        </div>
      </section>

      <!-- ── 颜色对照 ── -->
      <section class="rule-section">
        <div class="section-title">
          <span class="section-icon">🎨</span>
          <h2>图表颜色对照</h2>
        </div>
        <div class="color-reference">
          <div class="color-row">
            <span class="color-dot" style="background: #2d2d2d;"></span>
            <span class="color-label">RSI6（黑线）— 短周期快速线</span>
          </div>
          <div class="color-row">
            <span class="color-dot" style="background: #f59e0b;"></span>
            <span class="color-label">RSI12（黄线）— 中周期线</span>
          </div>
          <div class="color-row">
            <span class="color-dot" style="background: #8b5cf6;"></span>
            <span class="color-label">RSI24（紫线）— 长周期慢速线</span>
          </div>
          <div class="color-row">
            <span class="color-dot" style="background: #aaa; border: 1px dashed #666;"></span>
            <span class="color-label">虚线 — 超买线(80) / 中轴线(50) / 超卖线(20)</span>
          </div>
        </div>
      </section>
    </div>

    <div class="rules-footer">
      <RouterLink to="/" class="back-link">← 返回首页</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.rules-page {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-lg);
  height: calc(100vh - var(--header-height));
  overflow-y: auto;
  background: var(--bg-primary);
}

.rules-header {
  margin-bottom: var(--spacing-lg);
}

.rules-header h1 {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

.rules-desc {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  margin-top: var(--spacing-sm);
}

.rules-sections {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* ── Section ── */

.rule-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.section-icon {
  font-size: var(--font-size-lg);
}

.section-title h2 {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  flex: 1;
}

.section-badge {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: bold;
}

.section-badge.active {
  background: var(--stock-down);
  color: var(--bg-primary);
}

/* ── Rule Card ── */

.rule-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.rule-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.rule-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--stock-up);
  color: var(--bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: var(--font-size-sm);
  flex-shrink: 0;
}

.rule-header h3 {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  flex: 1;
}

.rule-status {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: bold;
}

.rule-status.on {
  background: var(--stock-down);
  color: var(--bg-primary);
}

.rule-status.pending {
  background: var(--text-muted);
  color: var(--bg-primary);
}

.rule-status.info {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

/* ── Condition ── */

.rule-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rule-condition {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  border-left: 3px solid;
}

.rule-condition.sell {
  background: var(--bg-up-tint);
  border-left-color: var(--stock-up);
}

.rule-condition.buy {
  background: var(--bg-down-tint);
  border-left-color: var(--stock-down);
}

.rule-condition.neutral {
  background: var(--bg-hover);
  border-left-color: var(--text-secondary);
}

.condition-label {
  font-size: var(--font-size-sm);
  font-weight: bold;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.condition-detail {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  line-height: 1.6;
}

.rule-note {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-light);
  line-height: 1.6;
}

/* ── Color Reference ── */

.color-reference {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.color-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.color-dot {
  width: 20px;
  height: 3px;
  border-radius: 2px;
  flex-shrink: 0;
}

.color-label {
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

/* ── Footer ── */

.rules-footer {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-primary);
}

.back-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--font-size-base);
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--stock-up);
}

@media (max-width: 768px) {
  .rules-page {
    padding: var(--spacing-md);
  }
}
</style>