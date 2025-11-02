'use client'

import React, { useState, useEffect } from 'react'

interface PlayfulLoadingAnimationProps {
  isDarkMode: boolean
}

/**
 * Origami-style paper folding animation
 * Cycles through different paper toys: crane, boat, butterfly, star
 */
export const PlayfulLoadingAnimation: React.FC<PlayfulLoadingAnimationProps> = ({ isDarkMode }) => {
  // Shuffle array using Fisher-Yates algorithm
  const shuffleArray = (array: number[]) => {
    const shuffled = [...array]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    return shuffled
  }

  // Sophisticated color palettes - sleek and curated
  const colorPalettes = [
    // Oceanic blues
    { paper: '#4A90E2', fold: '#2E5C8A', shadow: 'rgba(74, 144, 226, 0.3)' },
    // Forest greens
    { paper: '#52C6A0', fold: '#2E8B76', shadow: 'rgba(82, 198, 160, 0.3)' },
    // Sunset coral
    { paper: '#FF7E67', fold: '#C84E3D', shadow: 'rgba(255, 126, 103, 0.3)' },
    // Royal purple
    { paper: '#9B59B6', fold: '#6C3E85', shadow: 'rgba(155, 89, 182, 0.3)' },
    // Golden amber
    { paper: '#F39C12', fold: '#B8740F', shadow: 'rgba(243, 156, 18, 0.3)' },
    // Cherry blossom
    { paper: '#FF8BA7', fold: '#C75879', shadow: 'rgba(255, 139, 167, 0.3)' },
    // Slate blue
    { paper: '#5DADE2', fold: '#3B7FA8', shadow: 'rgba(93, 173, 226, 0.3)' },
    // Mint fresh
    { paper: '#48C9B0', fold: '#31857A', shadow: 'rgba(72, 201, 176, 0.3)' },
    // Lavender dream
    { paper: '#AF7AC5', fold: '#7F5692', shadow: 'rgba(175, 122, 197, 0.3)' },
    // Tangerine
    { paper: '#EB984E', fold: '#B5714A', shadow: 'rgba(235, 152, 78, 0.3)' },
    // Crimson
    { paper: '#E74C3C', fold: '#A93529', shadow: 'rgba(231, 76, 60, 0.3)' },
    // Teal
    { paper: '#1ABC9C', fold: '#148F77', shadow: 'rgba(26, 188, 156, 0.3)' },
    // Rose gold
    { paper: '#E8A091', fold: '#B47468', shadow: 'rgba(232, 160, 145, 0.3)' },
    // Indigo
    { paper: '#5C6BC0', fold: '#3F4C8F', shadow: 'rgba(92, 107, 192, 0.3)' },
    // Peach
    { paper: '#FFAB91', fold: '#C97B64', shadow: 'rgba(255, 171, 145, 0.3)' },
    // Steel blue
    { paper: '#607D8B', fold: '#455A64', shadow: 'rgba(96, 125, 139, 0.3)' },
    // Lime
    { paper: '#9CCC65', fold: '#7CB342', shadow: 'rgba(156, 204, 101, 0.3)' },
    // Plum
    { paper: '#BA68C8', fold: '#8E24AA', shadow: 'rgba(186, 104, 200, 0.3)' },
    // Salmon
    { paper: '#FF8A80', fold: '#D56B63', shadow: 'rgba(255, 138, 128, 0.3)' },
    // Turquoise
    { paper: '#4DD0E1', fold: '#36A3B4', shadow: 'rgba(77, 208, 225, 0.3)' },
  ]

  // Initialize with shuffled order - 20 shapes (mix of traditional + modern origami)
  // Traditional: Crane(0), Boat(1), Butterfly(2), Star(3), Fish(5), Fox(7),
  //              Dragon(8), Peacock(9), Koi(10), Samurai(11), Frog(12), Elephant(13), Swan(14), Unicorn(15)
  // Modern: Car(16), Plane(17), Rocket(18), Camera(19), Robot(20), Laptop(21)
  const [shapeOrder, setShapeOrder] = useState<number[]>(() =>
    shuffleArray([0, 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
  )
  const [colorOrder, setColorOrder] = useState<number[]>(() =>
    shuffleArray([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
  )
  const [currentIndex, setCurrentIndex] = useState(0)
  const currentShape = shapeOrder[currentIndex]
  const currentColor = colorPalettes[colorOrder[currentIndex]]

  // Cycle through shapes every 6 seconds - time for full fold sequence
  // Total cycle: 120 seconds for all shapes, then reshuffle
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => {
        const nextIndex = prev + 1
        // When we've shown all shapes, reshuffle for next round
        if (nextIndex >= shapeOrder.length) {
          setShapeOrder(shuffleArray([0, 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]))
          setColorOrder(shuffleArray([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]))
          return 0
        }
        return nextIndex
      })
    }, 6000) // 6 seconds per shape - allows for full folding sequence
    return () => clearInterval(interval)
  }, [shapeOrder.length])

  // Use random color from palette for each shape
  const paperColor = currentColor.paper
  const foldLineColor = currentColor.fold
  const shadowColor = currentColor.shadow

  return (
    <div className="relative w-48 h-48 mx-auto flex items-center justify-center">
      {/* Origami Crane */}
      {currentShape === 0 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Body */}
          <polygon
            points="100,50 140,100 100,140 60,100"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiFloat 1.8s ease-in-out infinite' }}
          />
          {/* Wings */}
          <polygon
            points="100,100 40,80 60,100"
            fill={paperColor}
            opacity="0.8"
            stroke={foldLineColor}
            strokeWidth="1.5"
            style={{ animation: 'origamiWing 1.2s ease-in-out infinite' }}
          />
          <polygon
            points="100,100 160,80 140,100"
            fill={paperColor}
            opacity="0.8"
            stroke={foldLineColor}
            strokeWidth="1.5"
            style={{ animation: 'origamiWing 2s ease-in-out infinite reverse' }}
          />
          {/* Head */}
          <polygon
            points="100,50 90,35 100,40"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
          />
          {/* Tail */}
          <polygon
            points="100,140 100,160 95,150"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
          />
          {/* Animated crease lines - showing paper folding */}
          <line
            x1="70"
            y1="90"
            x2="130"
            y2="90"
            stroke={foldLineColor}
            strokeWidth="1"
            opacity="0.2"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out' }}
          />
          <line
            x1="100"
            y1="50"
            x2="100"
            y2="140"
            stroke={foldLineColor}
            strokeWidth="1"
            opacity="0.2"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out 0.5s' }}
          />
          <line
            x1="80"
            y1="75"
            x2="120"
            y2="115"
            stroke={foldLineColor}
            strokeWidth="0.8"
            opacity="0.15"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out 1s' }}
          />
        </svg>
      )}

      {/* Origami Boat */}
      {currentShape === 1 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Boat hull */}
          <polygon
            points="70,120 130,120 110,150 90,150"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiFloat 2.5s ease-in-out infinite' }}
          />
          {/* Sail */}
          <polygon
            points="100,60 70,120 130,120"
            fill={paperColor}
            opacity="0.9"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiSail 3s ease-in-out infinite' }}
          />
          {/* Animated fold lines showing paper transformation */}
          <line
            x1="85"
            y1="90"
            x2="115"
            y2="90"
            stroke={foldLineColor}
            strokeWidth="1"
            opacity="0.2"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out 0.3s' }}
          />
          <line
            x1="100"
            y1="60"
            x2="100"
            y2="120"
            stroke={foldLineColor}
            strokeWidth="1"
            opacity="0.2"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out 0.6s' }}
          />
          <line
            x1="70"
            y1="120"
            x2="90"
            y2="150"
            stroke={foldLineColor}
            strokeWidth="0.8"
            opacity="0.15"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out 0.9s' }}
          />
          <line
            x1="130"
            y1="120"
            x2="110"
            y2="150"
            stroke={foldLineColor}
            strokeWidth="0.8"
            opacity="0.15"
            style={{ animation: 'origamiCreaseAppear 6s ease-in-out 0.9s' }}
          />
        </svg>
      )}

      {/* Origami Butterfly */}
      {currentShape === 2 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Left wing top */}
          <ellipse
            cx="70"
            cy="80"
            rx="35"
            ry="40"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiWingFlutter 0.9s ease-in-out infinite', transformOrigin: '100px 100px' }}
          />
          {/* Left wing bottom */}
          <ellipse
            cx="75"
            cy="120"
            rx="30"
            ry="35"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiWingFlutter 1.5s ease-in-out infinite 0.1s', transformOrigin: '100px 100px' }}
          />
          {/* Right wing top */}
          <ellipse
            cx="130"
            cy="80"
            rx="35"
            ry="40"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiWingFlutter 0.9s ease-in-out infinite', transformOrigin: '100px 100px' }}
          />
          {/* Right wing bottom */}
          <ellipse
            cx="125"
            cy="120"
            rx="30"
            ry="35"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiWingFlutter 1.5s ease-in-out infinite 0.1s', transformOrigin: '100px 100px' }}
          />
          {/* Body */}
          <ellipse cx="100" cy="100" rx="8" ry="50" fill={foldLineColor} />
        </svg>
      )}

      {/* Origami Star */}
      {currentShape === 3 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* 5-pointed star */}
          <polygon
            points="100,40 115,80 160,85 125,115 135,160 100,135 65,160 75,115 40,85 85,80"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiRotate 4s ease-in-out infinite' }}
          />
          {/* Inner fold lines */}
          <polygon
            points="100,70 110,95 125,100 110,110 100,130 90,110 75,100 90,95"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="1"
            opacity="0.5"
          />
        </svg>
      )}

      {/* Origami Heart */}
      {currentShape === 4 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out' }}
        >
          {/* Heart shape */}
          <path
            d="M100,140 L70,100 Q60,80 75,70 Q100,60 100,85 Q100,60 125,70 Q140,80 130,100 Z"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiPulse 2s ease-in-out infinite' }}
          />
          {/* Center fold line */}
          <line x1="100" y1="70" x2="100" y2="140" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
        </svg>
      )}

      {/* Origami Angelfish - Elegant tropical fish */}
      {currentShape === 5 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Main body - diamond shape characteristic of angelfish */}
          <path
            d="M100,60 Q120,80 125,100 Q120,120 100,140 Q80,120 75,100 Q80,80 100,60"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiAngelfishGlide 3s ease-in-out infinite' }}
          />
          {/* Dorsal fin - tall and flowing */}
          <path
            d="M90,65 Q85,40 90,30 Q95,25 100,30 Q105,40 100,65"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiAngelfishFinFlow 2.5s ease-in-out infinite' }}
          />
          {/* Ventral fin - mirror of dorsal */}
          <path
            d="M90,135 Q85,160 90,170 Q95,175 100,170 Q105,160 100,135"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiAngelfishFinFlow 2.5s ease-in-out infinite 0.3s' }}
          />
          {/* Pectoral fins - delicate side fins */}
          <path
            d="M105,90 Q120,85 125,90 Q120,95 110,100"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
            opacity="0.85"
            style={{ animation: 'origamiAngelfishPectoralWave 2s ease-in-out infinite' }}
          />
          <path
            d="M105,110 Q120,115 125,110 Q120,105 110,100"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
            opacity="0.85"
            style={{ animation: 'origamiAngelfishPectoralWave 2s ease-in-out infinite 0.2s' }}
          />
          {/* Tail fin - elegant and flowing */}
          <path
            d="M75,100 Q65,95 55,95 L60,100 L55,105 Q65,105 75,100"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiAngelfishTailSway 2.5s ease-in-out infinite' }}
          />
          {/* Decorative stripes - characteristic angelfish pattern */}
          <path d="M95,70 Q100,85 95,100 Q100,115 95,130" stroke={foldLineColor} strokeWidth="1.5" opacity="0.4" fill="none" />
          <path d="M105,70 Q110,85 105,100 Q110,115 105,130" stroke={foldLineColor} strokeWidth="1.5" opacity="0.4" fill="none" />
          {/* Eye */}
          <circle cx="108" cy="85" r="4" fill={foldLineColor} />
          <circle cx="108" cy="85" r="2" fill={paperColor} opacity="0.6" />
          {/* Mouth */}
          <path d="M118,97 Q120,100 118,103" stroke={foldLineColor} strokeWidth="1.5" fill="none" />
          {/* Gill line */}
          <path d="M105,82 Q108,88 105,94" stroke={foldLineColor} strokeWidth="1" opacity="0.5" fill="none" />
        </svg>
      )}

      {/* Origami Flower */}
      {currentShape === 6 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out' }}
        >
          {/* 5 petals */}
          {[0, 1, 2, 3, 4].map((i) => {
            const angle = (i * 72) - 90
            const rad = (angle * Math.PI) / 180
            const x = 100 + Math.cos(rad) * 30
            const y = 100 + Math.sin(rad) * 30
            return (
              <ellipse
                key={i}
                cx={x}
                cy={y}
                rx="20"
                ry="35"
                fill={paperColor}
                stroke={foldLineColor}
                strokeWidth="2"
                opacity="0.9"
                style={{
                  transform: `rotate(${angle}deg)`,
                  transformOrigin: '100px 100px',
                  animation: 'origamiPetalWave 3s ease-in-out infinite',
                  animationDelay: `${i * 0.15}s`
                }}
              />
            )
          })}
          {/* Center */}
          <circle cx="100" cy="100" r="12" fill={foldLineColor} />
        </svg>
      )}

      {/* Origami Fox */}
      {currentShape === 7 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Left ear */}
          <polygon
            points="70,60 50,90 85,90"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiEarTwitch 2s ease-in-out infinite' }}
          />
          {/* Right ear */}
          <polygon
            points="130,60 150,90 115,90"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiEarTwitch 2s ease-in-out infinite 0.3s' }}
          />
          {/* Face */}
          <polygon
            points="100,90 70,120 130,120"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Snout */}
          <polygon
            points="100,120 85,135 115,135"
            fill={paperColor}
            opacity="0.8"
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Eyes */}
          <circle cx="85" cy="105" r="3" fill={foldLineColor} />
          <circle cx="115" cy="105" r="3" fill={foldLineColor} />
          {/* Nose */}
          <circle cx="100" cy="125" r="3" fill={foldLineColor} />
        </svg>
      )}

      {/* Origami Dragon */}
      {currentShape === 8 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Dragon body - elongated */}
          <path
            d="M60,120 Q70,100 90,95 Q110,90 130,100 Q140,110 135,125"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiDragonBody 3s ease-in-out infinite' }}
          />
          {/* Dragon neck and head */}
          <path
            d="M130,100 Q145,85 150,70 L155,65 L150,60 L145,65"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Wings - large and majestic */}
          <path
            d="M95,95 Q80,70 70,55 L75,60 Q85,75 95,90"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiDragonWing 2.5s ease-in-out infinite' }}
          />
          <path
            d="M115,95 Q130,70 140,55 L135,60 Q125,75 115,90"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiDragonWing 2.5s ease-in-out infinite 0.2s' }}
          />
          {/* Tail - curved and spiky */}
          <path
            d="M60,120 Q45,130 35,145 L40,140 Q50,130 58,122"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiTailSway 2s ease-in-out infinite' }}
          />
          {/* Spikes along back */}
          <polygon points="85,95 83,85 87,90" fill={foldLineColor} opacity="0.7" />
          <polygon points="105,92 103,82 107,87" fill={foldLineColor} opacity="0.7" />
          <polygon points="120,97 118,87 122,92" fill={foldLineColor} opacity="0.7" />
        </svg>
      )}

      {/* Origami Phoenix - Majestic mythical bird */}
      {currentShape === 9 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Tail feathers - layered flowing design */}
          {/* Layer 1 - Longest tail feathers */}
          <path
            d="M100,130 Q80,145 70,165 Q75,160 85,150"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiPhoenixTailFlow 3s ease-in-out infinite', animationDelay: '0s' }}
          />
          <path
            d="M100,130 Q100,150 95,175 Q98,168 100,155"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiPhoenixTailFlow 3s ease-in-out infinite', animationDelay: '0.2s' }}
          />
          <path
            d="M100,130 Q120,145 130,165 Q125,160 115,150"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiPhoenixTailFlow 3s ease-in-out infinite', animationDelay: '0.4s' }}
          />
          {/* Layer 2 - Mid-length feathers */}
          <path
            d="M98,125 Q85,135 80,150 Q85,145 92,138"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.8"
            opacity="0.75"
            style={{ animation: 'origamiPhoenixTailFlow 3s ease-in-out infinite', animationDelay: '0.1s' }}
          />
          <path
            d="M102,125 Q115,135 120,150 Q115,145 108,138"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.8"
            opacity="0.75"
            style={{ animation: 'origamiPhoenixTailFlow 3s ease-in-out infinite', animationDelay: '0.3s' }}
          />
          {/* Body - elegant curved shape */}
          <ellipse
            cx="100"
            cy="105"
            rx="22"
            ry="30"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiPhoenixBodyFloat 2.5s ease-in-out infinite' }}
          />
          {/* Wings - large and majestic */}
          {/* Left wing - upper section */}
          <path
            d="M85,100 Q60,85 45,80 Q50,88 65,95"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiPhoenixWingBeat 2.5s ease-in-out infinite' }}
          />
          {/* Left wing - lower section */}
          <path
            d="M85,110 Q65,105 50,105 Q58,110 72,115"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiPhoenixWingBeat 2.5s ease-in-out infinite', animationDelay: '0.1s' }}
          />
          {/* Right wing - upper section */}
          <path
            d="M115,100 Q140,85 155,80 Q150,88 135,95"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiPhoenixWingBeat 2.5s ease-in-out infinite' }}
          />
          {/* Right wing - lower section */}
          <path
            d="M115,110 Q135,105 150,105 Q142,110 128,115"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiPhoenixWingBeat 2.5s ease-in-out infinite', animationDelay: '0.1s' }}
          />
          {/* Wing detail lines */}
          <path d="M85,100 L70,90" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <path d="M85,105 L68,98" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <path d="M115,100 L130,90" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <path d="M115,105 L132,98" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          {/* Neck and head */}
          <path
            d="M100,75 Q98,85 100,90"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="6"
            strokeLinecap="round"
          />
          <circle cx="100" cy="70" r="12" fill={paperColor} stroke={foldLineColor} strokeWidth="2" />
          {/* Crown/crest - flame-like */}
          <path
            d="M95,62 Q92,52 95,48 L97,52 L100,45 L103,52 L105,48 Q108,52 105,62"
            fill={foldLineColor}
            opacity="0.8"
            style={{ animation: 'origamiPhoenixCrownFlicker 2s ease-in-out infinite' }}
          />
          {/* Beak */}
          <path d="M100,70 L108,68 L108,72 Z" fill={foldLineColor} />
          {/* Eye */}
          <circle cx="103" cy="68" r="2" fill={foldLineColor} />
          {/* Chest detail */}
          <path d="M95,100 Q100,108 105,100" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
        </svg>
      )}

      {/* Origami Koi Fish */}
      {currentShape === 10 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Koi body - elegant curved shape */}
          <path
            d="M50,100 Q60,85 80,80 Q110,75 130,85 Q145,95 150,110 Q145,125 130,130 Q100,135 70,125 Q55,115 50,100"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiKoiSwim 3s ease-in-out infinite' }}
          />
          {/* Head detail */}
          <circle cx="145" cy="102" r="8" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.9" />
          {/* Eye */}
          <circle cx="145" cy="102" r="3" fill={foldLineColor} />
          {/* Mouth */}
          <path d="M152,105 Q155,107 152,109" stroke={foldLineColor} strokeWidth="1.5" fill="none" />
          {/* Dorsal fin - top */}
          <path
            d="M95,75 Q95,60 100,55 Q105,60 105,75"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiKoiFinWave 2s ease-in-out infinite' }}
          />
          {/* Pectoral fin - side */}
          <path
            d="M115,110 Q125,120 120,130 Q115,125 115,115"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
            opacity="0.8"
            style={{ animation: 'origamiKoiFinWave 2s ease-in-out infinite 0.2s' }}
          />
          {/* Tail - majestic fan shape */}
          <path
            d="M50,100 Q35,90 25,85 L30,95 Q40,100 30,105 L25,115 Q35,110 50,100"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiKoiTailFan 2.5s ease-in-out infinite' }}
          />
          {/* Scale pattern - decorative lines */}
          <path d="M70,95 Q75,90 80,95" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          <path d="M85,92 Q90,87 95,92" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          <path d="M100,90 Q105,85 110,90" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          <path d="M115,92 Q120,87 125,92" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          <path d="M70,110 Q75,115 80,110" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          <path d="M85,113 Q90,118 95,113" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          <path d="M100,115 Q105,120 110,115" stroke={foldLineColor} strokeWidth="1" opacity="0.4" fill="none" />
          {/* Whiskers */}
          <line x1="152" y1="104" x2="165" y2="102" stroke={foldLineColor} strokeWidth="1" opacity="0.6" />
          <line x1="152" y1="106" x2="165" y2="108" stroke={foldLineColor} strokeWidth="1" opacity="0.6" />
        </svg>
      )}

      {/* Origami Samurai Helmet */}
      {currentShape === 11 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Helmet main body */}
          <polygon
            points="100,50 60,120 140,120"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Horns - left */}
          <path
            d="M70,90 Q50,70 40,50 L45,55 Q60,75 72,95"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
          />
          {/* Horns - right */}
          <path
            d="M130,90 Q150,70 160,50 L155,55 Q140,75 128,95"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
          />
          {/* Neck guard flaps */}
          <polygon
            points="60,120 50,140 70,135"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
          />
          <polygon
            points="140,120 150,140 130,135"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Center ornament */}
          <circle cx="100" cy="85" r="8" fill={foldLineColor} />
          {/* Fold lines for detail */}
          <line x1="100" y1="50" x2="100" y2="120" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <line x1="80" y1="85" x2="120" y2="85" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
        </svg>
      )}

      {/* Origami Frog - jumping pose */}
      {currentShape === 12 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Body */}
          <ellipse
            cx="100"
            cy="110"
            rx="40"
            ry="30"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiFrogJump 2s ease-in-out infinite' }}
          />
          {/* Head */}
          <ellipse
            cx="100"
            cy="80"
            rx="35"
            ry="25"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiFrogJump 2s ease-in-out infinite' }}
          />
          {/* Eyes - bulging */}
          <ellipse cx="85" cy="75" rx="10" ry="12" fill={paperColor} stroke={foldLineColor} strokeWidth="2" />
          <ellipse cx="115" cy="75" rx="10" ry="12" fill={paperColor} stroke={foldLineColor} strokeWidth="2" />
          <circle cx="85" cy="75" r="4" fill={foldLineColor} />
          <circle cx="115" cy="75" r="4" fill={foldLineColor} />
          {/* Front legs */}
          <path
            d="M75,110 L60,130 L65,132"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            style={{ animation: 'origamiFrogLeg 2s ease-in-out infinite' }}
          />
          <path
            d="M125,110 L140,130 L135,132"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            style={{ animation: 'origamiFrogLeg 2s ease-in-out infinite' }}
          />
          {/* Back legs - folded */}
          <path
            d="M70,115 Q55,120 50,135 L55,137"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            opacity="0.8"
          />
          <path
            d="M130,115 Q145,120 150,135 L145,137"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            opacity="0.8"
          />
        </svg>
      )}

      {/* Origami Elephant */}
      {currentShape === 13 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Body */}
          <ellipse
            cx="110"
            cy="110"
            rx="45"
            ry="40"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Head */}
          <circle cx="90" cy="85" r="28" fill={paperColor} stroke={foldLineColor} strokeWidth="2" />
          {/* Trunk - curved */}
          <path
            d="M90,110 Q75,125 70,145 Q68,155 75,158"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="4"
            style={{ animation: 'origamiTrunkSway 3s ease-in-out infinite' }}
          />
          {/* Ears - large */}
          <ellipse
            cx="65"
            cy="85"
            rx="20"
            ry="30"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiEarFlap 3s ease-in-out infinite' }}
          />
          <ellipse
            cx="115"
            cy="85"
            rx="20"
            ry="30"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiEarFlap 3s ease-in-out infinite 0.3s' }}
          />
          {/* Eye */}
          <circle cx="90" cy="80" r="4" fill={foldLineColor} />
          {/* Tusks */}
          <path d="M85,100 Q82,110 80,115" stroke={foldLineColor} strokeWidth="2" fill="none" opacity="0.7" />
          <path d="M95,100 Q98,110 100,115" stroke={foldLineColor} strokeWidth="2" fill="none" opacity="0.7" />
          {/* Legs */}
          <rect x="95" y="135" width="12" height="25" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.85" />
          <rect x="120" y="135" width="12" height="25" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.85" />
        </svg>
      )}

      {/* Origami Swan */}
      {currentShape === 14 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Body - elegant curve */}
          <ellipse
            cx="120"
            cy="120"
            rx="40"
            ry="30"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiFloat 3s ease-in-out infinite' }}
          />
          {/* Neck - graceful S-curve */}
          <path
            d="M90,110 Q70,95 70,75 Q70,60 80,50"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="6"
            strokeLinecap="round"
            style={{ animation: 'origamiSwanNeck 4s ease-in-out infinite' }}
          />
          {/* Head */}
          <ellipse
            cx="80"
            cy="45"
            rx="8"
            ry="10"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Beak */}
          <polygon points="80,40 75,35 80,37" fill={foldLineColor} />
          {/* Wing - layered */}
          <path
            d="M120,105 Q135,95 145,90 Q140,100 130,110"
            fill={paperColor}
            opacity="0.85"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiWingGlide 3s ease-in-out infinite' }}
          />
          <path
            d="M125,115 Q140,110 150,108 Q145,118 135,125"
            fill={paperColor}
            opacity="0.75"
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiWingGlide 3s ease-in-out infinite 0.2s' }}
          />
          {/* Tail feathers */}
          <path d="M160,125 L170,130 L165,120" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          <path d="M158,120 L168,123 L163,115" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" opacity="0.8" />
        </svg>
      )}

      {/* Origami Unicorn */}
      {currentShape === 15 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Body */}
          <ellipse
            cx="120"
            cy="115"
            rx="45"
            ry="35"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiFloat 2.5s ease-in-out infinite' }}
          />
          {/* Neck */}
          <path
            d="M85,105 Q75,90 75,75"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Head */}
          <ellipse cx="75" cy="65" rx="15" ry="18" fill={paperColor} stroke={foldLineColor} strokeWidth="2" />
          {/* Horn - spiraling */}
          <path
            d="M75,50 L73,35 L75,38 L77,35 Z"
            fill={foldLineColor}
            stroke={foldLineColor}
            strokeWidth="1"
            style={{ animation: 'origamiHornGlow 2s ease-in-out infinite' }}
          />
          {/* Mane - flowing */}
          <path
            d="M78,60 Q90,55 95,50"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            opacity="0.8"
            style={{ animation: 'origamiManeFlow 2s ease-in-out infinite' }}
          />
          <path
            d="M80,68 Q92,65 98,62"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            opacity="0.7"
            style={{ animation: 'origamiManeFlow 2s ease-in-out infinite 0.2s' }}
          />
          <path
            d="M82,76 Q94,75 100,74"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            opacity="0.6"
            style={{ animation: 'origamiManeFlow 2s ease-in-out infinite 0.4s' }}
          />
          {/* Ear */}
          <polygon points="72,55 68,45 75,50" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          {/* Eye */}
          <circle cx="72" cy="65" r="3" fill={foldLineColor} />
          {/* Legs */}
          <rect x="105" y="135" width="10" height="28" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.85" />
          <rect x="130" y="135" width="10" height="28" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.85" />
          {/* Tail - flowing */}
          <path
            d="M165,115 Q175,120 180,130"
            stroke={foldLineColor}
            strokeWidth="4"
            fill="none"
            style={{ animation: 'origamiTailFlow 2.5s ease-in-out infinite' }}
          />
        </svg>
      )}

      {/* Origami Car */}
      {currentShape === 16 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Car body */}
          <rect
            x="60"
            y="110"
            width="80"
            height="30"
            rx="5"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiCarBounce 2s ease-in-out infinite' }}
          />
          {/* Car roof/cabin */}
          <path
            d="M75,110 L85,85 L115,85 L125,110"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
          />
          {/* Windows */}
          <path
            d="M80,105 L88,90 L112,90 L120,105"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="1.5"
            opacity="0.6"
          />
          <line x1="100" y1="90" x2="100" y2="105" stroke={foldLineColor} strokeWidth="1.5" opacity="0.6" />
          {/* Wheels */}
          <circle
            cx="80"
            cy="140"
            r="12"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="3"
            style={{ animation: 'origamiWheelSpin 0.8s linear infinite' }}
          />
          <circle cx="80" cy="140" r="6" fill={foldLineColor} />
          <circle
            cx="120"
            cy="140"
            r="12"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="3"
            style={{ animation: 'origamiWheelSpin 0.8s linear infinite' }}
          />
          <circle cx="120" cy="140" r="6" fill={foldLineColor} />
          {/* Headlights */}
          <circle cx="145" cy="120" r="3" fill={foldLineColor} opacity="0.7" />
          <circle cx="145" cy="130" r="3" fill={foldLineColor} opacity="0.7" />
          {/* Detail lines */}
          <line x1="60" y1="125" x2="140" y2="125" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
        </svg>
      )}

      {/* Origami Plane */}
      {currentShape === 17 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Plane body - sleek fuselage */}
          <path
            d="M50,100 L140,100 L160,110 L150,100 L160,90 L140,100 Z"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiPlaneFly 3s ease-in-out infinite' }}
          />
          {/* Wings - main */}
          <polygon
            points="90,100 60,70 80,95"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiWingTilt 2.5s ease-in-out infinite' }}
          />
          <polygon
            points="90,100 60,130 80,105"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.9"
            style={{ animation: 'origamiWingTilt 2.5s ease-in-out infinite' }}
          />
          {/* Tail wings */}
          <polygon
            points="50,100 40,85 45,95"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
            opacity="0.8"
          />
          <polygon
            points="50,100 40,115 45,105"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="1.5"
            opacity="0.8"
          />
          {/* Cockpit window */}
          <circle cx="130" cy="100" r="8" fill="none" stroke={foldLineColor} strokeWidth="2" opacity="0.6" />
          {/* Engine details */}
          <ellipse cx="150" cy="100" rx="8" ry="12" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" opacity="0.7" />
          {/* Center fold line */}
          <line x1="50" y1="100" x2="140" y2="100" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
        </svg>
      )}

      {/* Origami Rocket */}
      {currentShape === 18 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Rocket body */}
          <rect
            x="85"
            y="70"
            width="30"
            height="70"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiRocketLaunch 2s ease-in-out infinite' }}
          />
          {/* Nose cone */}
          <polygon
            points="100,40 85,70 115,70"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Fins - left */}
          <polygon
            points="85,120 70,140 85,135"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
          />
          {/* Fins - right */}
          <polygon
            points="115,120 130,140 115,135"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
          />
          {/* Window/porthole */}
          <circle cx="100" cy="85" r="8" fill="none" stroke={foldLineColor} strokeWidth="2" opacity="0.6" />
          <circle cx="100" cy="85" r="4" fill={foldLineColor} opacity="0.4" />
          {/* Flames/exhaust */}
          <path
            d="M90,140 L85,155 L90,148 L85,160"
            stroke={foldLineColor}
            strokeWidth="2"
            fill="none"
            opacity="0.8"
            style={{ animation: 'origamiFlameFlicker 0.5s ease-in-out infinite' }}
          />
          <path
            d="M100,140 L100,165"
            stroke={foldLineColor}
            strokeWidth="3"
            fill="none"
            style={{ animation: 'origamiFlameFlicker 0.5s ease-in-out infinite 0.1s' }}
          />
          <path
            d="M110,140 L115,155 L110,148 L115,160"
            stroke={foldLineColor}
            strokeWidth="2"
            fill="none"
            opacity="0.8"
            style={{ animation: 'origamiFlameFlicker 0.5s ease-in-out infinite 0.2s' }}
          />
          {/* Detail lines */}
          <line x1="85" y1="100" x2="115" y2="100" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <line x1="85" y1="115" x2="115" y2="115" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
        </svg>
      )}

      {/* Origami Camera */}
      {currentShape === 19 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Camera body */}
          <rect
            x="70"
            y="90"
            width="60"
            height="45"
            rx="5"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Lens */}
          <circle
            cx="100"
            cy="112"
            r="18"
            fill="none"
            stroke={foldLineColor}
            strokeWidth="3"
            style={{ animation: 'origamiLensFocus 3s ease-in-out infinite' }}
          />
          <circle cx="100" cy="112" r="12" fill="none" stroke={foldLineColor} strokeWidth="2" opacity="0.7" />
          <circle cx="100" cy="112" r="6" fill={foldLineColor} opacity="0.5" />
          {/* Flash */}
          <rect x="115" y="92" width="10" height="8" rx="2" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          <circle
            cx="120"
            cy="96"
            r="3"
            fill={foldLineColor}
            opacity="0.6"
            style={{ animation: 'origamiFlashBlink 4s ease-in-out infinite' }}
          />
          {/* Viewfinder */}
          <rect x="75" y="92" width="8" height="6" rx="1" fill="none" stroke={foldLineColor} strokeWidth="1.5" opacity="0.7" />
          {/* Shutter button */}
          <circle cx="125" cy="105" r="4" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          {/* Mode dial */}
          <circle cx="80" cy="105" r="5" fill="none" stroke={foldLineColor} strokeWidth="1.5" opacity="0.6" />
          <line x1="80" y1="100" x2="80" y2="105" stroke={foldLineColor} strokeWidth="1" />
          {/* Grip texture */}
          <line x1="72" y1="120" x2="72" y2="130" stroke={foldLineColor} strokeWidth="1" opacity="0.4" />
          <line x1="75" y1="120" x2="75" y2="130" stroke={foldLineColor} strokeWidth="1" opacity="0.4" />
          <line x1="78" y1="120" x2="78" y2="130" stroke={foldLineColor} strokeWidth="1" opacity="0.4" />
        </svg>
      )}

      {/* Origami Robot */}
      {currentShape === 20 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Robot head */}
          <rect
            x="80"
            y="60"
            width="40"
            height="35"
            rx="5"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiRobotNod 2s ease-in-out infinite' }}
          />
          {/* Antenna */}
          <line x1="100" y1="60" x2="100" y2="45" stroke={foldLineColor} strokeWidth="2" />
          <circle cx="100" cy="45" r="4" fill={foldLineColor} style={{ animation: 'origamiAntennaBlink 1.5s ease-in-out infinite' }} />
          {/* Eyes */}
          <rect x="87" y="70" width="8" height="8" fill="none" stroke={foldLineColor} strokeWidth="2" />
          <rect x="105" y="70" width="8" height="8" fill="none" stroke={foldLineColor} strokeWidth="2" />
          <circle
            cx="91"
            cy="74"
            r="3"
            fill={foldLineColor}
            style={{ animation: 'origamiEyeBlink 3s ease-in-out infinite' }}
          />
          <circle
            cx="109"
            cy="74"
            r="3"
            fill={foldLineColor}
            style={{ animation: 'origamiEyeBlink 3s ease-in-out infinite' }}
          />
          {/* Mouth */}
          <rect x="92" y="85" width="16" height="4" fill="none" stroke={foldLineColor} strokeWidth="1.5" />
          <line x1="96" y1="85" x2="96" y2="89" stroke={foldLineColor} strokeWidth="1" />
          <line x1="100" y1="85" x2="100" y2="89" stroke={foldLineColor} strokeWidth="1" />
          <line x1="104" y1="85" x2="104" y2="89" stroke={foldLineColor} strokeWidth="1" />
          {/* Body */}
          <rect x="75" y="95" width="50" height="40" rx="5" fill={paperColor} stroke={foldLineColor} strokeWidth="2" />
          {/* Control panel */}
          <circle cx="90" cy="110" r="5" fill="none" stroke={foldLineColor} strokeWidth="1.5" opacity="0.7" />
          <circle cx="110" cy="110" r="5" fill="none" stroke={foldLineColor} strokeWidth="1.5" opacity="0.7" />
          <rect x="95" y="120" width="10" height="8" fill="none" stroke={foldLineColor} strokeWidth="1" opacity="0.6" />
          {/* Arms */}
          <rect
            x="60"
            y="100"
            width="15"
            height="30"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiRobotArmWave 2.5s ease-in-out infinite' }}
          />
          <rect
            x="125"
            y="100"
            width="15"
            height="30"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            opacity="0.85"
            style={{ animation: 'origamiRobotArmWave 2.5s ease-in-out infinite 0.3s' }}
          />
          {/* Hands */}
          <circle cx="67" cy="130" r="4" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          <circle cx="133" cy="130" r="4" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          {/* Legs */}
          <rect x="85" y="135" width="12" height="20" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.85" />
          <rect x="103" y="135" width="12" height="20" fill={paperColor} stroke={foldLineColor} strokeWidth="2" opacity="0.85" />
          {/* Feet */}
          <rect x="82" y="155" width="18" height="5" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
          <rect x="100" y="155" width="18" height="5" fill={paperColor} stroke={foldLineColor} strokeWidth="1.5" />
        </svg>
      )}

      {/* Origami Laptop */}
      {currentShape === 21 && (
        <svg
          viewBox="0 0 200 200"
          className="w-40 h-40"
          style={{ animation: 'origamiFold 6s ease-in-out', transformStyle: 'preserve-3d' }}
        >
          {/* Laptop base/keyboard */}
          <path
            d="M60,120 L140,120 L145,140 L55,140 Z"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
          />
          {/* Keyboard keys grid */}
          {[0, 1, 2, 3].map((row) =>
            [0, 1, 2, 3, 4, 5].map((col) => (
              <rect
                key={`key-${row}-${col}`}
                x={70 + col * 11}
                y={123 + row * 4}
                width="9"
                height="3"
                fill="none"
                stroke={foldLineColor}
                strokeWidth="0.5"
                opacity="0.4"
              />
            ))
          )}
          {/* Trackpad */}
          <rect x="85" y="132" width="30" height="6" rx="1" fill="none" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          {/* Laptop screen */}
          <rect
            x="65"
            y="70"
            width="70"
            height="50"
            rx="3"
            fill={paperColor}
            stroke={foldLineColor}
            strokeWidth="2"
            style={{ animation: 'origamiScreenGlow 3s ease-in-out infinite' }}
          />
          {/* Screen display area */}
          <rect x="70" y="75" width="60" height="40" fill="none" stroke={foldLineColor} strokeWidth="1.5" opacity="0.6" />
          {/* Screen content - code lines */}
          <line x1="75" y1="82" x2="110" y2="82" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <line x1="75" y1="87" x2="120" y2="87" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <line x1="75" y1="92" x2="105" y2="92" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <line x1="75" y1="97" x2="125" y2="97" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          <line x1="75" y1="102" x2="115" y2="102" stroke={foldLineColor} strokeWidth="1" opacity="0.5" />
          {/* Cursor */}
          <rect
            x="115"
            y="100"
            width="2"
            height="4"
            fill={foldLineColor}
            style={{ animation: 'origamiCursorBlink 1s ease-in-out infinite' }}
          />
          {/* Camera dot */}
          <circle cx="100" cy="72" r="1.5" fill={foldLineColor} opacity="0.6" />
          {/* Hinge */}
          <line x1="65" y1="120" x2="135" y2="120" stroke={foldLineColor} strokeWidth="2" opacity="0.8" />
        </svg>
      )}


      <style jsx>{`
        /* Core origami folding animation - shows transformation from flat paper to shape */
        @keyframes origamiFold {
          0% {
            opacity: 0;
            transform: scale(0.1) rotateX(90deg) rotateY(90deg);
            filter: brightness(1.3);
          }
          /* Unfold from flat paper */
          8% {
            opacity: 0.6;
            transform: scale(0.4) rotateX(70deg) rotateY(70deg);
            filter: brightness(1.2);
          }
          /* First major fold */
          16% {
            opacity: 0.8;
            transform: scale(0.6) rotateX(45deg) rotateY(45deg);
            filter: brightness(1.1);
          }
          /* Second fold - taking shape */
          24% {
            opacity: 0.9;
            transform: scale(0.8) rotateX(20deg) rotateY(20deg);
            filter: brightness(1.05);
          }
          /* Final fold - shape complete */
          32% {
            opacity: 1;
            transform: scale(1) rotateX(0deg) rotateY(0deg);
            filter: brightness(1);
          }
          /* Hold the completed shape */
          68% {
            opacity: 1;
            transform: scale(1) rotateX(0deg) rotateY(0deg);
            filter: brightness(1);
          }
          /* Begin unfolding - reverse sequence */
          76% {
            opacity: 0.9;
            transform: scale(0.9) rotateX(-15deg) rotateY(-15deg);
            filter: brightness(1.05);
          }
          84% {
            opacity: 0.8;
            transform: scale(0.7) rotateX(-40deg) rotateY(-40deg);
            filter: brightness(1.1);
          }
          92% {
            opacity: 0.5;
            transform: scale(0.4) rotateX(-70deg) rotateY(-70deg);
            filter: brightness(1.2);
          }
          /* Fold back to flat */
          100% {
            opacity: 0;
            transform: scale(0.1) rotateX(-90deg) rotateY(-90deg);
            filter: brightness(1.3);
          }
        }

        /* Enhanced floating with paper-like movement */
        @keyframes origamiFloat {
          0%, 100% {
            transform: translateY(0px) translateX(0px) rotateZ(0deg);
          }
          25% {
            transform: translateY(-8px) translateX(2px) rotateZ(1deg);
          }
          50% {
            transform: translateY(-15px) translateX(0px) rotateZ(0deg);
          }
          75% {
            transform: translateY(-8px) translateX(-2px) rotateZ(-1deg);
          }
        }

        /* Wing flapping with realistic paper fold */
        @keyframes origamiWing {
          0%, 100% {
            transform: rotateZ(0deg) scaleY(1);
          }
          25% {
            transform: rotateZ(-12deg) scaleY(0.95);
          }
          50% {
            transform: rotateZ(-25deg) scaleY(0.9);
          }
          75% {
            transform: rotateZ(-12deg) scaleY(0.95);
          }
        }

        /* Sail billowing effect */
        @keyframes origamiSail {
          0%, 100% {
            transform: skewX(0deg) scaleX(1);
          }
          33% {
            transform: skewX(8deg) scaleX(1.05);
          }
          66% {
            transform: skewX(-3deg) scaleX(0.98);
          }
        }

        /* Butterfly wing flutter with folding motion */
        @keyframes origamiWingFlutter {
          0%, 100% {
            transform: scaleX(1) rotateY(0deg);
          }
          25% {
            transform: scaleX(0.85) rotateY(-15deg);
          }
          50% {
            transform: scaleX(0.7) rotateY(-25deg);
          }
          75% {
            transform: scaleX(0.85) rotateY(-15deg);
          }
        }

        /* 3D rotation showing paper dimensionality */
        @keyframes origamiRotate {
          0% {
            transform: rotate(0deg) scale(1);
          }
          25% {
            transform: rotate(90deg) scale(0.95);
          }
          50% {
            transform: rotate(180deg) scale(1);
          }
          75% {
            transform: rotate(270deg) scale(0.95);
          }
          100% {
            transform: rotate(360deg) scale(1);
          }
        }

        /* Pulsing with paper crinkle effect */
        @keyframes origamiPulse {
          0%, 100% {
            transform: scale(1);
            filter: brightness(1);
          }
          50% {
            transform: scale(1.12);
            filter: brightness(1.1);
          }
        }

        /* Crease lines appearing during folding */
        @keyframes origamiCreaseAppear {
          0%, 30% {
            opacity: 0;
            stroke-width: 0;
          }
          40% {
            opacity: 0.4;
            stroke-width: 1.5;
          }
          60% {
            opacity: 0.3;
            stroke-width: 1;
          }
          100% {
            opacity: 0.2;
            stroke-width: 0.8;
          }
        }

        @keyframes origamiSwim {
          0%, 100% {
            transform: translateX(0) rotateZ(0deg);
          }
          50% {
            transform: translateX(-5px) rotateZ(-3deg);
          }
        }

        @keyframes origamiTailWag {
          0%, 100% {
            transform: rotateZ(0deg);
          }
          50% {
            transform: rotateZ(15deg);
          }
        }

        @keyframes origamiPetalWave {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.1);
          }
        }

        @keyframes origamiEarTwitch {
          0%, 90%, 100% {
            transform: rotateZ(0deg);
          }
          95% {
            transform: rotateZ(-5deg);
          }
        }

        /* Dragon animations - powerful wing beats and serpentine body */
        @keyframes origamiDragonBody {
          0%, 100% {
            transform: translateY(0) scaleY(1) scaleX(1);
          }
          25% {
            transform: translateY(-8px) scaleY(1.05) scaleX(0.98);
          }
          50% {
            transform: translateY(-12px) scaleY(1.08) scaleX(0.96);
          }
          75% {
            transform: translateY(-8px) scaleY(1.05) scaleX(0.98);
          }
        }

        @keyframes origamiDragonWing {
          0%, 100% {
            transform: translateY(0) rotateZ(0deg) scaleY(1);
          }
          30% {
            transform: translateY(-15px) rotateZ(-25deg) scaleY(0.85);
          }
          60% {
            transform: translateY(-8px) rotateZ(-12deg) scaleY(0.92);
          }
        }

        @keyframes origamiTailSway {
          0%, 100% {
            transform: rotateZ(0deg) translateX(0);
          }
          33% {
            transform: rotateZ(18deg) translateX(3px);
          }
          66% {
            transform: rotateZ(-8deg) translateX(-2px);
          }
        }

        /* Angelfish animations */
        @keyframes origamiAngelfishGlide {
          0%, 100% {
            transform: translateX(0) translateY(0) rotateZ(0deg);
          }
          25% {
            transform: translateX(-3px) translateY(2px) rotateZ(-3deg);
          }
          50% {
            transform: translateX(0) translateY(4px) rotateZ(0deg);
          }
          75% {
            transform: translateX(3px) translateY(2px) rotateZ(3deg);
          }
        }

        @keyframes origamiAngelfishFinFlow {
          0%, 100% {
            transform: scaleX(1) scaleY(1);
          }
          50% {
            transform: scaleX(1.05) scaleY(1.08);
          }
        }

        @keyframes origamiAngelfishPectoralWave {
          0%, 100% {
            transform: translateX(0) rotateZ(0deg);
          }
          50% {
            transform: translateX(2px) rotateZ(-8deg);
          }
        }

        @keyframes origamiAngelfishTailSway {
          0%, 100% {
            transform: translateX(0) scaleX(1);
          }
          50% {
            transform: translateX(-3px) scaleX(1.1);
          }
        }

        /* Phoenix animations */
        @keyframes origamiPhoenixBodyFloat {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-5px);
          }
        }

        @keyframes origamiPhoenixWingBeat {
          0%, 100% {
            transform: translateY(0) rotateZ(0deg);
          }
          50% {
            transform: translateY(-8px) rotateZ(-12deg);
          }
        }

        @keyframes origamiPhoenixTailFlow {
          0%, 100% {
            transform: translateY(0) rotateZ(0deg) scaleY(1);
          }
          50% {
            transform: translateY(5px) rotateZ(8deg) scaleY(1.1);
          }
        }

        @keyframes origamiPhoenixCrownFlicker {
          0%, 100% {
            opacity: 0.8;
            transform: scaleY(1);
          }
          50% {
            opacity: 1;
            transform: scaleY(1.15);
          }
        }

        /* Koi Fish animations */
        @keyframes origamiKoiSwim {
          0%, 100% {
            transform: translateX(0) translateY(0) rotateZ(0deg);
          }
          25% {
            transform: translateX(3px) translateY(-2px) rotateZ(2deg);
          }
          50% {
            transform: translateX(0) translateY(-4px) rotateZ(0deg);
          }
          75% {
            transform: translateX(-3px) translateY(-2px) rotateZ(-2deg);
          }
        }

        @keyframes origamiKoiFinWave {
          0%, 100% {
            transform: rotateZ(0deg) scaleY(1);
          }
          50% {
            transform: rotateZ(-5deg) scaleY(1.1);
          }
        }

        @keyframes origamiKoiTailFan {
          0%, 100% {
            transform: rotateZ(0deg) scaleX(1);
          }
          50% {
            transform: rotateZ(5deg) scaleX(1.15);
          }
        }

        /* Frog animations */
        @keyframes origamiFrogJump {
          0%, 80%, 100% {
            transform: translateY(0);
          }
          10% {
            transform: translateY(-8px);
          }
          20% {
            transform: translateY(-4px);
          }
        }

        @keyframes origamiFrogLeg {
          0%, 80%, 100% {
            transform: translateY(0) rotateZ(0deg);
          }
          10% {
            transform: translateY(-5px) rotateZ(-5deg);
          }
          20% {
            transform: translateY(-2px) rotateZ(-2deg);
          }
        }

        /* Elephant animations */
        @keyframes origamiTrunkSway {
          0%, 100% {
            transform: translateX(0) rotateZ(0deg);
          }
          50% {
            transform: translateX(3px) rotateZ(5deg);
          }
        }

        @keyframes origamiEarFlap {
          0%, 100% {
            transform: rotateZ(0deg);
          }
          50% {
            transform: rotateZ(8deg);
          }
        }

        /* Swan animations */
        @keyframes origamiSwanNeck {
          0%, 100% {
            transform: translateX(0);
          }
          50% {
            transform: translateX(-2px);
          }
        }

        @keyframes origamiWingGlide {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-4px);
          }
        }

        /* Unicorn animations */
        @keyframes origamiHornGlow {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.05);
          }
        }

        @keyframes origamiManeFlow {
          0%, 100% {
            transform: translateY(0) rotateZ(0deg);
          }
          50% {
            transform: translateY(-2px) rotateZ(-3deg);
          }
        }

        @keyframes origamiTailFlow {
          0%, 100% {
            transform: translateY(0) rotateZ(0deg);
          }
          50% {
            transform: translateY(2px) rotateZ(5deg);
          }
        }

        /* Modern origami animations */

        /* Car animations */
        @keyframes origamiCarBounce {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-3px);
          }
        }

        @keyframes origamiWheelSpin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        /* Plane animations */
        @keyframes origamiPlaneFly {
          0%, 100% {
            transform: translateY(0) translateX(0);
          }
          50% {
            transform: translateY(-5px) translateX(3px);
          }
        }

        @keyframes origamiWingTilt {
          0%, 100% {
            transform: rotateZ(0deg);
          }
          50% {
            transform: rotateZ(-5deg);
          }
        }

        /* Rocket animations */
        @keyframes origamiRocketLaunch {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-8px);
          }
        }

        @keyframes origamiFlameFlicker {
          0%, 100% {
            opacity: 0.8;
            transform: scaleY(1);
          }
          50% {
            opacity: 1;
            transform: scaleY(1.2);
          }
        }

        /* Camera animations */
        @keyframes origamiLensFocus {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.05);
          }
        }

        @keyframes origamiFlashBlink {
          0%, 90%, 100% {
            opacity: 0.6;
          }
          95% {
            opacity: 1;
          }
        }

        /* Robot animations */
        @keyframes origamiRobotNod {
          0%, 100% {
            transform: translateY(0) rotateX(0deg);
          }
          50% {
            transform: translateY(2px) rotateX(2deg);
          }
        }

        @keyframes origamiAntennaBlink {
          0%, 80%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          90% {
            opacity: 0.5;
            transform: scale(1.2);
          }
        }

        @keyframes origamiEyeBlink {
          0%, 90%, 100% {
            transform: scaleY(1);
          }
          95% {
            transform: scaleY(0.1);
          }
        }

        @keyframes origamiRobotArmWave {
          0%, 100% {
            transform: rotateZ(0deg);
          }
          50% {
            transform: rotateZ(10deg);
          }
        }

        /* Laptop animations */
        @keyframes origamiScreenGlow {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.95;
          }
        }

        @keyframes origamiCursorBlink {
          0%, 49%, 100% {
            opacity: 1;
          }
          50%, 99% {
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}
