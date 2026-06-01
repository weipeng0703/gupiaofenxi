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

      <!-- ── 微信推送设置 ── -->
      <section class="rule-section">
        <div class="section-title">
          <span class="section-icon">💬</span>
          <h2>微信推送设置</h2>
          <span :class="['section-badge', wechatConfigured ? 'active' : 'pending']">
            {{ wechatConfigured ? '已配置' : '未配置' }}
          </span>
        </div>

        <div class="rule-card">
          <div class="rule-header">
            <h3>企业微信机器人推送</h3>
          </div>
          <div class="rule-body">
            <div class="wechat-setup-steps">
              <div class="step">
                <div class="step-num">1</div>
                <div class="step-content">
                  <strong>注册企业微信</strong>
                  <p>访问 <a href="https://work.weixin.qq.com/" target="_blank">work.weixin.qq.com</a>，个人即可免费注册</p>
                </div>
              </div>
              <div class="step">
                <div class="step-num">2</div>
                <div class="step-content">
                  <strong>创建群聊 + 添加机器人</strong>
                  <p>在企业微信中创建一个群聊 → 群设置 → 群机器人 → 添加机器人 → 复制 Webhook 地址</p>
                </div>
              </div>
              <div class="step">
                <div class="step-num">3</div>
                <div class="step-content">
                  <strong>配置 Webhook URL</strong>
                  <p>在后端目录创建 <code>.env</code> 文件，添加：</p>
                  <pre class="code-block">WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key</pre>
                </div>
              </div>
              <div class="step">
                <div class="step-num">4</div>
                <div class="step-content">
                  <strong>重启后端 + 测试</strong>
                  <p>重启后端服务，然后点击下方按钮测试推送</p>
                </div>
              </div>
            </div>
          </div>
          <div class="rule-note">
            <button class="test-push-btn" @click="testWechatPush" :disabled="testingPush">
              {{ testingPush ? '发送中...' : '📨 发送测试消息' }}
            </button>
            <span v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'fail']">
              {{ testResult.message }}
            </span>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const wechatConfigured = ref(false)
const testingPush = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

onMounted(async () => {
  try {
    const { data } = await axios.get(`${apiBaseUrl}/wechat/status`)
    wechatConfigured.value = data.configured
  } catch {
    wechatConfigured.value = false
  }
})

async function testWechatPush() {
  testingPush.value = true
  testResult.value = null
  try {
    const { data } = await axios.post(`${apiBaseUrl}/wechat/test`)
    testResult.value = data
    if (data.success) {
      wechatConfigured.value = true
    }
  } catch (e: any) {
    testResult.value = { success: false, message: e?.response?.data?.detail || '请求失败，请检查后端是否运行' }
  } finally {
    testingPush.value = false
  }
}
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

/* ── 微信推送设置 ── */

.wechat-setup-steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.step {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.step-num {
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

.step-content p {
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.step-content a {
  color: var(--stock-up);
  text-decoration: none;
}

.step-content a:hover {
  text-decoration: underline;
}

.code-block {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  margin-top: var(--spacing-xs);
  overflow-x: auto;
}

.test-push-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid var(--stock-up);
  border-radius: var(--radius-sm);
  background: var(--stock-up);
  color: var(--bg-primary);
  cursor: pointer;
  font-size: var(--font-size-base);
  font-weight: bold;
  transition: opacity 0.2s;
}

.test-push-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-push-btn:not(:disabled):hover {
  opacity: 0.9;
}

.test-result {
  margin-left: var(--spacing-md);
  font-size: var(--font-size-sm);
  font-weight: bold;
}

.test-result.success {
  color: var(--stock-down);
}

.test-result.fail {
  color: var(--stock-up);
}

.section-badge.pending {
  background: var(--text-muted);
  color: var(--bg-primary);
}

@media (max-width: 768px) {
  .rules-page {
    padding: var(--spacing-md);
  }
}
</style>