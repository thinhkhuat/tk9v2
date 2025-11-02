/**
 * Origami Shapes Library for TK9 Waiting Experience
 *
 * 20 sophisticated, well-crafted origami shapes with SVG path definitions.
 * Adapted from PlayfulLoadingAnimation.tsx with academic-aesthetic refinement.
 *
 * Categories:
 * - Traditional Origami (14 shapes): Crane, Boat, Butterfly, Star, Angelfish, Fox, Dragon, Phoenix, Koi, Samurai Helmet, Frog, Elephant, Swan, Unicorn
 * - Modern Tech-Inspired (6 shapes): Car, Plane, Rocket, Camera, Robot, Laptop
 *
 * Reference: docs/code-samples/PlayfulLoadingAnimation.tsx
 */

import type { OrigamiShape } from './types'

// ============================================================================
// Traditional Origami Shapes (14 shapes)
// ============================================================================

export const origamiCrane: OrigamiShape = {
  name: 'Crane',
  category: 'traditional',
  paths: [
    // Body - central diamond
    { d: 'M100,50 140,100 100,140 60,100 Z', fill: 'primary', opacity: 1 },
    // Left wing
    { d: 'M100,100 40,80 60,100 Z', fill: 'primary', opacity: 0.8 },
    // Right wing
    { d: 'M100,100 160,80 140,100 Z', fill: 'primary', opacity: 0.8 },
    // Head
    { d: 'M100,50 90,35 100,40 Z', fill: 'secondary', opacity: 1 },
    // Tail
    { d: 'M100,140 100,160 95,150 Z', fill: 'secondary', opacity: 1 }
  ]
}

export const origamiBoat: OrigamiShape = {
  name: 'Boat',
  category: 'traditional',
  paths: [
    // Hull
    { d: 'M70,120 130,120 110,150 90,150 Z', fill: 'primary', opacity: 1 },
    // Sail
    { d: 'M100,60 70,120 130,120 Z', fill: 'primary', opacity: 0.9 }
  ]
}

export const origamiButterfly: OrigamiShape = {
  name: 'Butterfly',
  category: 'traditional',
  paths: [
    // Left wing top
    { d: 'M70,80 Q35,60 35,80 Q35,100 70,100 Q105,90 70,80', fill: 'primary', opacity: 1 },
    // Left wing bottom
    { d: 'M75,120 Q45,105 45,120 Q45,135 75,135 Q105,127 75,120', fill: 'primary', opacity: 0.85 },
    // Right wing top
    { d: 'M130,80 Q165,60 165,80 Q165,100 130,100 Q95,90 130,80', fill: 'primary', opacity: 1 },
    // Right wing bottom
    { d: 'M125,120 Q155,105 155,120 Q155,135 125,135 Q95,127 125,120', fill: 'primary', opacity: 0.85 },
    // Body
    { d: 'M100,50 Q108,75 108,100 Q108,125 100,150 Q92,125 92,100 Q92,75 100,50', fill: 'secondary', opacity: 1 }
  ]
}

export const origamiStar: OrigamiShape = {
  name: 'Star',
  category: 'traditional',
  paths: [
    // 5-pointed star
    { d: 'M100,40 115,80 160,85 125,115 135,160 100,135 65,160 75,115 40,85 85,80 Z', fill: 'primary', opacity: 1 },
    // Inner accent
    { d: 'M100,70 110,95 125,100 110,110 100,130 90,110 75,100 90,95 Z', fill: 'accent', opacity: 0.6 }
  ]
}

export const origamiAngelfish: OrigamiShape = {
  name: 'Angelfish',
  category: 'traditional',
  paths: [
    // Main body
    { d: 'M100,60 Q120,80 125,100 Q120,120 100,140 Q80,120 75,100 Q80,80 100,60', fill: 'primary', opacity: 1 },
    // Dorsal fin
    { d: 'M90,65 Q85,40 90,30 Q95,25 100,30 Q105,40 100,65 Z', fill: 'primary', opacity: 0.9 },
    // Ventral fin
    { d: 'M90,135 Q85,160 90,170 Q95,175 100,170 Q105,160 100,135 Z', fill: 'primary', opacity: 0.9 },
    // Pectoral fins
    { d: 'M105,90 Q120,85 125,90 Q120,95 110,100 Z', fill: 'secondary', opacity: 0.85 },
    { d: 'M105,110 Q120,115 125,110 Q120,105 110,100 Z', fill: 'secondary', opacity: 0.85 },
    // Tail fin
    { d: 'M75,100 Q65,95 55,95 L60,100 L55,105 Q65,105 75,100 Z', fill: 'primary', opacity: 0.9 }
  ]
}

export const origamiFox: OrigamiShape = {
  name: 'Fox',
  category: 'traditional',
  paths: [
    // Left ear
    { d: 'M70,60 50,90 85,90 Z', fill: 'primary', opacity: 1 },
    // Right ear
    { d: 'M130,60 150,90 115,90 Z', fill: 'primary', opacity: 1 },
    // Face
    { d: 'M100,90 70,120 130,120 Z', fill: 'primary', opacity: 1 },
    // Snout
    { d: 'M100,120 85,135 115,135 Z', fill: 'secondary', opacity: 0.8 }
  ]
}

export const origamiDragon: OrigamiShape = {
  name: 'Dragon',
  category: 'traditional',
  paths: [
    // Body
    { d: 'M60,120 Q70,100 90,95 Q110,90 130,100 Q140,110 135,125 Z', fill: 'primary', opacity: 1 },
    // Neck and head
    { d: 'M130,100 Q145,85 150,70 L155,65 L150,60 L145,65 Z', fill: 'primary', opacity: 1 },
    // Left wing
    { d: 'M95,95 Q80,70 70,55 L75,60 Q85,75 95,90 Z', fill: 'primary', opacity: 0.85 },
    // Right wing
    { d: 'M115,95 Q130,70 140,55 L135,60 Q125,75 115,90 Z', fill: 'primary', opacity: 0.85 },
    // Tail
    { d: 'M60,120 Q45,130 35,145 L40,140 Q50,130 58,122 Z', fill: 'secondary', opacity: 1 }
  ]
}

export const origamiPhoenix: OrigamiShape = {
  name: 'Phoenix',
  category: 'traditional',
  paths: [
    // Tail feathers - layer 1
    { d: 'M100,130 Q80,145 70,165 Q75,160 85,150 Z', fill: 'primary', opacity: 0.85 },
    { d: 'M100,130 Q100,150 95,175 Q98,168 100,155 Z', fill: 'primary', opacity: 0.85 },
    { d: 'M100,130 Q120,145 130,165 Q125,160 115,150 Z', fill: 'primary', opacity: 0.85 },
    // Tail feathers - layer 2
    { d: 'M98,125 Q85,135 80,150 Q85,145 92,138 Z', fill: 'primary', opacity: 0.75 },
    { d: 'M102,125 Q115,135 120,150 Q115,145 108,138 Z', fill: 'primary', opacity: 0.75 },
    // Body
    { d: 'M100,75 Q78,90 78,105 Q78,120 100,135 Q122,120 122,105 Q122,90 100,75', fill: 'primary', opacity: 1 },
    // Wings - left upper
    { d: 'M85,100 Q60,85 45,80 Q50,88 65,95 Z', fill: 'primary', opacity: 0.9 },
    // Wings - left lower
    { d: 'M85,110 Q65,105 50,105 Q58,110 72,115 Z', fill: 'primary', opacity: 0.85 },
    // Wings - right upper
    { d: 'M115,100 Q140,85 155,80 Q150,88 135,95 Z', fill: 'primary', opacity: 0.9 },
    // Wings - right lower
    { d: 'M115,110 Q135,105 150,105 Q142,110 128,115 Z', fill: 'primary', opacity: 0.85 },
    // Head and crown
    { d: 'M94,62 Q92,52 95,48 L97,52 L100,45 L103,52 L105,48 Q108,52 105,62 Z', fill: 'secondary', opacity: 1 }
  ]
}

export const origamiKoi: OrigamiShape = {
  name: 'Koi Fish',
  category: 'traditional',
  paths: [
    // Body
    { d: 'M50,100 Q60,85 80,80 Q110,75 130,85 Q145,95 150,110 Q145,125 130,130 Q100,135 70,125 Q55,115 50,100 Z', fill: 'primary', opacity: 1 },
    // Head detail
    { d: 'M145,102 Q153,97 153,102 Q153,107 145,102', fill: 'secondary', opacity: 0.9 },
    // Dorsal fin
    { d: 'M95,75 Q95,60 100,55 Q105,60 105,75 Z', fill: 'primary', opacity: 0.85 },
    // Pectoral fin
    { d: 'M115,110 Q125,120 120,130 Q115,125 115,115 Z', fill: 'secondary', opacity: 0.8 },
    // Tail fan
    { d: 'M50,100 Q35,90 25,85 L30,95 Q40,100 30,105 L25,115 Q35,110 50,100 Z', fill: 'primary', opacity: 0.9 }
  ]
}

export const origamiSamuraiHelmet: OrigamiShape = {
  name: 'Samurai Helmet',
  category: 'traditional',
  paths: [
    // Main body
    { d: 'M100,50 60,120 140,120 Z', fill: 'primary', opacity: 1 },
    // Left horn
    { d: 'M70,90 Q50,70 40,50 L45,55 Q60,75 72,95 Z', fill: 'primary', opacity: 0.9 },
    // Right horn
    { d: 'M130,90 Q150,70 160,50 L155,55 Q140,75 128,95 Z', fill: 'primary', opacity: 0.9 },
    // Left neck guard
    { d: 'M60,120 50,140 70,135 Z', fill: 'secondary', opacity: 0.85 },
    // Right neck guard
    { d: 'M140,120 150,140 130,135 Z', fill: 'secondary', opacity: 0.85 }
  ]
}

export const origamiFrog: OrigamiShape = {
  name: 'Frog',
  category: 'traditional',
  paths: [
    // Body
    { d: 'M100,80 Q60,95 60,110 Q60,125 100,140 Q140,125 140,110 Q140,95 100,80', fill: 'primary', opacity: 1 },
    // Head
    { d: 'M100,55 Q65,60 65,80 Q65,100 100,105 Q135,100 135,80 Q135,60 100,55', fill: 'primary', opacity: 1 },
    // Left eye
    { d: 'M85,75 Q75,70 75,75 Q75,80 85,85 Q95,80 95,75 Q95,70 85,75', fill: 'secondary', opacity: 1 },
    // Right eye
    { d: 'M115,75 Q105,70 105,75 Q105,80 115,85 Q125,80 125,75 Q125,70 115,75', fill: 'secondary', opacity: 1 }
  ]
}

export const origamiElephant: OrigamiShape = {
  name: 'Elephant',
  category: 'traditional',
  paths: [
    // Body
    { d: 'M110,70 Q65,85 65,110 Q65,135 110,150 Q155,135 155,110 Q155,85 110,70', fill: 'primary', opacity: 1 },
    // Head
    { d: 'M90,57 Q62,60 62,85 Q62,110 90,113 Q118,110 118,85 Q118,60 90,57', fill: 'primary', opacity: 1 },
    // Trunk
    { d: 'M90,110 Q75,125 70,145 Q68,155 75,158 Z', fill: 'secondary', opacity: 1 },
    // Left ear
    { d: 'M65,85 Q45,70 45,85 Q45,100 65,115 Q85,100 65,85', fill: 'primary', opacity: 0.85 },
    // Right ear
    { d: 'M115,85 Q135,70 135,85 Q135,100 115,115 Q95,100 115,85', fill: 'primary', opacity: 0.85 }
  ]
}

export const origamiSwan: OrigamiShape = {
  name: 'Swan',
  category: 'traditional',
  paths: [
    // Body
    { d: 'M120,90 Q80,105 80,120 Q80,135 120,150 Q160,135 160,120 Q160,105 120,90', fill: 'primary', opacity: 1 },
    // Neck - S-curve
    { d: 'M90,110 Q70,95 70,75 Q70,60 80,50', fill: 'secondary', opacity: 1 },
    // Head
    { d: 'M80,45 Q72,40 72,45 Q72,50 80,55 Q88,50 88,45 Q88,40 80,45', fill: 'primary', opacity: 1 },
    // Wing upper
    { d: 'M120,105 Q135,95 145,90 Q140,100 130,110 Z', fill: 'primary', opacity: 0.85 },
    // Wing lower
    { d: 'M125,115 Q140,110 150,108 Q145,118 135,125 Z', fill: 'primary', opacity: 0.75 },
    // Tail feathers
    { d: 'M160,125 L170,130 L165,120 Z', fill: 'secondary', opacity: 1 }
  ]
}

export const origamiUnicorn: OrigamiShape = {
  name: 'Unicorn',
  category: 'traditional',
  paths: [
    // Body
    { d: 'M120,80 Q75,95 75,115 Q75,135 120,150 Q165,135 165,115 Q165,95 120,80', fill: 'primary', opacity: 1 },
    // Neck
    { d: 'M85,105 Q75,90 75,75', fill: 'secondary', opacity: 1 },
    // Head
    { d: 'M75,65 Q60,62 60,65 Q60,68 75,83 Q90,68 90,65 Q90,62 75,65', fill: 'primary', opacity: 1 },
    // Horn
    { d: 'M75,50 L73,35 L75,38 L77,35 Z', fill: 'accent', opacity: 1 },
    // Mane flow 1
    { d: 'M78,60 Q90,55 95,50 Z', fill: 'secondary', opacity: 0.8 },
    // Mane flow 2
    { d: 'M80,68 Q92,65 98,62 Z', fill: 'secondary', opacity: 0.7 },
    // Mane flow 3
    { d: 'M82,76 Q94,75 100,74 Z', fill: 'secondary', opacity: 0.6 },
    // Tail
    { d: 'M165,115 Q175,120 180,130 Z', fill: 'secondary', opacity: 0.8 }
  ]
}

// ============================================================================
// Modern Tech-Inspired Shapes (6 shapes)
// ============================================================================

export const origamiCar: OrigamiShape = {
  name: 'Car',
  category: 'modern',
  paths: [
    // Body - rounded rect
    { d: 'M60,110 L140,110 Q145,110 145,115 L145,135 Q145,140 140,140 L60,140 Q55,140 55,135 L55,115 Q55,110 60,110', fill: 'primary', opacity: 1 },
    // Cabin/roof
    { d: 'M75,110 L85,85 L115,85 L125,110 Z', fill: 'primary', opacity: 0.9 },
    // Windshield
    { d: 'M80,105 L88,90 L112,90 L120,105 Z', fill: 'accent', opacity: 0.6 }
  ]
}

export const origamiPlane: OrigamiShape = {
  name: 'Plane',
  category: 'modern',
  paths: [
    // Fuselage
    { d: 'M50,100 L140,100 L160,110 L150,100 L160,90 L140,100 Z', fill: 'primary', opacity: 1 },
    // Left wing
    { d: 'M90,100 60,70 80,95 Z', fill: 'primary', opacity: 0.9 },
    // Right wing
    { d: 'M90,100 60,130 80,105 Z', fill: 'primary', opacity: 0.9 },
    // Tail wing top
    { d: 'M50,100 40,85 45,95 Z', fill: 'secondary', opacity: 0.8 },
    // Tail wing bottom
    { d: 'M50,100 40,115 45,105 Z', fill: 'secondary', opacity: 0.8 }
  ]
}

export const origamiRocket: OrigamiShape = {
  name: 'Rocket',
  category: 'modern',
  paths: [
    // Body
    { d: 'M85,70 L115,70 L115,140 L85,140 Z', fill: 'primary', opacity: 1 },
    // Nose cone
    { d: 'M100,40 85,70 115,70 Z', fill: 'primary', opacity: 1 },
    // Left fin
    { d: 'M85,120 70,140 85,135 Z', fill: 'secondary', opacity: 0.85 },
    // Right fin
    { d: 'M115,120 130,140 115,135 Z', fill: 'secondary', opacity: 0.85 },
    // Window
    { d: 'M100,85 Q92,85 92,85 Q92,85 100,93 Q108,85 108,85 Q108,85 100,85', fill: 'accent', opacity: 0.6 },
    // Flame left
    { d: 'M90,140 L85,155 L90,148 L85,160 Z', fill: 'accent', opacity: 0.8 },
    // Flame center
    { d: 'M100,140 L100,165 Z', fill: 'accent', opacity: 0.8 },
    // Flame right
    { d: 'M110,140 L115,155 L110,148 L115,160 Z', fill: 'accent', opacity: 0.8 }
  ]
}

export const origamiCamera: OrigamiShape = {
  name: 'Camera',
  category: 'modern',
  paths: [
    // Body
    { d: 'M70,90 L130,90 Q135,90 135,95 L135,130 Q135,135 130,135 L70,135 Q65,135 65,130 L65,95 Q65,90 70,90', fill: 'primary', opacity: 1 },
    // Lens outer
    { d: 'M100,112 Q82,112 82,112 Q82,112 100,130 Q118,112 118,112 Q118,112 100,112', fill: 'accent', opacity: 0.8 },
    // Lens middle
    { d: 'M100,112 Q88,112 88,112 Q88,112 100,124 Q112,112 112,112 Q112,112 100,112', fill: 'accent', opacity: 0.7 },
    // Flash
    { d: 'M115,92 L125,92 Q127,92 127,94 L127,98 Q127,100 125,100 L115,100 Q113,100 113,98 L113,94 Q113,92 115,92', fill: 'secondary', opacity: 1 },
    // Viewfinder
    { d: 'M75,92 L83,92 Q84,92 84,93 L84,97 Q84,98 83,98 L75,98 Q74,98 74,97 L74,93 Q74,92 75,92', fill: 'accent', opacity: 0.7 }
  ]
}

export const origamiRobot: OrigamiShape = {
  name: 'Robot',
  category: 'modern',
  paths: [
    // Head
    { d: 'M80,60 L120,60 Q125,60 125,65 L125,90 Q125,95 120,95 L80,95 Q75,95 75,90 L75,65 Q75,60 80,60', fill: 'primary', opacity: 1 },
    // Antenna
    { d: 'M100,60 L100,45 M100,45 Q96,45 96,45 Q96,45 100,49 Q104,45 104,45 Q104,45 100,45', fill: 'secondary', opacity: 1 },
    // Body
    { d: 'M75,95 L125,95 Q130,95 130,100 L130,130 Q130,135 125,135 L75,135 Q70,135 70,130 L70,100 Q70,95 75,95', fill: 'primary', opacity: 1 },
    // Left eye
    { d: 'M87,70 L95,70 L95,78 L87,78 Z', fill: 'accent', opacity: 1 },
    // Right eye
    { d: 'M105,70 L113,70 L113,78 L105,78 Z', fill: 'accent', opacity: 1 },
    // Mouth
    { d: 'M92,85 L108,85 L108,89 L92,89 Z', fill: 'accent', opacity: 1 },
    // Left arm
    { d: 'M60,100 L75,100 L75,130 L60,130 Z', fill: 'secondary', opacity: 0.85 },
    // Right arm
    { d: 'M125,100 L140,100 L140,130 L125,130 Z', fill: 'secondary', opacity: 0.85 }
  ]
}

export const origamiLaptop: OrigamiShape = {
  name: 'Laptop',
  category: 'modern',
  paths: [
    // Keyboard base
    { d: 'M60,120 L140,120 L145,140 L55,140 Z', fill: 'primary', opacity: 1 },
    // Trackpad
    { d: 'M85,132 L115,132 Q116,132 116,133 L116,137 Q116,138 115,138 L85,138 Q84,138 84,137 L84,133 Q84,132 85,132', fill: 'accent', opacity: 0.5 },
    // Screen
    { d: 'M65,70 L135,70 Q138,70 138,73 L138,117 Q138,120 135,120 L65,120 Q62,120 62,117 L62,73 Q62,70 65,70', fill: 'primary', opacity: 1 },
    // Display area
    { d: 'M70,75 L130,75 L130,115 L70,115 Z', fill: 'accent', opacity: 0.6 },
    // Code lines (simplified as single path)
    { d: 'M75,82 L110,82 M75,87 L120,87 M75,92 L105,92 M75,97 L125,97 M75,102 L115,102', fill: 'secondary', opacity: 0.5 },
    // Cursor
    { d: 'M115,100 L117,100 L117,104 L115,104 Z', fill: 'secondary', opacity: 1 }
  ]
}

// ============================================================================
// Master Shape Collection
// ============================================================================

/**
 * All 20 origami shapes for Phase 1
 */
export const allOrigamiShapes: OrigamiShape[] = [
  // Traditional (14)
  origamiCrane,
  origamiBoat,
  origamiButterfly,
  origamiStar,
  origamiAngelfish,
  origamiFox,
  origamiDragon,
  origamiPhoenix,
  origamiKoi,
  origamiSamuraiHelmet,
  origamiFrog,
  origamiElephant,
  origamiSwan,
  origamiUnicorn,
  // Modern (6)
  origamiCar,
  origamiPlane,
  origamiRocket,
  origamiCamera,
  origamiRobot,
  origamiLaptop
]

/**
 * Get shape by index (0-19)
 */
export function getShapeByIndex(index: number): OrigamiShape {
  return allOrigamiShapes[index % allOrigamiShapes.length]!
}

/**
 * Get shapes by category
 */
export function getShapesByCategory(category: 'traditional' | 'modern' | 'research'): OrigamiShape[] {
  return allOrigamiShapes.filter(shape => shape.category === category)
}

/**
 * Total shape count
 */
export const TOTAL_SHAPES = allOrigamiShapes.length
