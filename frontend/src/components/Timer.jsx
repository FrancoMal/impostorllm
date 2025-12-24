import React, { useState, useEffect } from 'react'

export default function Timer({ duration, onComplete }) {
  const [timeLeft, setTimeLeft] = useState(duration)

  useEffect(() => {
    setTimeLeft(duration)
  }, [duration])

  useEffect(() => {
    if (timeLeft <= 0) {
      onComplete?.()
      return
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [timeLeft, onComplete])

  const minutes = Math.floor(timeLeft / 60)
  const seconds = timeLeft % 60

  const getTimerClass = () => {
    if (timeLeft <= 10) return 'danger'
    if (timeLeft <= 30) return 'warning'
    return ''
  }

  return (
    <div className="text-center">
      <div className={`timer ${getTimerClass()}`}>
        {minutes}:{seconds.toString().padStart(2, '0')}
      </div>
      <div className="text-sm text-gray-400 mt-1">
        Tiempo de debate
      </div>
    </div>
  )
}
