/** WebSocket 连接管理器 — 自动重连 + 消息分发 */
import type { WSMessage, RealtimeQuote, SignalItem, StockFullResponse } from '@/types/stock'

type MessageHandler = (msg: WSMessage) => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 3000
  private handlers: Map<string, MessageHandler[]> = new Map()
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null
  private _isConnected = false

  get isConnected(): boolean {
    return this._isConnected
  }

  connect(url?: string): void {
    if (url) this.url = url
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return

    this.ws = new WebSocket(this.url)
    this.ws.onopen = () => this.onOpen()
    this.ws.onmessage = (event) => this.onMessage(event)
    this.ws.onclose = () => this.onClose()
    this.ws.onerror = () => this.onError()
  }

  disconnect(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this._isConnected = false
  }

  subscribe(stockCodes: string[]): void {
    this.send({
      type: 'subscribe',
      payload: { stock_codes: stockCodes, include_signals: true },
    })
  }

  unsubscribe(stockCodes: string[]): void {
    this.send({ type: 'unsubscribe', payload: { stock_codes: stockCodes } })
  }

  requestHist(stockCode: string, period: string, startDate?: string, endDate?: string): void {
    this.send({
      type: 'request_hist',
      payload: { stock_code: stockCode, period, start_date: startDate, end_date: endDate },
    })
  }

  /** 注册消息处理器 */
  on(type: string, handler: MessageHandler): void {
    if (!this.handlers.has(type)) this.handlers.set(type, [])
    this.handlers.get(type)!.push(handler)
  }

  off(type: string, handler: MessageHandler): void {
    const list = this.handlers.get(type)
    if (list) {
      const idx = list.indexOf(handler)
      if (idx >= 0) list.splice(idx, 1)
    }
  }

  private send(data: object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private onOpen(): void {
    this._isConnected = true
    this.reconnectAttempts = 0
    this.startHeartbeat()
    this.dispatchEvent({ type: 'connected', payload: {}, timestamp: new Date().toISOString() })
  }

  private onMessage(event: MessageEvent): void {
    try {
      const msg: WSMessage = JSON.parse(event.data)
      this.dispatchEvent(msg)
    } catch (e) {
      console.error('WebSocket 消息解析失败:', e)
    }
  }

  private onClose(): void {
    this._isConnected = false
    this.stopHeartbeat()
    this.dispatchEvent({ type: 'disconnected', payload: {}, timestamp: new Date().toISOString() })
    this.attemptReconnect()
  }

  private onError(): void {
    // onclose 会随后触发，这里不需要额外处理
  }

  private dispatchEvent(msg: WSMessage): void {
    const handlers = this.handlers.get(msg.type)
    if (handlers) {
      for (const h of handlers) h(msg)
    }
    // 也通知通配处理器
    const wildcards = this.handlers.get('*')
    if (wildcards) {
      for (const h of wildcards) h(msg)
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts)
      setTimeout(() => {
        this.reconnectAttempts++
        this.connect()
      }, delay)
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping', payload: {} })
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

// 全局 WebSocket 实例
export const wsManager = new WebSocketManager()
export default wsManager