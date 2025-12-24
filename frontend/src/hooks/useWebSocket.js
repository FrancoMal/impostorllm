import { useEffect, useRef, useCallback, useState } from 'react'

export function useWebSocket(gameId, onMessage, onConnect, onDisconnect) {
  const wsRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectTimeoutRef = useRef(null)

  const connect = useCallback(() => {
    if (!gameId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/${gameId}`

    try {
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        onConnect?.()
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        onDisconnect?.()
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 3000)
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          onMessage?.(message)
        } catch (e) {
          console.error('Failed to parse message:', e)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }, [gameId, onMessage, onConnect, onDisconnect])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const send = useCallback((type, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }))
    }
  }, [])

  useEffect(() => {
    if (gameId) {
      connect()
    }
    return () => {
      disconnect()
    }
  }, [gameId, connect, disconnect])

  return { isConnected, send, disconnect }
}
