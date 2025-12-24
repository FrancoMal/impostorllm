import React from 'react'
import { motion } from 'framer-motion'

export default function WordReveal({ word }) {
  const isImpostor = word === 'IMPOSTOR'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/90 flex items-center justify-center z-50"
    >
      <motion.div
        initial={{ scale: 0.5, rotateY: 90 }}
        animate={{ scale: 1, rotateY: 0 }}
        transition={{ duration: 0.8, type: 'spring' }}
        className="text-center"
      >
        <div className="text-xl text-gray-400 mb-4">
          Tu palabra es:
        </div>

        <motion.div
          className={`text-6xl font-bold mb-6 ${
            isImpostor ? 'text-red-500' : 'text-green-400'
          }`}
          animate={isImpostor ? { scale: [1, 1.1, 1] } : {}}
          transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 1 }}
        >
          {word}
        </motion.div>

        {isImpostor ? (
          <div className="text-red-400 max-w-sm mx-auto">
            <p className="text-lg font-medium mb-2">¡Eres el impostor!</p>
            <p className="text-sm text-gray-400">
              No conoces la palabra secreta. Observa las pistas de los demás
              e intenta pasar desapercibido. Si te descubren, tendrás una
              oportunidad de adivinar la palabra.
            </p>
          </div>
        ) : (
          <div className="text-green-400 max-w-sm mx-auto">
            <p className="text-lg font-medium mb-2">Eres inocente</p>
            <p className="text-sm text-gray-400">
              Da pistas sutiles relacionadas con la palabra. ¡Cuidado! Si
              eres muy obvio, el impostor podría adivinarla.
            </p>
          </div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          className="mt-8 text-gray-500 text-sm"
        >
          El juego comenzará en unos segundos...
        </motion.div>
      </motion.div>
    </motion.div>
  )
}
