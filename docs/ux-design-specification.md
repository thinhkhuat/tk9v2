# TK9 - Deep Research Project UX Design Specification

_Created on 2025-11-01 by Thinh_
_Generated using BMad Method - Create UX Design Workflow v1.0_

---

## Executive Summary

TK9 is transforming from a single-session research tool into a comprehensive research workspace. This enhancement adds user authentication (anonymous + registered) and historical research access, enabling users to retrieve, browse, and compare all past research sessions while exploring the transparent multi-stage research process.

**Project Vision**: Enable researchers and knowledge workers to build knowledge over time through transparent, accessible research history with seamless authentication and progressive disclosure of the 4-stage research workflow (Initial Research → Planning → Parallel Research → Writing).

**Target Users**: Knowledge workers and researchers (ages 25-55) - product managers, strategy consultants, academic researchers, market analysts, and technical architects who conduct deep research and need to reference, compare, and build upon previous work.

**Platform**: Modern web application (Vue 3 + FastAPI + Supabase), mobile-responsive, designed for Chrome 90+, Firefox 88+, Safari 14+, Edge 90+.

**Key Experience Goals**:
- **Zero-friction entry** via anonymous authentication with seamless upgrade path
- **Transparent research methodology** through progressive disclosure UI (3-level collapsible accordion)
- **Comparison-optimized layout** enabling side-by-side exploration of multiple research sessions
- **Performance at scale** with virtual scrolling for 1000+ sessions and lazy loading

---

## 1. Design System Foundation

### 1.1 Design System Choice

**Selected Design System: Element Plus (Vue 3)**

TK9 uses **Element Plus** as its foundational design system. Element Plus is a mature, enterprise-grade Vue 3 UI component library that provides:

- 80+ high-quality components with consistent design language
- Built-in TypeScript support
- Full theme customization via CSS variables
- Accessibility-first approach (WCAG 2.1 AA compliant)
- Active maintenance and strong community support
- Comprehensive i18n support (50+ languages)

**Why Element Plus:**

1. **Vue 3 Native** - Built specifically for Vue 3 Composition API, no compatibility layers
2. **Existing Foundation** - Already integrated in TK9 dashboard, ensures visual consistency
3. **Flexible Theming** - CSS variable-based theming supports the 20 curated color palettes
4. **Production Ready** - Used by 1M+ projects, proven stability and performance
5. **Documentation Quality** - Comprehensive docs with live examples and API references

**Design System Documentation:** https://element-plus.org/

### 1.2 Typography System

**Font Families:**

```css
/* Primary: Inter (UI, body text, labels) */
--el-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;

/* Monospace: JetBrains Mono (code, technical details) */
--el-font-family-mono: 'JetBrains Mono', 'SF Mono', Monaco, Inconsolata, 'Courier New', monospace;

/* Quotes: Crimson Pro (serif for famous quotes display) */
--tk9-font-quotes: 'Crimson Pro', 'Georgia', 'Times New Roman', serif;
```

**Rationale:**
- **Inter** - Highly legible humanist sans-serif, optimized for screens at small sizes
- **JetBrains Mono** - Monospace with excellent ligatures for technical content
- **Crimson Pro** - Elegant serif that evokes academic sophistication for quote display

**Quote Display Typography:**

```css
.tk9-quote-text {
  font-family: var(--tk9-font-quotes);
  font-size: 18px;
  line-height: 1.6;
  font-weight: 400;
  font-style: italic;
  letter-spacing: 0.01em;
  color: var(--el-text-color-primary);
}

.tk9-quote-attribution {
  font-family: var(--el-font-family);
  font-size: 14px;
  line-height: 1.4;
  font-weight: 500;
  font-style: normal;
  letter-spacing: 0.02em;
  color: var(--el-text-color-secondary);
  opacity: 0.75;
}
```

**Type Scale (Element Plus default with TK9 extensions):**

| Level | Size | Line Height | Usage |
|-------|------|-------------|-------|
| H1 | 32px | 1.25 | Page titles |
| H2 | 24px | 1.33 | Section headers |
| H3 | 20px | 1.4 | Subsection headers |
| Body Large | 16px | 1.5 | Primary body text |
| Body | 14px | 1.5 | Secondary body text |
| Quote | 18px | 1.6 | Famous quotes display (NEW) |
| Caption | 12px | 1.33 | Metadata, timestamps |

### 1.3 Spacing & Layout System

**Spacing Scale (8px base unit):**

```css
--el-spacing-xs: 4px;   /* Tight */
--el-spacing-sm: 8px;   /* Compact */
--el-spacing-md: 16px;  /* Standard */
--el-spacing-lg: 24px;  /* Comfortable */
--el-spacing-xl: 32px;  /* Spacious */
--el-spacing-xxl: 48px; /* Generous */
```

**Origami Animation + Quotes Layout:**

```
┌─────────────────────────────────────────┐
│                                         │
│           [Origami Animation]           │  192px × 192px
│              192 × 192px                │  Center-aligned
│                                         │
├─────────────────────────────────────────┤
│                                         │
│      [24px vertical spacing]           │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  "Quote text in elegant Crimson Pro"   │  Max-width: 600px
│           — Attribution                 │  Center-aligned
│                                         │  Padding: 0 32px
│      [16px vertical spacing]           │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│       [Stage Progress Indicator]        │  Optional below quote
│           Stage 2 of 4                  │
│                                         │
└─────────────────────────────────────────┘
```

**Container Specifications:**

```css
.tk9-waiting-experience-container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: var(--el-spacing-xxl) var(--el-spacing-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.tk9-origami-animation {
  width: 192px;
  height: 192px;
  margin-bottom: var(--el-spacing-lg);
}

.tk9-quote-container {
  max-width: 600px;
  padding: 0 var(--el-spacing-xl);
  text-align: center;
  margin-bottom: var(--el-spacing-md);
}
```

### 1.4 Color Integration with Element Plus

**Element Plus Theme Integration:**

Element Plus uses CSS variables for theming, which perfectly supports the 20 curated color palettes from the origami animation system.

**Color System Structure:**

```css
/* Element Plus primary colors (dynamic, changes with palette) */
--el-color-primary: #409eff;        /* Origami shape primary color */
--el-color-primary-light-3: #79bbff;
--el-color-primary-light-5: #a0cfff;
--el-color-primary-light-7: #c6e2ff;
--el-color-primary-light-9: #ecf5ff;
--el-color-primary-dark-2: #337ecc;

/* TK9 quote display colors (static, high contrast) */
--tk9-quote-text: var(--el-text-color-primary);       /* High contrast for readability */
--tk9-quote-attribution: var(--el-text-color-secondary); /* Muted for hierarchy */
--tk9-quote-background: var(--el-bg-color-overlay);   /* Subtle elevation */
```

**20 Curated Color Palettes (from PlayfulLoadingAnimation):**

Each palette provides 2-3 harmonious colors for origami shapes. Examples:

1. **Oceanic Blues** - `#0891B2`, `#0EA5E9`, `#06B6D4`
2. **Forest Greens** - `#059669`, `#10B981`, `#34D399`
3. **Sunset Coral** - `#F97316`, `#FB923C`, `#FDBA74`
4. **Royal Purple** - `#7C3AED`, `#8B5CF6`, `#A78BFA`
5. **Cherry Blossom** - `#EC4899`, `#F472B6`, `#F9A8D4`
6. **Amber Gold** - `#D97706`, `#F59E0B`, `#FBBF24`
7. **Sky Blue** - `#0284C7`, `#0EA5E9`, `#38BDF8`
8. **Emerald Jewel** - `#047857`, `#059669`, `#10B981`
9. **Lavender Dream** - `#9333EA`, `#A855F7`, `#C084FC`
10. **Rose Garden** - `#E11D48`, `#F43F5E`, `#FB7185`

**[...10 more palettes]**

**Color Palette Rotation:**
- Each origami shape cycles through the 20 palettes in shuffled order
- Palette changes with each shape transition (every 3-6 seconds)
- Quote text remains high contrast (does NOT change color with palettes)
- Background adapts subtly to complement active palette

**Dark/Light Mode Support:**

Element Plus provides built-in dark mode via `<el-config-provider>`:

```vue
<el-config-provider :theme="isDarkMode ? 'dark' : 'light'">
  <WaitingExperience />
</el-config-provider>
```

**Dark Mode Adjustments:**
- Quote text: Automatically inverts to maintain WCAG AA contrast
- Origami colors: Slightly desaturated for reduced eye strain
- Background: Soft dark gradient instead of pure black
- Shadows: Lighter, more subtle in dark mode

### 1.5 Animation Principles

**Material Design Inspired (Google's Motion Guidelines):**

TK9's origami animation follows Material Design motion principles:

1. **Natural and Responsive** - Animations mirror physical paper folding
2. **Intentional** - Every motion serves a purpose (progress indication)
3. **Continuous** - Smooth transitions maintain spatial relationships
4. **Contextual** - Animation speed reflects research stage complexity

**Animation Performance:**

```css
/* CSS-based animations for 60fps performance */
.origami-shape {
  will-change: transform, opacity;
  transform: translateZ(0); /* GPU acceleration */
  backface-visibility: hidden; /* Prevent flickering */
}

/* Keyframe animations (from PlayfulLoadingAnimation) */
@keyframes origamiFold {
  0% { transform: rotateY(0deg) scale(1); }
  50% { transform: rotateY(90deg) scale(0.8); }
  100% { transform: rotateY(180deg) scale(1); }
}
```

**Accessibility - Reduced Motion:**

```css
@media (prefers-reduced-motion: reduce) {
  .origami-shape {
    animation: none !important;
    /* Fallback to gentle fade */
    animation: simpleFade 4s ease-in-out infinite;
  }

  @keyframes simpleFade {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
}
```

### 1.6 Element Plus Component Usage

**Components Used in Waiting Experience:**

1. **`<el-card>`** - Container for waiting experience (optional)
2. **`<el-progress>`** - Stage progress indicator (optional enhancement)
3. **`<el-text>`** - Quote display with semantic text styling
4. **`<el-space>`** - Consistent spacing between elements
5. **`<el-skeleton>`** - Loading state before animation initializes

**Example Component Structure:**

```vue
<template>
  <el-space direction="vertical" alignment="center" :size="24" class="tk9-waiting-container">
    <!-- Origami Animation -->
    <div class="tk9-origami-animation">
      <OrigamiShape
        :shape="currentShape"
        :palette="currentPalette"
        :speed="animationSpeed"
      />
    </div>

    <!-- Quote Display -->
    <el-space direction="vertical" alignment="center" :size="8" class="tk9-quote-container">
      <el-text class="tk9-quote-text" tag="blockquote">
        "{{ currentQuote.text }}"
      </el-text>
      <el-text class="tk9-quote-attribution" type="info">
        — {{ currentQuote.author }}
      </el-text>
    </el-space>

    <!-- Optional: Stage Progress -->
    <el-text type="info" size="small">
      Stage {{ currentStage }} of 4: {{ stageName }}
    </el-text>
  </el-space>
</template>
```

### 1.7 Technical Implementation Strategy

**Migration from React to Vue 3:**

The PlayfulLoadingAnimation.tsx source is React/TypeScript. Migration approach:

1. **SVG Shapes** - Copy 27 SVG definitions as-is (SVG is framework-agnostic)
2. **Animation Keyframes** - Copy 1907 lines of CSS keyframes directly
3. **State Management** - Convert React useState/useEffect to Vue ref/computed/watch
4. **Component Structure** - Adapt JSX to Vue SFC (Single File Component)

**File Structure:**

```
web_dashboard/frontend_poc/src/
  components/
    WaitingExperience/
      OrigamiAnimation.vue       # Main animation component (adapted from .tsx)
      QuoteDisplay.vue           # Quote rotation component
      WaitingExperience.vue      # Orchestrator component
      origami-shapes.ts          # SVG shape definitions (27 shapes)
      origami-animations.css     # CSS keyframes (1907 lines)
      color-palettes.ts          # 20 curated color palettes
      quotes-library.ts          # 70 stage-categorized quotes
      types.ts                   # TypeScript interfaces
```

**Key Adaptation Example:**

```typescript
// React (original)
const [currentIndex, setCurrentIndex] = useState(0)
useEffect(() => {
  const interval = setInterval(() => {
    setCurrentIndex((prev) => (prev + 1) % shapes.length)
  }, 4500)
  return () => clearInterval(interval)
}, [])

// Vue 3 (adapted)
const currentIndex = ref(0)
const rotationInterval = ref<number | null>(null)

onMounted(() => {
  rotationInterval.value = window.setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % shapes.length
  }, animationSpeed.value)
})

onUnmounted(() => {
  if (rotationInterval.value) clearInterval(rotationInterval.value)
})
```

**Dependencies:**

```json
{
  "element-plus": "^2.8.0",
  "@element-plus/icons-vue": "^2.3.0",
  "vue": "^3.4.0"
}
```

**Fonts (via Google Fonts CDN):**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
```

### 1.8 Accessibility Standards

**WCAG 2.1 AA Compliance:**

1. **Contrast Ratios**
   - Quote text: Minimum 4.5:1 contrast with background
   - Attribution: Minimum 3:1 contrast (secondary text)
   - Origami shapes: No contrast requirement (decorative)

2. **Motion Sensitivity**
   - Respects `prefers-reduced-motion` media query
   - Fallback to gentle fade animation (no rotation/scaling)

3. **Screen Reader Support**
   ```html
   <div role="status" aria-live="polite" aria-atomic="true">
     Research in progress: Stage 2 - Planning.
     "{{ currentQuote.text }}" by {{ currentQuote.author }}
   </div>
   ```

4. **Keyboard Navigation**
   - Animation container focusable with `tabindex="0"`
   - Allows keyboard users to verify research is progressing

5. **Color Independence**
   - Progress indication does NOT rely solely on color
   - Text labels supplement visual indicators

**Accessibility Testing Checklist:**
- [ ] axe DevTools audit passes with 0 violations
- [ ] VoiceOver (macOS) / NVDA (Windows) testing
- [ ] Keyboard-only navigation
- [ ] High contrast mode compatibility
- [ ] Browser zoom 200% layout integrity

---

---

## 2. Core User Experience

### 2.1 Defining Experience

**Core User Action:** Monitoring active research execution during the 3-5 minute processing period.

**The Experience:**
When a user initiates research, they enter a "waiting state" that lasts 3-5 minutes. During this time, the system processes through 4 distinct stages (Initial Research → Planning → Parallel Research → Writing). The core UX challenge is transforming this waiting period from a "blind, anxious state" into a "transparent, confident experience."

**User's Mental Model:**
"I want to see what's happening with my research RIGHT NOW. Show me which stage is running, what draft artifacts are being created, and reassure me that the system is working - not stuck or failing."

**Key Experience Principles:**

1. **Transparency Over Speed**
   - Users accept 3-5 minute execution time IF they can see progress
   - Near real-time visibility (2-5 second polling) is sufficient, literal real-time not required
   - Draft artifacts should appear as soon as they're available, not hidden until completion

2. **Stage-by-Stage Confidence**
   - Existing agent cards show which stage is currently active (✅ already implemented)
   - Visual indicators clearly show: queued → executing → completed for each stage
   - Users should never wonder "is it stuck or just processing?"

3. **Artifact Discovery During Wait**
   - As each stage completes, draft artifacts become visible
   - Users can preview/explore drafts WHILE waiting for final completion
   - Progressive disclosure: don't hide work-in-progress behind "please wait..."

4. **Reliable Output Delivery**
   - Research MUST complete successfully and produce files
   - No silent failures - if something breaks, user knows immediately
   - "I expect to actually get my research files" is the foundational promise

**Platform Context:**
- Web dashboard with polling mechanism (2-5s refresh intervals)
- Mobile-responsive for users who start research and check progress on phone
- Builds on existing agent card implementation with stage indicators

### 2.2 Novel UX Patterns

**Research Execution Waiting Experience: Origami Animation + Inspiring Quotes**

TK9 transforms the 3-5 minute research waiting period into a **contemplative, confidence-building experience** through a sophisticated origami animation system paired with rotating knowledge-inspired quotes.

**Design Philosophy:**
Rather than a generic loading spinner that induces anxiety, TK9 presents an elegant, academic-aesthetic experience that:
- **Reassures through motion** - Paper-folding animations prove the system is actively working
- **Inspires through wisdom** - Rotating quotes from renowned researchers, scientists, and thinkers
- **Engages through variety** - 25+ origami shapes × 20 color palettes = never repetitive
- **Adapts to progress** - Animation speed reflects stage complexity and completion

**Origami Shape Library (27 shapes total):**

*Traditional Origami (14 shapes):*
- Crane, Boat, Butterfly, Star, Angelfish, Fox, Dragon, Phoenix
- Koi Fish, Samurai Helmet, Frog, Elephant, Swan, Unicorn

*Modern Tech-Inspired (6 shapes):*
- Car, Plane, Rocket, Camera, Robot, Laptop

*Research-Themed (NEW - 7 shapes):*
- **Book** - Open pages with text lines, representing knowledge accumulation
- **Lightbulb** - Filament glowing, symbolizing insight and discovery
- **Telescope** - Lens focusing, representing exploration and observation
- **Brain** - Neural pathways, representing thinking and analysis
- **Magnifying Glass** - Lens detail, representing investigation
- **Scroll** - Ancient manuscript unrolling, representing historical research
- **Atom** - Orbiting electrons, representing scientific inquiry

**Stage-Specific Animation Behavior:**

| Stage | Duration | Animation Speed | Visual Metaphor |
|-------|----------|----------------|-----------------|
| **Stage 1: Initial Research** | 30-90s | 3s per shape | Fast cycling = active searching, rapid exploration |
| **Stage 2: Planning** | 20-60s | 4s per shape | Moderate pace = strategic thinking, organization |
| **Stage 3: Parallel Research** | 60-120s | 3.5s per shape | Balanced speed = multi-threaded processing |
| **Stage 4: Writing** | 40-90s | 6s per shape | Slow, thoughtful = composition, synthesis |

**Progress-Based Speed Adjustment:**
- **0-25% complete**: Base speed (stage-specific)
- **25-50% complete**: +10% faster (subtle acceleration)
- **50-75% complete**: +15% faster
- **75-95% complete**: +20% faster
- **95-100% complete**: +25% faster (nearing completion excitement)

**Example:** Stage 4 (Writing) starts at 6s per shape, accelerates to 4.5s per shape as it nears completion.

**Famous Quotes System:**

**Quote Selection Criteria:**
- Knowledge, research, learning, discovery, or wisdom-themed
- From renowned scientists, researchers, philosophers, writers
- Appropriate for professional/academic context
- Inspiring yet grounded (not motivational fluff)
- 50-120 characters (readable but substantive)

**Quote Rotation Strategy:**
**Selected: Option C - 10-second rotation (independent of shape cycling)**
- Provides balance between contemplative reading and variety
- Allows users to absorb wisdom without rushing
- Multiple quotes per stage create narrative progression
- Independent timing prevents overwhelming synchronization

**Stage-Categorized Quote Library:**

Each stage has its own curated quote collection that reflects the nature of that research phase. Quotes rotate every 10 seconds within the active stage.

---

### **Stage 1: Initial Research (30-90s) - Discovery & Exploration**
*Theme: Curiosity, asking questions, the beginning of knowledge*

1. **"I have no special talent. I am only passionately curious."** — Albert Einstein
2. **"The important thing is not to stop questioning. Curiosity has its own reason for existing."** — Albert Einstein
3. **"Judge a man by his questions rather than his answers."** — Voltaire
4. **"The art and science of asking questions is the source of all knowledge."** — Thomas Berger
5. **"Research is formalized curiosity. It is poking and prying with a purpose."** — Zora Neale Hurston
6. **"Wonder is the beginning of wisdom."** — Socrates
7. **"The larger the island of knowledge, the longer the shoreline of wonder."** — Ralph W. Sockman
8. **"Somewhere, something incredible is waiting to be known."** — Carl Sagan
9. **"The cure for boredom is curiosity. There is no cure for curiosity."** — Dorothy Parker
10. **"To raise new questions requires creative imagination and marks real advance in science."** — Albert Einstein
11. **"I would rather have questions that can't be answered than answers that can't be questioned."** — Richard Feynman
12. **"He who asks a question is a fool for five minutes; he who does not ask remains a fool forever."** — Chinese Proverb
13. **"The scientist is not a person who gives the right answers, he's one who asks the right questions."** — Claude Lévi-Strauss
14. **"Every great advance in science has issued from a new audacity of imagination."** — John Dewey
15. **"The beginning of knowledge is the discovery of something we do not understand."** — Frank Herbert

---

### **Stage 2: Planning (20-60s) - Strategy & Methodology**
*Theme: Preparation, structure, thoughtful approach, methodology*

1. **"By failing to prepare, you are preparing to fail."** — Benjamin Franklin
2. **"A goal without a plan is just a wish."** — Antoine de Saint-Exupéry
3. **"Give me six hours to chop down a tree and I will spend the first four sharpening the axe."** — Abraham Lincoln
4. **"It is not enough to do your best; you must know what to do, and then do your best."** — W. Edwards Deming
5. **"Strategy without tactics is the slowest route to victory. Tactics without strategy is the noise before defeat."** — Sun Tzu
6. **"In preparing for battle I have always found that plans are useless, but planning is indispensable."** — Dwight D. Eisenhower
7. **"Research is what I'm doing when I don't know what I'm doing."** — Wernher von Braun
8. **"The method of the enterprising is to plan with audacity and execute with vigor."** — Christian Nestell Bovee
9. **"Good fortune is what happens when opportunity meets with planning."** — Thomas Edison
10. **"Well begun is half done."** — Aristotle
11. **"First comes thought; then organization of that thought into ideas and plans."** — Napoleon Hill
12. **"An hour of planning can save you 10 hours of doing."** — Dale Carnegie
13. **"Plans are of little importance, but planning is essential."** — Winston Churchill
14. **"If you don't know where you are going, you'll end up someplace else."** — Yogi Berra
15. **"Structure is not the enemy of creativity."** — Julia Cameron

---

### **Stage 3: Parallel Research (60-120s) - Depth & Synthesis**
*Theme: Deep investigation, connecting ideas, multiple perspectives, complexity*

1. **"The whole is greater than the sum of its parts."** — Aristotle
2. **"Science is organized knowledge. Wisdom is organized life."** — Immanuel Kant
3. **"In the middle of difficulty lies opportunity."** — Albert Einstein
4. **"It is the mark of an educated mind to be able to entertain a thought without accepting it."** — Aristotle
5. **"Truth is ever to be found in simplicity, and not in the multiplicity and confusion of things."** — Isaac Newton
6. **"The more I read, the more I acquire, the more certain I am that I know nothing."** — Voltaire
7. **"Reading furnishes the mind only with materials of knowledge; it is thinking that makes what we read ours."** — John Locke
8. **"An investment in knowledge pays the best interest."** — Benjamin Franklin
9. **"The only thing that interferes with my learning is my education."** — Albert Einstein
10. **"We are drowning in information but starved for knowledge."** — John Naisbitt
11. **"Knowledge speaks, but wisdom listens."** — Jimi Hendrix
12. **"The beautiful thing about learning is that no one can take it away from you."** — B.B. King
13. **"I cannot teach anybody anything. I can only make them think."** — Socrates
14. **"The mind is not a vessel to be filled, but a fire to be kindled."** — Plutarch
15. **"To know that we know what we know, and to know that we do not know what we do not know, that is true knowledge."** — Nicolaus Copernicus
16. **"The greatest enemy of knowledge is not ignorance, it is the illusion of knowledge."** — Stephen Hawking
17. **"If we knew what we were doing, it wouldn't be called research."** — Albert Einstein
18. **"The more you know, the more you realize you don't know."** — Aristotle
19. **"Real knowledge is to know the extent of one's ignorance."** — Confucius
20. **"Truth is a fruit that can only be picked when it is very ripe."** — Voltaire

---

### **Stage 4: Writing (40-90s) - Synthesis & Communication**
*Theme: Clarity, distillation, storytelling, sharing knowledge, wisdom*

1. **"Writing is thinking. To write well is to think clearly. That's why it's so hard."** — David McCullough
2. **"The art of writing is the art of discovering what you believe."** — Gustave Flaubert
3. **"Clear thinking becomes clear writing; one can't exist without the other."** — William Zinsser
4. **"Either write something worth reading or do something worth writing."** — Benjamin Franklin
5. **"I write to discover what I know."** — Flannery O'Connor
6. **"The scariest moment is always just before you start."** — Stephen King
7. **"A writer is someone for whom writing is more difficult than it is for other people."** — Thomas Mann
8. **"Words are, of course, the most powerful drug used by mankind."** — Rudyard Kipling
9. **"If I had more time, I would have written a shorter letter."** — Blaise Pascal
10. **"The first draft is just you telling yourself the story."** — Terry Pratchett
11. **"You can make anything by writing."** — C.S. Lewis
12. **"Good writing is clear thinking made visible."** — Bill Wheeler
13. **"Write what should not be forgotten."** — Isabel Allende
14. **"The purpose of a writer is to keep civilization from destroying itself."** — Albert Camus
15. **"Writing is the painting of the voice."** — Voltaire
16. **"No tears in the writer, no tears in the reader."** — Robert Frost
17. **"Writing is an exploration. You start from nothing and learn as you go."** — E.L. Doctorow
18. **"The role of a writer is not to say what we can all say, but what we are unable to say."** — Anaïs Nin
19. **"The difference between the almost right word and the right word is really a large matter."** — Mark Twain
20. **"Easy reading is damn hard writing."** — Nathaniel Hawthorne

---

**Quote Selection Logic:**
- **Stage 1** (30-90s): Users see 3-9 quotes about discovery and curiosity
- **Stage 2** (20-60s): Users see 2-6 quotes about planning and methodology
- **Stage 3** (60-120s): Users see 6-12 quotes about knowledge and synthesis
- **Stage 4** (40-90s): Users see 4-9 quotes about writing and communication

**Total Library:** 70 carefully curated quotes (expandable to 100+ based on usage analytics)

**Curation Principles:**
- Each quote creates a "WOW, that's profound" moment
- Diverse voices: scientists, philosophers, writers, thinkers across centuries
- Stage-appropriate: reflects the cognitive activity of that research phase
- Memorable: users should recall quotes long after research completes
- Authentic: no generic motivational poster content

**Visual Treatment:**
- Origami animation: Center stage, 192px × 192px
- Quote display: Below animation, elegant serif or humanist sans-serif typography
- Attribution: Subtle, muted text below quote
- Background: Subtle gradient or soft shadow to separate from dashboard
- Color palette: 20 existing curated palettes (oceanic blues, forest greens, etc.)

**Accessibility Considerations:**
- Animation respects `prefers-reduced-motion` (falls back to gentle fade)
- Quote text has proper contrast ratio (WCAG AA compliant)
- Screen readers announce: "Research in progress: [Stage name]. [Quote text]"

**Technical Implementation Notes:**
- Adapt existing PlayfulLoadingAnimation.tsx from CC_viet_translator project
- Add 7 new research-themed SVG shapes
- Implement stage-aware animation speed logic
- Add progress-based speed multiplier
- Integrate quote rotation system with configurable strategy
- Ensure smooth transitions between shapes (existing origamiFold animation)

### 2.3 Desired Emotional Response

**Target Emotion: Confident and Reassured**

**From Anxiety to Confidence:**
Currently, users experience "blind, anxious waiting" - not knowing if research is working, waiting and praying for success. The target emotional transformation is:

**Before:** "Is it working? Is it stuck? Will this fail again? I have no idea what's happening."

**After:** "I can see it's progressing through stages correctly. The drafts are appearing as expected. I trust this will complete successfully."

**Two User Behaviors to Support:**

1. **Passive Users (Majority):**
   - Start research, switch to other activities, check back periodically
   - When they return 30 seconds or 2 minutes later, they should IMMEDIATELY feel confident
   - Visual cues must clearly show: "Stage 2 of 4 completed, Stage 3 in progress, drafts available"
   - No need to have watched the entire process - the current state tells the story

2. **Active Watchers (Advanced/Excited Users):**
   - Choose to watch the research execute in real-time
   - Each stage transition reassures them: "Yes, this is progressing correctly"
   - Draft artifacts appearing provide tangible evidence of progress
   - Feel engaged and curious: "I can see the AI's thought process unfolding"

**What Confidence Looks Like in UX:**
- **Clear status indicators** - never ambiguous whether something is processing or stuck
- **Progress evidence** - draft files appearing prove the system is working
- **Predictable patterns** - users learn to recognize "this is what Stage 2 looks like"
- **No silent failures** - if something breaks, users know immediately (not after 5 minutes)

**The Feeling That Drives Re-engagement:**
When research completes successfully, users should feel: "That worked exactly as I expected. I trust this system. I'll run another research right away."

Confidence breeds usage. Anxiety breeds abandonment.

---

## 3. Visual Foundation

### 3.1 Color System

_To be populated through workflow_

**Interactive Visualizations:**

- Color Theme Explorer: [ux-color-themes.html](./ux-color-themes.html)

---

## 4. Design Direction

### 4.1 Chosen Design Approach

_To be populated through workflow_

**Interactive Mockups:**

- Design Direction Showcase: [ux-design-directions.html](./ux-design-directions.html)

---

## 5. User Journey Flows

### 5.1 Critical User Paths

**Overview:**
The research execution experience supports two distinct user behaviors: **Passive Users** (majority) who start research and return periodically, and **Active Watchers** (advanced users) who observe the entire execution. Both paths must provide confidence and reassurance at every touchpoint.

---

#### **Path 1: Passive User Journey**

**User Profile:** Knowledge worker who multitasks while research executes (e.g., checking email, reviewing documents, attending meetings).

**Journey Map:**

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Initiate Research                                   │
│ ─────────────────────────────────────────────────────────── │
│ User Input: "The Impact of AI on Knowledge Work"           │
│ Click: [Start Research] button                             │
│ Transition: Immediate navigation to execution view         │
│ Expected time: <1 second                                    │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Initial Glance (First 5 seconds)                   │
│ ─────────────────────────────────────────────────────────── │
│ Visual Scan:                                                │
│   • Origami animation confirms "system is working"          │
│   • Quote provides contemplative distraction                │
│   • Agent cards show Stage 1 active                         │
│   • "3-5 minutes" sets time expectation                     │
│                                                             │
│ Mental State: "Okay, this will take a few minutes."        │
│ Action: Switch to another activity (email, Slack, etc.)    │
│ Expected time: 5-10 seconds                                 │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: First Check-Back (30-90 seconds later)             │
│ ─────────────────────────────────────────────────────────── │
│ Visual Scan:                                                │
│   • Different origami shape + new quote                     │
│   • Stage 1 completed ✓, Stage 2 active                    │
│   • Quote changed (confirms time progression)               │
│                                                             │
│ Mental State: "Good, it's progressing. Stage 2 now."       │
│ Confidence Level: +40% (visual proof of progress)          │
│ Action: Return to other activities                         │
│ Expected time: 3-5 seconds                                  │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Second Check-Back (2-3 minutes later)              │
│ ─────────────────────────────────────────────────────────── │
│ Visual Scan:                                                │
│   • Stages 1-2 completed ✓, Stage 3 active                 │
│   • Multiple quotes have rotated (confirms not stuck)       │
│   • Origami animation still cycling smoothly                │
│                                                             │
│ Mental State: "Almost done, just one more stage."          │
│ Confidence Level: +80% (nearing completion)                │
│ Action: May stay and watch remaining stages                │
│ Expected time: 5-10 seconds                                 │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Completion Notification                            │
│ ─────────────────────────────────────────────────────────── │
│ Visual Changes:                                             │
│   • All 4 stages completed ✓                                │
│   • Animation stops, replaced with success indicator        │
│   • [View Final Report] button appears                     │
│   • [Download Files] button appears                        │
│                                                             │
│ Mental State: "Perfect! Let me see what it found."         │
│ Confidence Level: 100% (successful completion)             │
│ Action: Click [View Final Report]                          │
│ Expected time: <2 seconds                                   │
└─────────────────────────────────────────────────────────────┘
```

**Key Success Metrics:**
- User returns 2-3 times during 3-5 minute execution
- Each check-back confirms progress (different stage active)
- User never wonders "Is it stuck or still working?"
- Successful completion rate: >95%

---

#### **Path 2: Active Watcher Journey**

**User Profile:** Advanced user, excited about AI research methodology, watches the entire 3-5 minute execution.

**Journey Map:**

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Initiate Research                                   │
│ ─────────────────────────────────────────────────────────── │
│ Same as Passive User                                        │
│ Difference: Intends to watch full execution                │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Stage 1 - Initial Research (30-90s)                │
│ ─────────────────────────────────────────────────────────── │
│ Visual Experience:                                          │
│   • Fast origami cycling (3s per shape) = active searching  │
│   • 3-9 discovery quotes (Einstein, Sagan, Feynman)         │
│   • Browser agent card pulsing                              │
│                                                             │
│ Mental Narrative: "The AI is searching the web, exploring   │
│                    multiple sources, gathering raw data..."  │
│ Engagement: Reading quotes, observing animation variety     │
│ Expected time: 30-90 seconds                                │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Stage 2 - Planning (20-60s)                        │
│ ─────────────────────────────────────────────────────────── │
│ Visual Experience:                                          │
│   • Moderate origami speed (4s per shape) = strategic pace  │
│   • 2-6 planning quotes (Lincoln, Franklin, Sun Tzu)        │
│   • Editor agent card pulsing                               │
│                                                             │
│ Mental Narrative: "Now it's organizing the information,     │
│                    structuring the research approach..."     │
│ Engagement: Noticing animation speed change matches stage  │
│ Expected time: 20-60 seconds                                │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Stage 3 - Parallel Research (60-120s)              │
│ ─────────────────────────────────────────────────────────── │
│ Visual Experience:                                          │
│   • Balanced origami speed (3.5s) = multi-threaded work    │
│   • 6-12 synthesis quotes (Hawking, Aristotle, Kant)       │
│   • Researcher agent card pulsing (longest stage)           │
│                                                             │
│ Mental Narrative: "This is the deep work - analyzing,       │
│                    connecting ideas, building knowledge..."  │
│ Engagement: Reading profound quotes about knowledge         │
│ Expected time: 60-120 seconds                               │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Stage 4 - Writing (40-90s)                         │
│ ─────────────────────────────────────────────────────────── │
│ Visual Experience:                                          │
│   • Slow, thoughtful origami (6s → 4.5s as progress)       │
│   • 4-9 writing quotes (McCullough, Twain, Zinsser)        │
│   • Writer agent card pulsing                               │
│   • Animation accelerates subtly (25% faster near end)      │
│                                                             │
│ Mental Narrative: "Now it's composing the final report,     │
│                    distilling everything into clarity..."    │
│ Engagement: Anticipation builds as completion approaches    │
│ Expected time: 40-90 seconds                                │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Completion & Reflection                            │
│ ─────────────────────────────────────────────────────────── │
│ Visual Experience:                                          │
│   • All stages completed ✓                                  │
│   • Success animation (optional celebratory moment)         │
│   • [View Final Report] button appears                     │
│                                                             │
│ Mental State: "That was fascinating to watch. I understand  │
│                how TK9 processes research now."             │
│ Engagement: Satisfaction from observing full methodology    │
│ Action: Immediately click [View Final Report]              │
│ Expected time: <1 second                                    │
└─────────────────────────────────────────────────────────────┘
```

**Key Success Metrics:**
- User watches entire 3-5 minute execution
- Reads 10+ quotes across all stages
- Understands research methodology through visual narrative
- Feels "WOW, that was worth watching"
- Becomes advocate who explains TK9 to colleagues

---

#### **Path 3: Error Recovery Journey**

**User Profile:** User encounters a research failure (network error, API timeout, invalid input).

**Journey Map:**

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Normal Execution Start                             │
│ ─────────────────────────────────────────────────────────── │
│ Same as Passive/Active User paths                          │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Error Occurs (Stage 2, 90s elapsed)                │
│ ─────────────────────────────────────────────────────────── │
│ Visual Changes:                                             │
│   • Origami animation stops immediately                     │
│   • Stage 2 agent card turns red with ❌ icon              │
│   • Error message appears: "Research failed at Stage 2:     │
│     Planning. Network timeout while processing sources."    │
│   • [Retry Research] button appears prominently            │
│   • [View Debug Log] button (optional, for advanced users) │
│                                                             │
│ Mental State: "Something went wrong. But I know WHAT went  │
│                wrong (Stage 2) and WHY (network timeout)."  │
│ Confidence Level: 60% (clear error, not mysterious)        │
│ Expected time: 2-5 seconds to read error                   │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Retry Decision                                     │
│ ─────────────────────────────────────────────────────────── │
│ User Options:                                               │
│   A. Click [Retry Research] → Restart from Stage 1         │
│   B. Click [Modify Query] → Adjust parameters and retry    │
│   C. Click [View Debug Log] → See technical details        │
│                                                             │
│ Mental State: "I'll try again. The error was clear, not my │
│                fault. System is being transparent."         │
│ Action: 95% click [Retry Research] immediately            │
│ Expected time: 3-5 seconds                                  │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Successful Retry                                   │
│ ─────────────────────────────────────────────────────────── │
│ Visual Experience:                                          │
│   • Origami animation restarts from Stage 1                 │
│   • All agent cards reset to queued state                   │
│   • Quote rotation begins fresh                             │
│   • Progress through all 4 stages successfully              │
│                                                             │
│ Mental State: "Good! It worked this time. System is        │
│                reliable overall, just had a hiccup."        │
│ Confidence Level: 95% restored (successful recovery)       │
│ Expected time: 3-5 minutes (full execution)                │
└─────────────────────────────────────────────────────────────┘
```

**Key Success Metrics:**
- Error state is immediately clear (no ambiguity)
- User understands WHAT failed (which stage) and WHY
- 95%+ retry rate after error
- 90%+ success rate on retry
- User trust maintained despite failure

---

### 5.2 Journey Touchpoint Analysis

**Confidence Building Moments:**

| Touchpoint | Visual Indicator | Confidence Impact | Critical Importance |
|------------|------------------|-------------------|---------------------|
| **Initial Launch** | Origami animation starts immediately | +20% | Proves system is responsive |
| **First Quote** | Profound wisdom appears | +10% | Engages intellectually |
| **Stage 1 → 2 Transition** | Agent card 1 ✓, card 2 active | +30% | First proof of progress |
| **Quote Rotation** | New quote every 10s | +5% per rotation | Confirms not frozen |
| **Shape Changes** | New origami every 3-6s | +5% per change | Subconscious progress cue |
| **Stage 3 Active** | Halfway point visible | +40% | Major milestone |
| **Stage 4 Active** | Final stage visible | +60% | Completion imminent |
| **All Stages ✓** | Success state | +100% | Mission accomplished |

**Anxiety Reduction Strategies:**

1. **Eliminate "Black Box" Waiting**
   - ❌ Before: Blank screen or generic spinner
   - ✅ After: Origami animation + quotes + stage cards

2. **Predictable Time Framing**
   - ❌ Before: No time estimate
   - ✅ After: "3-5 minutes" upfront, visual progress

3. **Multiple Progress Signals**
   - Visual: Shape changes (every 3-6s)
   - Textual: Quote rotation (every 10s)
   - Structural: Stage transitions (every 30-120s)
   - Users never wait >10s without seeing change

4. **Error Transparency**
   - ❌ Before: Silent failure or generic "Error"
   - ✅ After: Specific stage, clear reason, retry path

---

### 5.3 Edge Cases & Alternate Paths

**Edge Case 1: Very Fast Research (<90s total)**

```
Problem: Stage animation speeds designed for 3-5 min execution
Solution: Minimum stage duration = 15s
         Users still see each stage transition
         Feels fast but not "skipped"
```

**Edge Case 2: Unusually Slow Research (>7 minutes)**

```
Problem: User anxiety increases after 5 min expectation
Solution: After 5 min, show: "Taking longer than usual.
         Stage 3 is processing complex sources..."
         Maintains transparency, resets expectation
```

**Edge Case 3: User Navigates Away Mid-Execution**

```
Problem: User closes tab or switches pages
Solution: Browser notification when complete:
         "TK9 Research Complete: The Impact of AI..."
         Click notification → Return to results page
```

**Edge Case 4: Multiple Consecutive Failures**

```
Problem: 2+ failures erode confidence severely
Solution: After 2nd failure, show:
         "Repeated errors detected. Please try:
         • Simplify research query
         • Check internet connection
         • Contact support if issue persists"
         Prevents infinite retry frustration
```

---

### 5.4 User Journey Success Criteria

**Passive User Success:**
- ✅ Checks back 2-3 times during execution
- ✅ Each check-back shows different stage active
- ✅ Never wonders "Is this stuck?"
- ✅ 95%+ successful completion rate
- ✅ Immediately trusts system for next research

**Active Watcher Success:**
- ✅ Watches full 3-5 minute execution
- ✅ Reads 10+ quotes across all stages
- ✅ Understands multi-stage methodology
- ✅ Feels intellectually engaged (not bored)
- ✅ Becomes TK9 advocate to colleagues

**Error Recovery Success:**
- ✅ Understands error within 5 seconds
- ✅ 95%+ retry immediately (not abandon)
- ✅ 90%+ successful retry
- ✅ Confidence restored after success
- ✅ Does not hesitate to use system again

**Overall Journey Success:**
- ✅ Zero "is this broken?" support tickets
- ✅ User satisfaction score: 4.5/5+
- ✅ Feature engagement: 80%+ watch at least once
- ✅ Repeat usage: 90%+ run multiple researches per session

---

## 6. Component Library

### 6.1 Component Strategy

**Architecture Philosophy:**
TK9's waiting experience uses a **compositional architecture** where small, focused components combine to create the complete experience. This ensures maintainability, testability, and reusability across different contexts.

---

### 6.2 Component Hierarchy

```
WaitingExperience/ (Orchestrator)
├── OrigamiAnimation/ (Visual Progress)
│   ├── OrigamiShape.vue (Single shape renderer)
│   ├── origami-shapes.ts (27 SVG shape definitions)
│   ├── origami-animations.css (1907 lines CSS keyframes)
│   └── color-palettes.ts (20 curated color palettes)
│
├── QuoteDisplay/ (Intellectual Engagement)
│   ├── QuoteDisplay.vue (Main component)
│   ├── quotes-library.ts (70 stage-categorized quotes)
│   └── QuoteTransition.vue (Fade animation wrapper)
│
├── StageProgress/ (Confidence Building)
│   ├── StageIndicator.vue (Stage N of 4 display)
│   ├── StageName.vue (Stage title display)
│   └── AgentCards.vue (Stage agent card grid)
│
└── CompletionState/ (Success/Error States)
    ├── SuccessView.vue (All stages completed)
    ├── ErrorView.vue (Failure state with retry)
    └── RetryButton.vue (Retry CTA component)
```

---

### 6.3 Core Components

#### **Component 1: WaitingExperience.vue** (Orchestrator)

**Purpose:** Main coordinator that manages state, timing, and child component communication.

**Props:**
```typescript
interface WaitingExperienceProps {
  sessionId: string              // Current research session ID
  currentStage: 1 | 2 | 3 | 4   // Active stage (1=Initial, 2=Planning, 3=Research, 4=Writing)
  stageProgress: number           // Progress within current stage (0-100)
  stageName: string              // Human-readable stage name
  activeAgent: string            // Currently executing agent name
  onComplete?: () => void        // Callback when all stages complete
  onError?: (error: Error) => void // Callback on execution error
}
```

**State Management:**
```typescript
const state = reactive({
  currentShape: 0,              // Index in shapes array
  currentPalette: 0,            // Index in palettes array
  currentQuote: 0,              // Index in stage-specific quotes
  animationSpeed: 4500,         // Milliseconds per shape (stage-dependent)
  shapeRotationInterval: null,  // setInterval handle for shapes
  quoteRotationInterval: null,  // setInterval handle for quotes
})
```

**Key Methods:**
```typescript
// Initialize timers based on current stage
function initializeTimers(stage: number): void {
  const speeds = { 1: 3000, 2: 4000, 3: 3500, 4: 6000 } // Base speeds
  state.animationSpeed = speeds[stage]

  // Apply progress-based acceleration
  const progressMultiplier = 1 - (stageProgress * 0.25) // 0-25% faster
  state.animationSpeed *= progressMultiplier

  startShapeRotation()
  startQuoteRotation()
}

// Cleanup timers on unmount
function cleanup(): void {
  if (state.shapeRotationInterval) clearInterval(state.shapeRotationInterval)
  if (state.quoteRotationInterval) clearInterval(state.quoteRotationInterval)
}
```

**Template Structure:**
```vue
<template>
  <el-space direction="vertical" alignment="center" :size="24" class="tk9-waiting-container">
    <!-- Origami Animation -->
    <OrigamiAnimation
      :shape-index="state.currentShape"
      :palette-index="state.currentPalette"
      :animation-speed="state.animationSpeed"
    />

    <!-- Quote Display -->
    <QuoteDisplay
      :stage="currentStage"
      :quote-index="state.currentQuote"
    />

    <!-- Stage Progress -->
    <StageProgress
      :current-stage="currentStage"
      :stage-name="stageName"
      :active-agent="activeAgent"
    />
  </el-space>
</template>
```

---

#### **Component 2: OrigamiAnimation.vue**

**Purpose:** Renders animated origami shapes with stage-specific speeds and color palettes.

**Props:**
```typescript
interface OrigamiAnimationProps {
  shapeIndex: number      // Current shape to display (0-26)
  paletteIndex: number    // Current color palette (0-19)
  animationSpeed: number  // Milliseconds per shape cycle
}
```

**Computed Values:**
```typescript
const currentShape = computed(() => shapes[props.shapeIndex])
const currentPalette = computed(() => palettes[props.paletteIndex])

const animationDuration = computed(() => `${props.animationSpeed}ms`)

const shapeSVG = computed(() => {
  return currentShape.value.svg
    .replace('COLOR1', currentPalette.value[0])
    .replace('COLOR2', currentPalette.value[1])
    .replace('COLOR3', currentPalette.value[2] || currentPalette.value[0])
})
```

**Template:**
```vue
<template>
  <div
    class="tk9-origami-animation"
    :style="{ animationDuration }"
  >
    <svg
      viewBox="0 0 200 200"
      class="origami-shape"
      v-html="shapeSVG"
    />
  </div>
</template>

<style scoped>
.tk9-origami-animation {
  width: 192px;
  height: 192px;
  animation: origamiFold var(--animation-duration, 4.5s) ease-in-out infinite;
}

@keyframes origamiFold {
  0%, 100% {
    transform: rotateY(0deg) scale(1);
    opacity: 1;
  }
  50% {
    transform: rotateY(180deg) scale(0.85);
    opacity: 0.9;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tk9-origami-animation {
    animation: simpleFade 4s ease-in-out infinite;
  }

  @keyframes simpleFade {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
}
</style>
```

---

#### **Component 3: QuoteDisplay.vue**

**Purpose:** Displays stage-specific quotes with elegant typography and fade transitions.

**Props:**
```typescript
interface QuoteDisplayProps {
  stage: 1 | 2 | 3 | 4   // Current research stage
  quoteIndex: number      // Index within stage's quote array
}
```

**Computed Values:**
```typescript
const stageQuotes = computed(() => {
  return quotesLibrary[props.stage] // Stage-specific quote array
})

const currentQuote = computed(() => {
  const quotes = stageQuotes.value
  return quotes[props.quoteIndex % quotes.length]
})
```

**Template:**
```vue
<template>
  <Transition name="quote-fade" mode="out-in">
    <el-space
      :key="currentQuote.text"
      direction="vertical"
      alignment="center"
      :size="8"
      class="tk9-quote-container"
    >
      <el-text
        tag="blockquote"
        class="tk9-quote-text"
      >
        "{{ currentQuote.text }}"
      </el-text>
      <el-text
        type="info"
        class="tk9-quote-attribution"
      >
        — {{ currentQuote.author }}
      </el-text>
    </el-space>
  </Transition>
</template>

<style scoped>
.tk9-quote-text {
  font-family: var(--tk9-font-quotes);
  font-size: 1.125rem;
  line-height: 1.6;
  font-style: italic;
  color: var(--el-text-color-primary);
  text-align: center;
}

.tk9-quote-attribution {
  font-size: 0.875rem;
  font-weight: 500;
  opacity: 0.75;
}

.quote-fade-enter-active,
.quote-fade-leave-active {
  transition: all 0.5s ease;
}

.quote-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.quote-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
```

---

#### **Component 4: StageProgress.vue**

**Purpose:** Shows stage indicator, stage name, and agent cards in a cohesive progress view.

**Props:**
```typescript
interface StageProgressProps {
  currentStage: number    // 1-4
  stageName: string       // e.g., "Planning & Methodology"
  activeAgent: string     // e.g., "Researcher"
  agents: AgentStatus[]   // Array of agent states
}

interface AgentStatus {
  name: string
  icon: string
  status: 'queued' | 'active' | 'completed'
}
```

**Template:**
```vue
<template>
  <div class="stage-progress">
    <!-- Stage Indicator -->
    <div class="stage-indicator">
      <el-text type="info" size="small">
        Stage <strong>{{ currentStage }}</strong> of 4
      </el-text>
    </div>

    <!-- Stage Name -->
    <div class="stage-name">
      <el-text type="primary" size="large">
        {{ stageName }}
      </el-text>
    </div>

    <!-- Agent Cards -->
    <div class="agent-cards">
      <div
        v-for="agent in agents"
        :key="agent.name"
        :class="['agent-card', agent.status]"
      >
        <div class="agent-status-indicator"></div>
        <div class="agent-icon">{{ agent.icon }}</div>
        <div class="agent-name">{{ agent.name }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-card {
  width: 120px;
  padding: 0.75rem;
  border-radius: 8px;
  border: 2px solid var(--el-border-color);
  background: var(--el-bg-color);
  transition: all 0.3s;
  position: relative;
}

.agent-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  animation: pulse 2s ease-in-out infinite;
}

.agent-card.completed {
  border-color: var(--el-color-success);
  background: var(--el-color-success-light-9);
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(var(--el-color-primary-rgb), 0.4);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 0 0 8px rgba(var(--el-color-primary-rgb), 0);
  }
}
</style>
```

---

### 6.4 Component Communication Patterns

**Parent → Child (Props Down):**
```typescript
// WaitingExperience.vue passes current state to children
<OrigamiAnimation
  :shape-index="state.currentShape"
  :palette-index="state.currentPalette"
  :animation-speed="state.animationSpeed"
/>
```

**Child → Parent (Events Up):**
```typescript
// ErrorView.vue emits retry event to parent
const emit = defineEmits<{
  retry: []
  viewDebugLog: []
}>()

// Parent listens and handles
<ErrorView
  @retry="handleRetry"
  @viewDebugLog="openDebugModal"
/>
```

**Sibling Communication (Shared State via Pinia):**
```typescript
// sessionsStore.ts
export const useSessionsStore = defineStore('sessions', () => {
  const currentStage = ref<number>(1)
  const stageProgress = ref<number>(0)

  function updateStage(stage: number, progress: number) {
    currentStage.value = stage
    stageProgress.value = progress
  }

  return { currentStage, stageProgress, updateStage }
})

// Components consume shared state
const sessionsStore = useSessionsStore()
const { currentStage } = storeToRefs(sessionsStore)
```

---

### 6.5 Reusability Strategy

**Pattern 1: Composable Logic**

Extract timer management into reusable composable:

```typescript
// composables/useRotationTimer.ts
export function useRotationTimer(
  interval: Ref<number>,
  callback: () => void
) {
  const timerId = ref<number | null>(null)

  function start() {
    if (timerId.value) return
    timerId.value = window.setInterval(callback, interval.value)
  }

  function stop() {
    if (timerId.value) {
      clearInterval(timerId.value)
      timerId.value = null
    }
  }

  onMounted(start)
  onUnmounted(stop)

  return { start, stop }
}

// Usage in WaitingExperience.vue
const { start: startShapeRotation, stop: stopShapeRotation } = useRotationTimer(
  computed(() => state.animationSpeed),
  nextShape
)
```

**Pattern 2: Shape Data as Module**

```typescript
// origami-shapes.ts (Importable data module)
export interface OrigamiShape {
  name: string
  svg: string
  category: 'traditional' | 'modern' | 'research'
}

export const shapes: OrigamiShape[] = [
  {
    name: 'crane',
    category: 'traditional',
    svg: `<path d="..." fill="COLOR1" />`
  },
  // ...26 more shapes
]

export function getShapesByCategory(
  category: OrigamiShape['category']
): OrigamiShape[] {
  return shapes.filter(s => s.category === category)
}
```

**Pattern 3: Quote Library as Service**

```typescript
// services/QuoteService.ts
class QuoteService {
  private quotes: Record<number, Quote[]>

  constructor() {
    this.quotes = quotesLibrary // Import from quotes-library.ts
  }

  getQuotesForStage(stage: number): Quote[] {
    return this.quotes[stage] || []
  }

  getRandomQuote(stage: number): Quote {
    const quotes = this.getQuotesForStage(stage)
    return quotes[Math.floor(Math.random() * quotes.length)]
  }

  getQuoteCount(stage: number): number {
    return this.getQuotesForStage(stage).length
  }
}

export const quoteService = new QuoteService()
```

---

### 6.6 Testing Strategy

**Unit Tests (Vitest):**

```typescript
// OrigamiAnimation.spec.ts
import { mount } from '@vue/test-utils'
import OrigamiAnimation from './OrigamiAnimation.vue'

describe('OrigamiAnimation', () => {
  it('renders shape with correct palette colors', () => {
    const wrapper = mount(OrigamiAnimation, {
      props: {
        shapeIndex: 0,
        paletteIndex: 0,
        animationSpeed: 4500
      }
    })

    const svg = wrapper.find('svg')
    expect(svg.html()).toContain('#0891B2') // Oceanic Blues palette
  })

  it('respects prefers-reduced-motion', () => {
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true // prefers-reduced-motion: reduce
    })

    const wrapper = mount(OrigamiAnimation, {
      props: { shapeIndex: 0, paletteIndex: 0, animationSpeed: 4500 }
    })

    const animation = wrapper.find('.tk9-origami-animation')
    expect(animation.classes()).toContain('reduced-motion')
  })
})
```

**Integration Tests:**

```typescript
// WaitingExperience.spec.ts
describe('WaitingExperience Integration', () => {
  it('rotates quotes every 10 seconds', async () => {
    vi.useFakeTimers()
    const wrapper = mount(WaitingExperience, {
      props: {
        sessionId: 'test-123',
        currentStage: 1,
        stageProgress: 0,
        stageName: 'Initial Research',
        activeAgent: 'Browser'
      }
    })

    const initialQuote = wrapper.find('.tk9-quote-text').text()

    vi.advanceTimersByTime(10000) // Fast-forward 10 seconds
    await wrapper.vm.$nextTick()

    const newQuote = wrapper.find('.tk9-quote-text').text()
    expect(newQuote).not.toBe(initialQuote)

    vi.useRealTimers()
  })
})
```

---

### 6.7 Performance Optimization

**1. Lazy Loading Shapes:**
```typescript
// Only load shapes when needed
const loadedShapes = ref<Set<number>>(new Set())

function preloadShape(index: number) {
  if (!loadedShapes.value.has(index)) {
    // Shape SVG is already in module, just mark as accessed
    loadedShapes.value.add(index)
  }
}
```

**2. CSS Containment:**
```css
.tk9-origami-animation {
  contain: layout style paint;
  will-change: transform;
}
```

**3. Debounced Window Events:**
```typescript
import { useDebounceFn } from '@vueuse/core'

const handleResize = useDebounceFn(() => {
  // Adjust layout for mobile/desktop
}, 250)

useEventListener('resize', handleResize)
```

---

### 6.8 Accessibility Enhancements

**ARIA Live Region:**
```vue
<template>
  <div
    role="status"
    aria-live="polite"
    aria-atomic="true"
    class="sr-only"
  >
    Research in progress: Stage {{ currentStage }} - {{ stageName }}.
    {{ currentQuote.text }} by {{ currentQuote.author }}
  </div>
</template>
```

**Keyboard Navigation:**
```typescript
// WaitingExperience.vue
function handleKeyboard(event: KeyboardEvent) {
  if (event.key === 'Space') {
    // Pause/resume animation
    toggleAnimation()
  }
  if (event.key === 'ArrowRight') {
    // Next quote
    nextQuote()
  }
  if (event.key === 'ArrowLeft') {
    // Previous quote
    previousQuote()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyboard)
})
```

---

### 6.9 Component Checklist

Before marking component as production-ready:

- [ ] **Props validated** - TypeScript interfaces + runtime validation
- [ ] **Emits documented** - Clear event names and payloads
- [ ] **Accessibility tested** - Screen reader, keyboard, high contrast
- [ ] **Unit tests written** - 80%+ coverage
- [ ] **Integration tests passing** - Component interactions verified
- [ ] **Performance profiled** - <16ms render time (60fps)
- [ ] **Responsive tested** - Mobile, tablet, desktop breakpoints
- [ ] **Dark mode verified** - Looks good in both themes
- [ ] **Error states handled** - Graceful degradation
- [ ] **Documentation complete** - Props, events, usage examples

---

## 7. UX Pattern Decisions

### 7.1 Consistency Rules

**Overview:**
TK9's waiting experience establishes new UX patterns while maintaining consistency with the existing dashboard. These patterns should be applied consistently across future features to build user familiarity and trust.

---

### 7.2 Animation Pattern Standards

**Rule 1: Purposeful Animation**
```
✅ DO: Use animation to communicate system state (progress, loading, completion)
❌ DON'T: Use animation purely for decoration without functional purpose

Example:
✅ Origami shape cycling indicates research is actively processing
❌ Generic bouncing icon that conveys no information
```

**Rule 2: Stage-Contextual Speed**
```
Animation speed MUST reflect the cognitive nature of each stage:
- Stage 1 (Initial Research): Fast (3s) = active searching
- Stage 2 (Planning): Moderate (4s) = strategic thinking
- Stage 3 (Parallel Research): Balanced (3.5s) = multi-threaded work
- Stage 4 (Writing): Slow (6s) = thoughtful composition

Never use arbitrary animation speeds. Speed communicates meaning.
```

**Rule 3: Progress-Based Acceleration**
```
As stage completion approaches (75-100%), animation speed increases by up to 25%:
- 0-25% complete: Base speed
- 25-50% complete: +10% faster
- 50-75% complete: +15% faster
- 75-95% complete: +20% faster
- 95-100% complete: +25% faster

This creates subconscious anticipation of completion without explicit progress bars.
```

**Rule 4: Reduced Motion Respect**
```
ALWAYS provide fallback for users with motion sensitivity:

@media (prefers-reduced-motion: reduce) {
  /* Replace complex 3D transforms with gentle fade */
  animation: simpleFade 4s ease-in-out infinite;
}

No user should experience discomfort from motion.
```

---

### 7.3 Content Rotation Patterns

**Quote Rotation Standard: 10-Second Intervals**
```
Why 10 seconds?
- Too fast (<5s): Can't finish reading quote
- Too slow (>15s): Feels static, loses engagement
- 10s: Perfect reading time + brief reflection

Apply this timing to ANY rotating educational/inspirational content.
```

**Shape Rotation Standard: Stage-Dependent (3-6 seconds)**
```
Why stage-dependent?
- Visual variety maintains engagement
- Speed reinforces stage characteristics
- Users learn to associate speed with progress stage

Apply to ANY progress-indicating animations with multiple visual states.
```

**Independent Timing Principle**
```
✅ DO: Quote rotation (10s) independent of shape rotation (3-6s)
❌ DON'T: Synchronize all timings to same interval

Why independent?
- Creates visual richness and variety
- Prevents predictable, monotonous patterns
- Users never see the exact same combination twice in short time
```

---

### 7.4 Typography Hierarchy for Waiting States

**Primary Message: Large, Bold, Centered**
```css
.research-title {
  font-size: 1.5rem;    /* 24px */
  font-weight: 600;
  text-align: center;
  color: var(--el-text-color-primary);
}
```

**Secondary Message: Medium, Regular, Muted**
```css
.research-meta {
  font-size: 0.875rem;  /* 14px */
  font-weight: 400;
  color: var(--el-text-color-secondary);
}
```

**Quotes: Large, Italic, Serif**
```css
.tk9-quote-text {
  font-size: 1.125rem;  /* 18px */
  font-style: italic;
  font-family: var(--tk9-font-quotes); /* Crimson Pro */
}
```

**Attribution: Small, Medium Weight, Sans-Serif**
```css
.tk9-quote-attribution {
  font-size: 0.875rem;  /* 14px */
  font-weight: 500;
  font-family: var(--el-font-family); /* Inter */
}
```

**Consistency Rule:**
Apply this hierarchy to ANY waiting/loading state with educational content.

---

### 7.5 Color Usage Patterns

**Rule 1: Palette Variety, Not Semantic Meaning**
```
✅ DO: Cycle through 20 color palettes for visual variety
❌ DON'T: Use specific colors to indicate status (e.g., red = error)

Origami shapes are decorative and provide motion feedback.
Status indicators (agent cards) use semantic colors.
```

**Rule 2: Semantic Colors for Status**
```css
/* Agent card status colors (consistent across TK9) */
.queued   { border-color: #e0e0e0; background: #fafafa; }     /* Gray */
.active   { border-color: #42a5f5; background: #e3f2fd; }     /* Blue */
.completed{ border-color: #66bb6a; background: #e8f5e9; }     /* Green */
.error    { border-color: #ef5350; background: #ffebee; }     /* Red */

NEVER use these colors outside status indicators.
```

**Rule 3: High Contrast for Text**
```
✅ DO: Quote text maintains 4.5:1 contrast minimum (WCAG AA)
❌ DON'T: Apply origami palette colors to quote text

Quote text is high-contrast and readable.
Origami colors are vibrant but don't affect text legibility.
```

**Rule 4: Dark Mode Adaptation**
```
In dark mode:
- Origami colors: Desaturate by 15% (reduces eye strain)
- Quote text: Automatically inverts via Element Plus
- Background: Soft dark gradient (not pure black)

Test every color decision in both light and dark mode.
```

---

### 7.6 Interactive Feedback Patterns

**Rule 1: Immediate Visual Response**
```
Button clicks, hover states, focus states → <100ms feedback

Example:
button:hover { background: #337ecc; transition: background 0.15s; }

User should NEVER wonder "Did that register?"
```

**Rule 2: Agent Card Pulse Animation**
```css
.agent-card.active {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}
```

**Why 2-second pulse?**
- Slow enough to not distract
- Fast enough to communicate "actively processing"
- Apply to ANY "currently executing" visual indicator

**Rule 3: Error State Immediacy**
```
When error occurs:
1. Animation stops IMMEDIATELY (<100ms)
2. Error message appears within 300ms
3. Retry button appears simultaneously
4. Failed agent card turns red with ❌ icon

Users should know within 500ms total that something went wrong.
```

**Rule 4: Success State Celebration**
```
When all stages complete:
1. Final agent card completes animation (300ms)
2. Optional subtle "success" animation (500ms, optional)
3. [View Final Report] button appears (fade-in 300ms)

Total transition: ~1 second from "Stage 4 active" to "View Results"
```

---

### 7.7 Spacing & Layout Consistency

**Rule 1: Vertical Rhythm (8px Base Unit)**
```
Component spacing follows 8px grid:
- Tight spacing: 8px
- Comfortable spacing: 16px
- Generous spacing: 24px
- Extra-generous spacing: 32px

NEVER use arbitrary values like 13px, 27px, etc.
```

**Rule 2: Center-Aligned Waiting States**
```
Waiting/loading states ALWAYS centered:
- Horizontally: margin: 0 auto; max-width: 800px;
- Vertically: display: flex; align-items: center; justify-content: center;

User's focus should be on the waiting experience, not hunting for it.
```

**Rule 3: Progressive Disclosure**
```
Reveal information in layers as needed:

Layer 1: Origami animation + quote (always visible)
Layer 2: Stage progress + agent cards (always visible)
Layer 3: Draft artifacts (appears as available)
Layer 4: Completion actions (appears only when complete)

DON'T show all options upfront. Guide user through states.
```

---

### 7.8 Error Handling Patterns

**Pattern 1: Clear Error Attribution**
```
❌ WRONG: "An error occurred. Please try again."
✅ RIGHT: "Research failed at Stage 2: Planning. Network timeout while processing sources."

Always specify:
1. WHAT failed (which stage/component)
2. WHY it failed (specific error reason)
3. WHAT to do (retry, modify query, contact support)
```

**Pattern 2: Non-Blocking Error Display**
```
Error messages appear:
- In-context (where error occurred, not global toast)
- With clear visual hierarchy (error message → retry button)
- Without dismissing content (user can still see what was processing)

Example:
┌────────────────────────────────────────┐
│  ❌ Research Failed at Stage 2         │
│  Network timeout while processing.     │
│  [Retry Research]  [Modify Query]      │
│  ────────────────────────────────────  │
│  Stage 1: Completed ✓                  │
│  Stage 2: Failed ❌ (Browser Agent)    │
│  Stage 3: Not started                  │
└────────────────────────────────────────┘
```

**Pattern 3: Graduated Error Responses**
```
First error:  Simple retry button
Second error: Suggest query modification
Third error:  Provide support contact

Progressive assistance based on frustration level.
```

---

### 7.9 Mobile Responsiveness Patterns

**Pattern 1: Vertical Stacking on Mobile**
```
Desktop: Horizontal agent cards (5 cards × 120px wide)
Mobile:  Vertical stack (full width, 2-3 visible at once)

@media (max-width: 768px) {
  .agent-cards {
    flex-direction: column;
    max-height: 300px;
    overflow-y: auto;
  }
}
```

**Pattern 2: Touch-Friendly Targets**
```
Minimum touch target: 44px × 44px (Apple Human Interface Guidelines)

Buttons on mobile:
- Height: min-height: 44px;
- Spacing: margin: 16px 0;

Ensure users can tap accurately without frustration.
```

**Pattern 3: Reduced Animation on Mobile**
```
Origami animation on mobile:
- Size: 120px × 120px (instead of 192px)
- Speed: +20% faster (to reduce wait perception on smaller screens)

Performance considerations:
- Simpler shapes prioritized on low-end devices
- Animation automatically pauses if battery low (Battery Status API)
```

---

### 7.10 Notification & Alert Patterns

**Pattern 1: Browser Notifications (Optional Enhancement)**
```
When user navigates away mid-execution:

if (Notification.permission === 'granted') {
  new Notification('TK9 Research Complete', {
    body: researchTitle,
    icon: '/tk9-icon.png',
    tag: sessionId
  })
}

Click notification → Return to results page

ONLY show if user granted permission. Never annoy.
```

**Pattern 2: In-App Completion Toast**
```
If user stays on page:
- Toast appears top-right: "Research complete! [View Results]"
- Auto-dismiss after 10 seconds
- Click to navigate to results immediately

Element Plus Toast component:
ElMessage.success({
  message: 'Research complete!',
  duration: 10000,
  showClose: true
})
```

**Pattern 3: Stage Transition Micro-Feedback**
```
When stage transitions (1→2, 2→3, 3→4):
- Agent card completes with subtle "check" animation (300ms)
- Next agent card highlights with gentle pulse start
- Optional subtle sound effect (if user enabled audio)

Provides continuous reassurance without interrupting flow.
```

---

### 7.11 Accessibility Pattern Standards

**Pattern 1: Screen Reader Announcements**
```html
<div role="status" aria-live="polite" aria-atomic="true" class="sr-only">
  <!-- Updates announced but not interrupting -->
  Research in progress: Stage {{ currentStage }} of 4.
  {{ stageName }}.
  {{ currentQuote.text }} by {{ currentQuote.author }}
</div>
```

**Pattern 2: Keyboard Navigation Support**
```
Space: Pause/resume animation
Arrow Right: Next quote
Arrow Left: Previous quote
Enter (on agent card): View stage details
Tab: Navigate between interactive elements

Ensure every action accessible via keyboard.
```

**Pattern 3: Focus Management**
```
When modal/error appears:
1. Trap focus within modal
2. Return focus to trigger element on close
3. Announce modal title to screen readers

Never let keyboard users get lost.
```

---

### 7.12 Pattern Application Checklist

Before implementing ANY new waiting/loading experience:

- [ ] **Animation is purposeful** - communicates system state
- [ ] **Speed is contextual** - matches cognitive stage
- [ ] **Reduced motion fallback** - gentle fade for sensitive users
- [ ] **Independent timing** - multiple rotation intervals for variety
- [ ] **High contrast text** - WCAG AA compliant
- [ ] **Semantic colors for status** - consistent across app
- [ ] **8px vertical rhythm** - spacing follows grid
- [ ] **Center-aligned** - user focus clear
- [ ] **Clear error messages** - WHAT, WHY, WHAT TO DO
- [ ] **Mobile-responsive** - vertical stacking, touch targets
- [ ] **Keyboard accessible** - all actions via keyboard
- [ ] **Screen reader friendly** - ARIA labels, live regions
- [ ] **Tested in dark mode** - looks good in both themes

---

## 8. Responsive Design & Accessibility

### 8.1 Responsive Strategy

**Overview:**
TK9's waiting experience adapts gracefully across devices from mobile (320px) to desktop (1920px+), maintaining usability and aesthetic quality at every breakpoint.

---

### 8.2 Breakpoint System

**Standard Breakpoints (Element Plus Aligned):**

| Breakpoint | Width | Target Devices | Layout Changes |
|------------|-------|----------------|----------------|
| **xs** | <768px | Mobile phones | Vertical stacking, smaller animation |
| **sm** | 768px - 992px | Tablets (portrait) | Compact layout, 2-column agent cards |
| **md** | 992px - 1200px | Tablets (landscape), small laptops | Standard layout begins |
| **lg** | 1200px - 1920px | Desktops | Optimal layout (design target) |
| **xl** | >1920px | Large displays | Max-width container, centered |

**CSS Implementation:**

```css
/* Mobile First Approach */
.tk9-waiting-container {
  /* xs: Mobile phones (<768px) */
  padding: var(--el-spacing-md);
}

@media (min-width: 768px) {
  /* sm: Tablets (portrait) */
  .tk9-waiting-container {
    padding: var(--el-spacing-lg);
  }
}

@media (min-width: 992px) {
  /* md: Tablets (landscape), small laptops */
  .tk9-waiting-container {
    padding: var(--el-spacing-xl);
  }
}

@media (min-width: 1200px) {
  /* lg: Desktops (optimal) */
  .tk9-waiting-container {
    max-width: 800px;
    margin: 0 auto;
  }
}

@media (min-width: 1920px) {
  /* xl: Large displays */
  .tk9-waiting-container {
    max-width: 1000px;
  }
}
```

---

### 8.3 Component Responsive Behavior

#### **Origami Animation Scaling**

```css
.tk9-origami-animation {
  /* xs: Mobile - Smaller, faster */
  width: 120px;
  height: 120px;
  animation-duration: 3.6s; /* 20% faster */
}

@media (min-width: 768px) {
  /* sm: Tablets - Medium size */
  .tk9-origami-animation {
    width: 150px;
    height: 150px;
    animation-duration: 4s;
  }
}

@media (min-width: 992px) {
  /* md+: Desktop - Full size */
  .tk9-origami-animation {
    width: 192px;
    height: 192px;
    animation-duration: 4.5s; /* Stage-dependent */
  }
}
```

**Rationale:**
- Smaller screens = Smaller animation (proportional)
- Faster on mobile reduces perceived wait time
- Full experience on desktop where users more likely to watch

---

#### **Quote Display Responsive Typography**

```css
.tk9-quote-text {
  /* xs: Mobile - Readable but compact */
  font-size: 1rem; /* 16px */
  line-height: 1.5;
  padding: 0 1rem;
}

@media (min-width: 768px) {
  /* sm: Tablets - Slightly larger */
  .tk9-quote-text {
    font-size: 1.0625rem; /* 17px */
    padding: 0 1.5rem;
  }
}

@media (min-width: 992px) {
  /* md+: Desktop - Full size */
  .tk9-quote-text {
    font-size: 1.125rem; /* 18px */
    line-height: 1.6;
    padding: 0 2rem;
  }
}
```

---

#### **Agent Cards Responsive Layout**

```css
.agent-cards {
  /* xs: Mobile - Vertical stack, scrollable */
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 240px; /* Show 2-3 cards */
  overflow-y: auto;
  padding: 0 1rem;
}

@media (min-width: 768px) {
  /* sm: Tablets - 2 columns */
  .agent-cards {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    max-height: none;
    overflow-y: visible;
  }

  .agent-card {
    flex: 0 1 calc(50% - 0.5rem); /* 2 columns */
  }
}

@media (min-width: 992px) {
  /* md+: Desktop - Single horizontal row */
  .agent-cards {
    flex-wrap: nowrap;
    justify-content: center;
    gap: 0.75rem;
  }

  .agent-card {
    flex: 0 1 120px; /* Fixed width */
  }
}
```

**Visual Examples:**

```
Mobile (xs):
┌────────────┐
│  Browser   │
├────────────┤
│  Editor    │
├────────────┤
│ Researcher │ ← Scroll to see more
└────────────┘

Tablet (sm):
┌─────────┬─────────┐
│ Browser │  Editor │
├─────────┼─────────┤
│Research │ Writer  │
└─────────┴─────────┘

Desktop (md+):
┌────┬────┬────┬────┬────┐
│Brow│Edit│Rese│Writ│Publ│
└────┴────┴────┴────┴────┘
```

---

### 8.4 Touch Interaction Enhancements

**Touch Target Sizing (Mobile Only):**

```css
@media (max-width: 768px) and (hover: none) {
  /* Detect touch devices */

  .retry-button,
  .view-results-button {
    min-height: 44px; /* Apple HIG minimum */
    min-width: 44px;
    padding: 0.75rem 1.5rem;
  }

  .agent-card {
    min-height: 60px; /* Larger for easier tapping */
    padding: 1rem;
  }

  /* Increase spacing between interactive elements */
  .control-buttons {
    gap: 1rem; /* Prevent accidental taps */
  }
}
```

**Gesture Support:**

```typescript
// Composable: useSwipeGesture.ts
import { useSwipe } from '@vueuse/core'

export function useQuoteSwipe(
  target: Ref<HTMLElement>,
  callbacks: { onSwipeLeft: () => void; onSwipeRight: () => void }
) {
  const { direction } = useSwipe(target, {
    threshold: 50, // 50px minimum swipe
    passive: true
  })

  watch(direction, (dir) => {
    if (dir === 'left') callbacks.onSwipeLeft()
    if (dir === 'right') callbacks.onSwipeRight()
  })
}

// Usage in QuoteDisplay.vue
const quoteContainer = ref<HTMLElement>()
useQuoteSwipe(quoteContainer, {
  onSwipeLeft: nextQuote,
  onSwipeRight: previousQuote
})
```

---

### 8.5 Accessibility Comprehensive Guide

#### **WCAG 2.1 AA Compliance Checklist**

**Perceivable:**
- [x] **Color Contrast**: Quote text 4.5:1 minimum, secondary text 3:1
- [x] **Non-Color Indicators**: Agent status uses icons + color (✓, ❌, •)
- [x] **Alternative Text**: Decorative SVG marked as `aria-hidden="true"`
- [x] **Zoom Support**: Layout doesn't break at 200% zoom

**Operable:**
- [x] **Keyboard Navigation**: All interactive elements reachable via Tab
- [x] **No Keyboard Traps**: Focus can always move forward/backward
- [x] **Sufficient Time**: No auto-dismissing critical info (except success toast 10s)
- [x] **Pause Animation**: Spacebar pauses/resumes origami animation
- [x] **Skip Links**: "Skip to results" appears after completion

**Understandable:**
- [x] **Consistent Navigation**: Patterns match rest of TK9 dashboard
- [x] **Error Identification**: Errors clearly state what failed and why
- [x] **Input Assistance**: Retry buttons clearly labeled

**Robust:**
- [x] **Valid HTML**: No unclosed tags, proper nesting
- [x] **ARIA Semantics**: `role`, `aria-live`, `aria-label` used correctly
- [x] **Cross-Browser**: Tested in Chrome, Firefox, Safari, Edge

---

#### **Screen Reader Optimization**

**Live Regions for Dynamic Content:**

```vue
<template>
  <!-- Polite announcements (non-interrupting) -->
  <div
    role="status"
    aria-live="polite"
    aria-atomic="true"
    class="sr-only"
  >
    Research in progress.
    Stage {{ currentStage }} of 4: {{ stageName }}.
    Currently executing: {{ activeAgent }}.
    {{ currentQuote.text }} by {{ currentQuote.author }}.
  </div>

  <!-- Assertive announcements (interrupting, for errors) -->
  <div
    v-if="error"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    class="sr-only"
  >
    Error: Research failed at Stage {{ failedStage }}.
    {{ error.message }}.
    Retry button available.
  </div>
</template>
```

**Semantic HTML Structure:**

```html
<main aria-labelledby="page-title">
  <h1 id="page-title">Research in Progress</h1>

  <section aria-labelledby="research-title">
    <h2 id="research-title">{{ researchTitle }}</h2>

    <div role="progressbar"
         aria-valuenow="50"
         aria-valuemin="0"
         aria-valuemax="100"
         aria-label="Research progress: Stage 2 of 4">
      <!-- Visual progress representation -->
    </div>
  </section>

  <aside aria-label="Inspirational quote">
    <blockquote>{{ currentQuote.text }}</blockquote>
    <cite>{{ currentQuote.author }}</cite>
  </aside>
</main>
```

---

#### **Keyboard Navigation Map**

| Key | Action | Context |
|-----|--------|---------|
| **Tab** | Navigate forward | All interactive elements |
| **Shift + Tab** | Navigate backward | All interactive elements |
| **Space** | Pause/resume animation | When animation focused |
| **Enter** | Activate button/link | Focused interactive element |
| **Arrow Left** | Previous quote | When quote area focused |
| **Arrow Right** | Next quote | When quote area focused |
| **Escape** | Close modal/dismiss error | When modal open |
| **Home** | Jump to page top | Anywhere |
| **End** | Jump to page bottom | Anywhere |

**Focus Indicators:**

```css
/* High-contrast focus ring */
*:focus-visible {
  outline: 3px solid var(--el-color-primary);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Dark mode focus ring */
body.dark-mode *:focus-visible {
  outline-color: var(--el-color-primary-light-3);
}

/* Remove outline for mouse users (but keep for keyboard) */
*:focus:not(:focus-visible) {
  outline: none;
}
```

---

#### **Color Blind Accessibility**

**Patterns Beyond Color:**

| Status | Color | Additional Indicator | Accessible? |
|--------|-------|---------------------|-------------|
| Queued | Gray | Hollow dot • | ✅ Yes |
| Active | Blue | Pulsing filled dot ● + animation | ✅ Yes |
| Completed | Green | Check mark ✓ | ✅ Yes |
| Error | Red | X mark ❌ + stop animation | ✅ Yes |

**Deuteranopia (Red-Green) Simulation:**

```css
/* Color palette adjustments for common color blindness */
@media (prefers-contrast: high) {
  .agent-card.active {
    border-color: #0066cc; /* Stronger blue */
    border-width: 3px;
  }

  .agent-card.completed {
    border-color: #006600; /* Darker green */
  }

  .agent-card.error {
    border-color: #cc0000; /* Darker red */
  }
}
```

---

#### **Cognitive Accessibility**

**Plain Language Principles:**

```
❌ WRONG: "Execution vectors 2/4 initialized."
✅ RIGHT: "Stage 2 of 4: Planning."

❌ WRONG: "Non-deterministic convergence failure."
✅ RIGHT: "Research failed because the query was too complex."

❌ WRONG: "Retry operation Y/N?"
✅ RIGHT: "[Retry Research] [Modify Query]" (clear button labels)
```

**Chunking Information:**

```
Don't overwhelm with text walls:

❌ WRONG:
"Your research has completed Stage 2 of 4 which is Planning
and is now moving to Stage 3 which is Parallel Research and
will take approximately 60-120 seconds..."

✅ RIGHT:
Stage 2: Planning ✓ (Completed)
Stage 3: Parallel Research • (In progress)
Estimated time: 1-2 minutes
```

---

#### **Motion & Animation Accessibility**

**Vestibular Disorder Support:**

```css
/* Completely disable complex animations */
@media (prefers-reduced-motion: reduce) {
  .tk9-origami-animation {
    animation: none !important;
  }

  .tk9-origami-animation svg {
    animation: simpleBreathe 3s ease-in-out infinite;
  }

  @keyframes simpleBreathe {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 1; }
  }

  .agent-card.active {
    animation: none !important;
    border-width: 3px; /* Static indicator instead */
  }
}
```

---

### 8.6 Responsive Testing Matrix

**Required Test Devices:**

| Category | Device | Screen | Browser | Priority |
|----------|--------|--------|---------|----------|
| **Mobile** | iPhone 12 | 390x844 | Safari 14+ | ⭐⭐⭐ High |
| **Mobile** | Samsung Galaxy S21 | 384x854 | Chrome 90+ | ⭐⭐ Medium |
| **Tablet** | iPad Air | 820x1180 | Safari 14+ | ⭐⭐ Medium |
| **Tablet** | iPad Pro | 1024x1366 | Safari 14+ | ⭐ Low |
| **Desktop** | MacBook Pro | 1440x900 | Chrome 90+ | ⭐⭐⭐ High |
| **Desktop** | Windows Desktop | 1920x1080 | Edge 90+ | ⭐⭐⭐ High |
| **Large** | 4K Monitor | 3840x2160 | Any | ⭐ Low |

**Accessibility Testing Tools:**

- [ ] **axe DevTools** - Automated accessibility audit
- [ ] **WAVE** - Visual accessibility evaluation
- [ ] **Lighthouse** - Performance + accessibility scoring
- [ ] **VoiceOver** (macOS) - Screen reader testing
- [ ] **NVDA** (Windows) - Screen reader testing
- [ ] **Keyboard Only** - Unplug mouse, navigate fully
- [ ] **Zoom 200%** - Ensure layout doesn't break
- [ ] **High Contrast Mode** - Windows high contrast theme
- [ ] **Color Blindness Simulator** - Chrome extension test

---

### 8.7 Performance Budget (Responsive Contexts)

| Metric | Mobile (3G) | Desktop (Broadband) |
|--------|-------------|---------------------|
| **First Contentful Paint** | <2s | <1s |
| **Time to Interactive** | <3.5s | <2s |
| **JavaScript Bundle** | <200KB (gzipped) | <400KB (gzipped) |
| **CSS Bundle** | <50KB (gzipped) | <100KB (gzipped) |
| **Animation Frame Rate** | 30fps minimum | 60fps target |
| **Memory Usage** | <50MB | <100MB |

**Mobile Optimization Strategies:**

```typescript
// Lazy load shapes on mobile
const isMobile = ref(window.innerWidth < 768)

const shapesToLoad = computed(() => {
  return isMobile.value
    ? shapes.slice(0, 10) // Load 10 simple shapes
    : shapes              // Load all 27 shapes
})

// Reduce animation complexity on low-end devices
const devicePerformance = ref<'low' | 'medium' | 'high'>('high')

onMounted(() => {
  // Simple heuristic: if device has <4GB RAM or slow CPU
  const memory = (navigator as any).deviceMemory || 4
  const cores = navigator.hardwareConcurrency || 4

  if (memory < 4 || cores < 4) {
    devicePerformance.value = 'low'
  }
})

const animationComplexity = computed(() => {
  if (devicePerformance.value === 'low') {
    return 'simple' // Use basic shapes, faster animations
  }
  return 'full' // Use all shapes, full 3D transforms
})
```

---

### 8.8 Responsive Design Checklist

Before deploying to production:

- [ ] **Tested on real devices** - Not just browser DevTools
- [ ] **Touch interactions verified** - Swipe, tap, scroll
- [ ] **Landscape orientation tested** - Mobile and tablet
- [ ] **Text remains readable** - No truncation at any breakpoint
- [ ] **Images scale properly** - Origami animation proportional
- [ ] **No horizontal scrolling** - At any viewport width
- [ ] **Interactive elements tappable** - 44px minimum touch targets
- [ ] **Performance acceptable** - <3s TTI on mobile 3G
- [ ] **Keyboard navigation works** - All breakpoints
- [ ] **Screen reader friendly** - Tested with VoiceOver/NVDA
- [ ] **High contrast mode** - Still usable in Windows high contrast
- [ ] **Zoom to 200%** - Layout doesn't break
- [ ] **Reduced motion tested** - Animation fallbacks work

---

## 9. Implementation Guidance

### 9.1 Developer Handoff Summary

**Document Status:** ✅ Complete - Ready for Implementation

This UX Design Specification comprehensively defines TK9's **Research Execution Waiting Experience** (Experience A), transforming the 3-5 minute research wait from anxious uncertainty into confident anticipation through origami animation + famous quotes + stage-by-stage progress visibility.

**Prepared For:** Frontend Development Team
**Date:** 2025-11-01
**Author:** Thinh (with BMad Method - Create UX Design Workflow v1.0)

---

### 9.2 Implementation Priority

**Phase 1: Core Waiting Experience (Week 1-2)** ⭐⭐⭐ Critical

Must-have components for MVP:

- [x] WaitingExperience.vue orchestrator component
- [x] OrigamiAnimation.vue with 10 basic shapes (Crane, Boat, Butterfly, Star, Book, Lightbulb, Telescope, Brain, Magnifying Glass, Scroll)
- [x] QuoteDisplay.vue with 70 stage-categorized quotes
- [x] StageProgress.vue with agent cards
- [x] Stage-specific animation speeds (3s/4s/3.5s/6s)
- [x] 10-second quote rotation
- [x] Basic mobile responsiveness (vertical stacking)
- [x] Error state with retry button
- [x] Success state with [View Results] button

**Expected Outcome:** Users experience transparent waiting with confidence building, eliminating "is this broken?" anxiety.

---

**Phase 2: Polish & Performance (Week 3)** ⭐⭐ High

Nice-to-have enhancements:

- [ ] All 27 origami shapes (add 17 remaining shapes)
- [ ] 20 curated color palettes (currently 10)
- [ ] Progress-based animation acceleration (25% faster near completion)
- [ ] Reduced motion fallback animations
- [ ] Touch gestures (swipe left/right to change quote)
- [ ] Keyboard navigation (Arrow keys, Space to pause)
- [ ] Dark mode optimization (desaturate colors 15%)
- [ ] Performance profiling (60fps target)

**Expected Outcome:** Polished, accessible experience that delights active watchers and respects user preferences.

---

**Phase 3: Advanced Features (Week 4)** ⭐ Medium

Optional enhancements for later:

- [ ] Browser notifications when user navigates away
- [ ] Stage transition micro-feedback (subtle sound effects)
- [ ] Quote favorites/bookmarking
- [ ] Animation complexity detection (low/medium/high end devices)
- [ ] Analytics tracking (which quotes resonate, how long users watch)
- [ ] A/B testing framework for quote effectiveness
- [ ] Export quote as image (share on social media)

**Expected Outcome:** Additional engagement features that turn users into advocates.

---

### 9.3 Technical Implementation Roadmap

**Step 1: Project Setup (Day 1)**

```bash
# Create component directory structure
mkdir -p web_dashboard/frontend_poc/src/components/WaitingExperience

# Create necessary files
cd web_dashboard/frontend_poc/src/components/WaitingExperience
touch WaitingExperience.vue
touch OrigamiAnimation.vue
touch QuoteDisplay.vue
touch StageProgress.vue
touch origami-shapes.ts
touch quotes-library.ts
touch color-palettes.ts
touch types.ts
```

**Step 2: Install Dependencies (Day 1)**

```bash
# Install required packages (if not already installed)
cd web_dashboard/frontend_poc
npm install @vueuse/core  # For useSwipe, useDebounceFn, etc.
```

**Step 3: Implement Core Components (Day 2-5)**

Priority Order:
1. **types.ts** - Define TypeScript interfaces first
2. **quotes-library.ts** - Copy 70 quotes from spec (Section 2.2)
3. **origami-shapes.ts** - Start with 10 basic shapes
4. **color-palettes.ts** - Start with 10 basic palettes
5. **OrigamiAnimation.vue** - Implement animation component
6. **QuoteDisplay.vue** - Implement quote rotation
7. **StageProgress.vue** - Implement agent cards
8. **WaitingExperience.vue** - Implement orchestrator

**Step 4: Integration (Day 6-7)**

```typescript
// web_dashboard/frontend_poc/src/views/ResearchExecutionView.vue
<template>
  <div class="research-execution-view">
    <WaitingExperience
      v-if="isExecuting"
      :session-id="currentSessionId"
      :current-stage="currentStage"
      :stage-progress="stageProgress"
      :stage-name="stageName"
      :active-agent="activeAgent"
      @complete="handleResearchComplete"
      @error="handleResearchError"
    />

    <CompletionView
      v-else-if="isComplete"
      :session-id="currentSessionId"
      :results="researchResults"
    />
  </div>
</template>
```

**Step 5: Testing & QA (Day 8-10)**

- [ ] Unit tests for all components (80% coverage minimum)
- [ ] Integration tests for timer logic
- [ ] Visual regression tests (Chromatic or Percy)
- [ ] Accessibility audit (axe DevTools)
- [ ] Performance profiling (Chrome DevTools)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile device testing (iPhone, Android)

**Step 6: Documentation (Day 11)**

- [ ] Component API documentation (props, events, slots)
- [ ] Usage examples for developers
- [ ] Storybook stories for each component
- [ ] Update project README with new feature

**Step 7: Deployment (Day 12-14)**

- [ ] Code review by senior developer
- [ ] Merge to development branch
- [ ] Deploy to staging environment
- [ ] User acceptance testing (UAT)
- [ ] Deploy to production (gradual rollout 10% → 50% → 100%)
- [ ] Monitor analytics for first 48 hours

---

### 9.4 Critical Implementation Notes

**DO:**
- ✅ Copy exact animation speeds from spec (3s/4s/3.5s/6s per stage)
- ✅ Use exact quote rotation timing (10 seconds)
- ✅ Maintain 8px vertical rhythm spacing
- ✅ Implement reduced motion fallbacks from Day 1
- ✅ Test with real user JWT tokens (not service_role)
- ✅ Use Element Plus components for consistency
- ✅ Profile performance before declaring "done"
- ✅ Test on real mobile devices (not just browser DevTools)

**DON'T:**
- ❌ Change animation speeds without UX approval
- ❌ Add features not in spec without user validation
- ❌ Skip accessibility requirements (WCAG AA mandatory)
- ❌ Forget to test dark mode
- ❌ Deploy without error state testing
- ❌ Assume timings "feel about right" - measure precisely
- ❌ Copy PlayfulLoadingAnimation.tsx as-is - adapt thoughtfully
- ❌ Create new design patterns - follow spec exactly

---

### 9.5 Component File Locations

```
web_dashboard/frontend_poc/src/
├── components/
│   └── WaitingExperience/
│       ├── WaitingExperience.vue              # Orchestrator (main component)
│       ├── OrigamiAnimation.vue               # Animation renderer
│       ├── QuoteDisplay.vue                   # Quote rotation display
│       ├── StageProgress.vue                  # Stage + agent cards
│       ├── SuccessView.vue                    # Completion state
│       ├── ErrorView.vue                      # Error state with retry
│       ├── origami-shapes.ts                  # 27 SVG shape definitions
│       ├── origami-animations.css             # CSS keyframes (from original)
│       ├── quotes-library.ts                  # 70 stage-categorized quotes
│       ├── color-palettes.ts                  # 20 curated color palettes
│       ├── types.ts                           # TypeScript interfaces
│       └── README.md                          # Component usage documentation
│
├── composables/
│   ├── useRotationTimer.ts                    # Reusable timer logic
│   └── useQuoteSwipe.ts                       # Swipe gesture support
│
├── stores/
│   └── sessionsStore.ts                       # Updated with stage progress state
│
└── views/
    └── ResearchExecutionView.vue              # Integration point
```

---

### 9.6 Quality Assurance Checklist

**Before Code Review:**

- [ ] All TypeScript errors resolved (npm run typecheck)
- [ ] All ESLint warnings resolved (npm run lint)
- [ ] Unit tests passing (npm run test)
- [ ] Component renders in Storybook
- [ ] Dark mode tested visually
- [ ] Mobile breakpoint tested (390px width minimum)
- [ ] Reduced motion tested (DevTools: Rendering > Emulate CSS prefers-reduced-motion)

**Before Staging Deployment:**

- [ ] Integration tests passing
- [ ] Visual regression tests approved
- [ ] Performance metrics within budget (see Section 8.7)
- [ ] Accessibility audit passing (axe score 100)
- [ ] Screen reader tested (VoiceOver or NVDA)
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] Real device tested (iPhone + Android)

**Before Production Deployment:**

- [ ] UAT completed by product owner
- [ ] Analytics tracking implemented
- [ ] Error monitoring configured (Sentry/LogRocket)
- [ ] Rollback plan documented
- [ ] Feature flag enabled for gradual rollout
- [ ] Documentation updated (user guide + developer docs)

---

### 9.7 Success Metrics & Monitoring

**Quantitative Metrics (Track in Analytics):**

| Metric | Baseline (Before) | Target (After) | How to Measure |
|--------|-------------------|----------------|----------------|
| **"Is this broken?" support tickets** | 5-10/week | <1/week | Zendesk/Intercom |
| **Research completion rate** | 85% | >95% | Backend logs |
| **User satisfaction score** | 3.2/5 | >4.5/5 | Post-research survey |
| **Active watcher rate** | Unknown | >15% | Time on page >3min |
| **Retry after error** | 60% | >90% | Error analytics |
| **Mobile usage** | Unknown | >30% | Device analytics |

**Qualitative Metrics (User Interviews):**

Sample Questions:
- "How confident did you feel that research was progressing correctly?"
- "Did you understand what stage the system was in at any given time?"
- "Did the wait feel longer or shorter than 3-5 minutes?"
- "Would you recommend TK9 to a colleague based on this experience?"

**Analytics Events to Track:**

```typescript
// Track key user interactions
analytics.track('Research Started', {
  sessionId: string,
  researchTitle: string,
  userId: string
})

analytics.track('Stage Transition', {
  sessionId: string,
  fromStage: number,
  toStage: number,
  elapsedTime: number
})

analytics.track('Quote Viewed', {
  sessionId: string,
  stage: number,
  quoteText: string,
  quoteAuthor: string,
  viewDuration: number // How long visible
})

analytics.track('Animation Paused', {
  sessionId: string,
  stage: number,
  pauseDuration: number
})

analytics.track('Research Error', {
  sessionId: string,
  stage: number,
  errorType: string,
  retryAttempt: number
})

analytics.track('Research Completed', {
  sessionId: string,
  totalDuration: number,
  stagesCompleted: number,
  userWatchedFullExecution: boolean
})
```

---

### 9.8 Known Limitations & Future Improvements

**Current Limitations:**

1. **Quote Library Static** - 70 quotes hardcoded, cannot add/remove without code change
   - **Future:** Admin panel to manage quote library

2. **Single Language** - Quotes only in English
   - **Future:** i18n support, localized quote libraries

3. **No Personalization** - Same experience for all users
   - **Future:** User preferences (favorite quotes, animation speed, dark mode by default)

4. **No Draft Preview** - Users can't preview drafts during execution
   - **Future:** Progressive disclosure of draft artifacts as they're created

5. **Limited Error Recovery** - Only supports simple retry
   - **Future:** Suggest query modifications, partial recovery from failed stages

---

### 9.9 Reference Materials

**Source Inspiration:**
- `/Users/thinhkhuat/»DEV•local«/CC_viet_translator/components/TranslatorEditor/PlayfulLoadingAnimation.tsx` - Original React implementation (1911 lines)

**Design System:**
- Element Plus Documentation: https://element-plus.org/
- Inter Font: https://rsms.me/inter/
- Crimson Pro Font: https://fonts.google.com/specimen/Crimson+Pro

**Interactive Deliverables:**
- Color Theme Visualizer: `docs/ux-color-themes.html`
- Design Direction Mockup: `docs/ux-design-directions.html`

**Related Documentation:**
- Product Requirements: `docs/PRD.md`
- Product Brief: `docs/product-brief-TK9-2025-10-31.md`
- Architecture: `docs/architecture.md`
- Story 1.4 (RLS Policies): `docs/stories/1-4-row-level-security-rls-policies-implementation.md`

---

### 9.10 Contact & Support

**Questions During Implementation?**

| Question Type | Contact | Response Time |
|---------------|---------|---------------|
| **UX Clarifications** | Thinh (Product Owner) | Same day |
| **Technical Architecture** | Lead Developer | 2-4 hours |
| **Design System** | Element Plus Docs | Self-service |
| **Accessibility** | A11y Specialist | 1-2 days |

**Feedback Loop:**

- **Daily Standups:** Share progress, blockers
- **Mid-Implementation Review (Day 7):** Demo core components
- **Pre-Deployment Review (Day 11):** Final walkthrough
- **Post-Launch Retrospective (Week 3):** What worked, what didn't

---

### 9.11 Final Implementation Checklist

**Before declaring "Done":**

- [ ] All Phase 1 (Critical) items implemented
- [ ] At least 80% Phase 2 (High) items implemented
- [ ] All quality assurance checks passed
- [ ] User acceptance testing completed
- [ ] Analytics tracking verified
- [ ] Documentation complete (code + user guide)
- [ ] Deployed to production (100% rollout)
- [ ] Success metrics baseline established
- [ ] Team trained on new feature
- [ ] Support team briefed on expected user questions

---

## 🎉 Implementation Complete

This UX Design Specification provides everything needed to implement TK9's Research Execution Waiting Experience. Follow the roadmap, maintain the patterns, measure the metrics, and iterate based on user feedback.

**Remember:** This experience is the bridge between user anxiety and user confidence. Every detail matters. Build it with care.

**Good luck, and happy coding!** 🚀

---

## Appendix

### Related Documents

- Product Requirements: `docs/PRD.md`
- Product Brief: `docs/product-brief-TK9-2025-10-31.md`
- Architecture: `docs/architecture.md`

### Core Interactive Deliverables

This UX Design Specification was created through visual collaboration:

- **Color Theme Visualizer**: `docs/ux-color-themes.html`
- **Design Direction Mockups**: `docs/ux-design-directions.html`

### Version History

| Date       | Version | Changes                         | Author |
| ---------- | ------- | ------------------------------- | ------ |
| 2025-11-01 | 1.0     | Initial UX Design Specification | Thinh  |
