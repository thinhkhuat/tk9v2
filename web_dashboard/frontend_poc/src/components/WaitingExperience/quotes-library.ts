/**
 * Famous Quotes Library for TK9 Waiting Experience
 *
 * 70 curated quotes organized by research stage, providing intellectual
 * engagement and contemplation during research execution.
 *
 * Quote Selection Criteria:
 * - Knowledge, research, learning, discovery, or wisdom-themed
 * - From renowned scientists, researchers, philosophers, writers
 * - Appropriate for professional/academic context
 * - Inspiring yet grounded (not motivational fluff)
 * - 50-120 characters (readable but substantive)
 *
 * Rotation Strategy: 10-second intervals within current stage
 *
 * Reference: docs/ux-design-specification.md Section 2.2
 */

import type { Quote, ResearchStage } from './types'

// ============================================================================
// Stage 1: Initial Research (15 quotes)
// Theme: Discovery & Exploration - Curiosity, questioning, the beginning
// ============================================================================

export const stage1Quotes: Quote[] = [
  {
    text: "I have no special talent. I am only passionately curious.",
    author: "Albert Einstein",
    stage: 1
  },
  {
    text: "The important thing is not to stop questioning. Curiosity has its own reason for existing.",
    author: "Albert Einstein",
    stage: 1
  },
  {
    text: "Judge a man by his questions rather than his answers.",
    author: "Voltaire",
    stage: 1
  },
  {
    text: "The art and science of asking questions is the source of all knowledge.",
    author: "Thomas Berger",
    stage: 1
  },
  {
    text: "Research is formalized curiosity. It is poking and prying with a purpose.",
    author: "Zora Neale Hurston",
    stage: 1
  },
  {
    text: "Wonder is the beginning of wisdom.",
    author: "Socrates",
    stage: 1
  },
  {
    text: "The larger the island of knowledge, the longer the shoreline of wonder.",
    author: "Ralph W. Sockman",
    stage: 1
  },
  {
    text: "Somewhere, something incredible is waiting to be known.",
    author: "Carl Sagan",
    stage: 1
  },
  {
    text: "The cure for boredom is curiosity. There is no cure for curiosity.",
    author: "Dorothy Parker",
    stage: 1
  },
  {
    text: "To raise new questions requires creative imagination and marks real advance in science.",
    author: "Albert Einstein",
    stage: 1
  },
  {
    text: "I would rather have questions that can't be answered than answers that can't be questioned.",
    author: "Richard Feynman",
    stage: 1
  },
  {
    text: "He who asks a question is a fool for five minutes; he who does not ask remains a fool forever.",
    author: "Chinese Proverb",
    stage: 1
  },
  {
    text: "The scientist is not a person who gives the right answers, he's one who asks the right questions.",
    author: "Claude Lévi-Strauss",
    stage: 1
  },
  {
    text: "Every great advance in science has issued from a new audacity of imagination.",
    author: "John Dewey",
    stage: 1
  },
  {
    text: "The beginning of knowledge is the discovery of something we do not understand.",
    author: "Frank Herbert",
    stage: 1
  }
]

// ============================================================================
// Stage 2: Planning (15 quotes)
// Theme: Strategy & Methodology - Preparation, structure, thoughtful approach
// ============================================================================

export const stage2Quotes: Quote[] = [
  {
    text: "By failing to prepare, you are preparing to fail.",
    author: "Benjamin Franklin",
    stage: 2
  },
  {
    text: "A goal without a plan is just a wish.",
    author: "Antoine de Saint-Exupéry",
    stage: 2
  },
  {
    text: "Give me six hours to chop down a tree and I will spend the first four sharpening the axe.",
    author: "Abraham Lincoln",
    stage: 2
  },
  {
    text: "It is not enough to do your best; you must know what to do, and then do your best.",
    author: "W. Edwards Deming",
    stage: 2
  },
  {
    text: "Strategy without tactics is the slowest route to victory. Tactics without strategy is the noise before defeat.",
    author: "Sun Tzu",
    stage: 2
  },
  {
    text: "In preparing for battle I have always found that plans are useless, but planning is indispensable.",
    author: "Dwight D. Eisenhower",
    stage: 2
  },
  {
    text: "Research is what I'm doing when I don't know what I'm doing.",
    author: "Wernher von Braun",
    stage: 2
  },
  {
    text: "The method of the enterprising is to plan with audacity and execute with vigor.",
    author: "Christian Nestell Bovee",
    stage: 2
  },
  {
    text: "Good fortune is what happens when opportunity meets with planning.",
    author: "Thomas Edison",
    stage: 2
  },
  {
    text: "Well begun is half done.",
    author: "Aristotle",
    stage: 2
  },
  {
    text: "First comes thought; then organization of that thought into ideas and plans.",
    author: "Napoleon Hill",
    stage: 2
  },
  {
    text: "An hour of planning can save you 10 hours of doing.",
    author: "Dale Carnegie",
    stage: 2
  },
  {
    text: "Plans are of little importance, but planning is essential.",
    author: "Winston Churchill",
    stage: 2
  },
  {
    text: "If you don't know where you are going, you'll end up someplace else.",
    author: "Yogi Berra",
    stage: 2
  },
  {
    text: "Structure is not the enemy of creativity.",
    author: "Julia Cameron",
    stage: 2
  }
]

// ============================================================================
// Stage 3: Parallel Research (20 quotes)
// Theme: Depth & Synthesis - Deep investigation, connecting ideas, complexity
// ============================================================================

export const stage3Quotes: Quote[] = [
  {
    text: "The whole is greater than the sum of its parts.",
    author: "Aristotle",
    stage: 3
  },
  {
    text: "Science is organized knowledge. Wisdom is organized life.",
    author: "Immanuel Kant",
    stage: 3
  },
  {
    text: "In the middle of difficulty lies opportunity.",
    author: "Albert Einstein",
    stage: 3
  },
  {
    text: "It is the mark of an educated mind to be able to entertain a thought without accepting it.",
    author: "Aristotle",
    stage: 3
  },
  {
    text: "Truth is ever to be found in simplicity, and not in the multiplicity and confusion of things.",
    author: "Isaac Newton",
    stage: 3
  },
  {
    text: "The more I read, the more I acquire, the more certain I am that I know nothing.",
    author: "Voltaire",
    stage: 3
  },
  {
    text: "Reading furnishes the mind only with materials of knowledge; it is thinking that makes what we read ours.",
    author: "John Locke",
    stage: 3
  },
  {
    text: "An investment in knowledge pays the best interest.",
    author: "Benjamin Franklin",
    stage: 3
  },
  {
    text: "The only thing that interferes with my learning is my education.",
    author: "Albert Einstein",
    stage: 3
  },
  {
    text: "We are drowning in information but starved for knowledge.",
    author: "John Naisbitt",
    stage: 3
  },
  {
    text: "Knowledge speaks, but wisdom listens.",
    author: "Jimi Hendrix",
    stage: 3
  },
  {
    text: "The beautiful thing about learning is that no one can take it away from you.",
    author: "B.B. King",
    stage: 3
  },
  {
    text: "I cannot teach anybody anything. I can only make them think.",
    author: "Socrates",
    stage: 3
  },
  {
    text: "The mind is not a vessel to be filled, but a fire to be kindled.",
    author: "Plutarch",
    stage: 3
  },
  {
    text: "To know that we know what we know, and to know that we do not know what we do not know, that is true knowledge.",
    author: "Nicolaus Copernicus",
    stage: 3
  },
  {
    text: "The greatest enemy of knowledge is not ignorance, it is the illusion of knowledge.",
    author: "Stephen Hawking",
    stage: 3
  },
  {
    text: "If we knew what we were doing, it wouldn't be called research.",
    author: "Albert Einstein",
    stage: 3
  },
  {
    text: "The more you know, the more you realize you don't know.",
    author: "Aristotle",
    stage: 3
  },
  {
    text: "Real knowledge is to know the extent of one's ignorance.",
    author: "Confucius",
    stage: 3
  },
  {
    text: "Truth is a fruit that can only be picked when it is very ripe.",
    author: "Voltaire",
    stage: 3
  }
]

// ============================================================================
// Stage 4: Writing (20 quotes)
// Theme: Synthesis & Communication - Clarity, distillation, sharing knowledge
// ============================================================================

export const stage4Quotes: Quote[] = [
  {
    text: "Writing is thinking. To write well is to think clearly. That's why it's so hard.",
    author: "David McCullough",
    stage: 4
  },
  {
    text: "The art of writing is the art of discovering what you believe.",
    author: "Gustave Flaubert",
    stage: 4
  },
  {
    text: "Clear thinking becomes clear writing; one can't exist without the other.",
    author: "William Zinsser",
    stage: 4
  },
  {
    text: "Either write something worth reading or do something worth writing.",
    author: "Benjamin Franklin",
    stage: 4
  },
  {
    text: "I write to discover what I know.",
    author: "Flannery O'Connor",
    stage: 4
  },
  {
    text: "The scariest moment is always just before you start.",
    author: "Stephen King",
    stage: 4
  },
  {
    text: "A writer is someone for whom writing is more difficult than it is for other people.",
    author: "Thomas Mann",
    stage: 4
  },
  {
    text: "Words are, of course, the most powerful drug used by mankind.",
    author: "Rudyard Kipling",
    stage: 4
  },
  {
    text: "If I had more time, I would have written a shorter letter.",
    author: "Blaise Pascal",
    stage: 4
  },
  {
    text: "The first draft is just you telling yourself the story.",
    author: "Terry Pratchett",
    stage: 4
  },
  {
    text: "You can make anything by writing.",
    author: "C.S. Lewis",
    stage: 4
  },
  {
    text: "Good writing is clear thinking made visible.",
    author: "Bill Wheeler",
    stage: 4
  },
  {
    text: "Write what should not be forgotten.",
    author: "Isabel Allende",
    stage: 4
  },
  {
    text: "The purpose of a writer is to keep civilization from destroying itself.",
    author: "Albert Camus",
    stage: 4
  },
  {
    text: "Writing is the painting of the voice.",
    author: "Voltaire",
    stage: 4
  },
  {
    text: "No tears in the writer, no tears in the reader.",
    author: "Robert Frost",
    stage: 4
  },
  {
    text: "Writing is an exploration. You start from nothing and learn as you go.",
    author: "E.L. Doctorow",
    stage: 4
  },
  {
    text: "The role of a writer is not to say what we can all say, but what we are unable to say.",
    author: "Anaïs Nin",
    stage: 4
  },
  {
    text: "The difference between the almost right word and the right word is really a large matter.",
    author: "Mark Twain",
    stage: 4
  },
  {
    text: "Easy reading is damn hard writing.",
    author: "Nathaniel Hawthorne",
    stage: 4
  }
]

// ============================================================================
// Combined Library & Helper Functions
// ============================================================================

/**
 * All 70 quotes combined into a single array
 */
export const allQuotes: Quote[] = [
  ...stage1Quotes,
  ...stage2Quotes,
  ...stage3Quotes,
  ...stage4Quotes
]

/**
 * Get quotes for a specific stage
 * @param stage - Research stage (1-4)
 * @returns Array of quotes for that stage
 */
export function getQuotesByStage(stage: ResearchStage): Quote[] {
  switch (stage) {
    case 1:
      return stage1Quotes
    case 2:
      return stage2Quotes
    case 3:
      return stage3Quotes
    case 4:
      return stage4Quotes
    default:
      return stage1Quotes
  }
}

/**
 * Get a random quote from a specific stage
 * @param stage - Research stage (1-4)
 * @returns Random quote from that stage
 */
export function getRandomQuote(stage: ResearchStage): Quote {
  const quotes = getQuotesByStage(stage)
  const randomIndex = Math.floor(Math.random() * quotes.length)
  return quotes[randomIndex]
}

/**
 * Quote statistics
 */
export const QUOTE_STATS = {
  stage1Count: stage1Quotes.length, // 15
  stage2Count: stage2Quotes.length, // 15
  stage3Count: stage3Quotes.length, // 20
  stage4Count: stage4Quotes.length, // 20
  totalCount: allQuotes.length       // 70
} as const

/**
 * Validate quote structure
 * @param quote - Quote to validate
 * @returns True if quote is valid
 */
export function isValidQuote(quote: Quote): boolean {
  return (
    typeof quote.text === 'string' &&
    quote.text.length >= 10 &&
    quote.text.length <= 250 &&
    typeof quote.author === 'string' &&
    quote.author.length > 0 &&
    [1, 2, 3, 4].includes(quote.stage)
  )
}

/**
 * Get expected quote count for stage timing
 * Based on UX specification Section 2.2:
 * - Stage 1 (30-90s): Users see 3-9 quotes
 * - Stage 2 (20-60s): Users see 2-6 quotes
 * - Stage 3 (60-120s): Users see 6-12 quotes
 * - Stage 4 (40-90s): Users see 4-9 quotes
 *
 * @param stage - Research stage
 * @param durationSeconds - Stage duration in seconds
 * @returns Expected number of quotes to display
 */
export function getExpectedQuoteCount(
  stage: ResearchStage,
  durationSeconds: number
): number {
  // Quotes rotate every 10 seconds
  const quoteRotationInterval = 10
  return Math.floor(durationSeconds / quoteRotationInterval)
}

/**
 * Export quote data for analytics
 * @returns Quote metadata for tracking
 */
export function exportQuoteMetadata() {
  return {
    totalQuotes: QUOTE_STATS.totalCount,
    stageBreakdown: {
      stage1: {
        count: QUOTE_STATS.stage1Count,
        theme: "Discovery & Exploration",
        examples: stage1Quotes.slice(0, 3).map(q => q.author)
      },
      stage2: {
        count: QUOTE_STATS.stage2Count,
        theme: "Strategy & Methodology",
        examples: stage2Quotes.slice(0, 3).map(q => q.author)
      },
      stage3: {
        count: QUOTE_STATS.stage3Count,
        theme: "Depth & Synthesis",
        examples: stage3Quotes.slice(0, 3).map(q => q.author)
      },
      stage4: {
        count: QUOTE_STATS.stage4Count,
        theme: "Synthesis & Communication",
        examples: stage4Quotes.slice(0, 3).map(q => q.author)
      }
    },
    authors: [...new Set(allQuotes.map(q => q.author))].length, // Unique authors
    createdAt: new Date().toISOString()
  }
}
