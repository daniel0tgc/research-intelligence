import { useAgentStore } from '../store/agent'

const WS_URL = import.meta.env.VITE_WS_URL

let socket: WebSocket | null = null

export function getSocket(): WebSocket {
  if (!socket || socket.readyState > 1) {
    socket = new WebSocket(WS_URL)
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string)
        useAgentStore.getState().handleEvent(data)
      } catch {
        // ignore malformed messages
      }
    }
    socket.onerror = () => {
      // connection errors are recoverable — next getSocket() call will reconnect
    }
  }
  return socket
}

export function initSocket(): void {
  getSocket()
}
