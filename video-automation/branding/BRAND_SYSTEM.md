# SBDK.dev Video Series Brand System

## Brand Overview

SBDK.dev represents the future of local-first data pipeline development. Our visual identity combines:
- **Terminal aesthetics** with modern polish
- **Developer-focused** design with broad accessibility
- **Data pipeline visualization** that makes complex concepts intuitive
- **Professional quality** suitable for enterprise and education

## Color Palette

### Primary Colors
```css
/* Core Brand Colors */
--sbdk-primary: #00D4AA;      /* Teal - Data flow, success, growth */
--sbdk-secondary: #6366F1;    /* Indigo - Technology, reliability */
--sbdk-accent: #F59E0B;       /* Amber - Highlights, energy, speed */

/* Dark Theme Foundation */
--sbdk-dark-bg: #0F172A;      /* Slate 900 - Main background */
--sbdk-dark-surface: #1E293B; /* Slate 800 - Cards, panels */
--sbdk-dark-border: #334155;  /* Slate 700 - Borders, dividers */

/* Text Colors */
--sbdk-text-primary: #F8FAFC;  /* Slate 50 - Primary text */
--sbdk-text-secondary: #CBD5E1; /* Slate 300 - Secondary text */
--sbdk-text-muted: #94A3B8;    /* Slate 400 - Muted text */
```

### Supporting Colors
```css
/* Status Colors */
--sbdk-success: #10B981;      /* Emerald 500 - Success states */
--sbdk-warning: #F59E0B;      /* Amber 500 - Warnings */
--sbdk-error: #EF4444;        /* Red 500 - Errors */
--sbdk-info: #3B82F6;         /* Blue 500 - Information */

/* Pipeline Flow Colors */
--sbdk-pipeline-extract: #8B5CF6;  /* Purple - Data extraction */
--sbdk-pipeline-transform: #06B6D4; /* Cyan - Data transformation */
--sbdk-pipeline-load: #10B981;      /* Green - Data loading */

/* Terminal Colors */
--sbdk-terminal-green: #4ADE80;   /* Bright green - Success output */
--sbdk-terminal-yellow: #FACC15;  /* Yellow - Warnings */
--sbdk-terminal-red: #F87171;     /* Red - Errors */
--sbdk-terminal-blue: #60A5FA;    /* Blue - Information */
```

## Typography System

### Primary Font Stack
```css
/* Code/Terminal Font */
font-family: "JetBrains Mono", "Fira Code", "SF Mono", "Monaco", "Cascadia Code", monospace;

/* UI Font */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Typography Scale
```css
/* Video Title Cards */
.title-hero: 72px/1.1 bold;
.title-main: 48px/1.2 bold;
.title-sub: 32px/1.3 medium;

/* Body Text */
.body-large: 24px/1.4 regular;
.body-medium: 18px/1.5 regular;
.body-small: 16px/1.5 regular;

/* Code/Terminal */
.code-large: 20px/1.4 monospace;
.code-medium: 16px/1.4 monospace;
.code-small: 14px/1.4 monospace;

/* Lower Thirds */
.lower-third-title: 28px/1.2 bold;
.lower-third-subtitle: 18px/1.3 medium;
```

## Logo Concepts

### Primary Logo
```
🚀 SBDK.dev
   ────────
   Sandbox Development Kit
```

### Animated Logo Variations

#### 1. Terminal Boot Sequence
```
Frame 1: $ _
Frame 2: $ sbdk_
Frame 3: $ sbdk init_
Frame 4: $ sbdk init pipeline_
Frame 5: 🚀 SBDK.dev [glow effect]
```

#### 2. Data Pipeline Flow
```
Raw Data → [🔄 DLT] → [🦆 DuckDB] → [📈 dbt] → Analytics
         ↓
    🚀 SBDK.dev
```

#### 3. Minimalist Pulse
```
SBDK.dev with subtle pulsing glow on the rocket emoji
Color shifts: Primary → Secondary → Accent → Primary
Duration: 3 seconds loop
```

## Title Card Designs

### Template 1: Code-First
```
Background: Dark gradient (--sbdk-dark-bg to --sbdk-dark-surface)
Layout:
┌─────────────────────────────────────────┐
│ $ sbdk init my_pipeline                 │
│                                         │
│   🚀 Building Modern Data Pipelines    │
│      with SBDK.dev                     │
│                                         │
│   Episode 01: Local-First Development  │
│                                         │
└─────────────────────────────────────────┘

Elements:
- Terminal-style header with typing animation
- Main title in bright teal (#00D4AA)
- Episode info in muted text (#94A3B8)
- Subtle code syntax highlighting
```

### Template 2: Visual Workflow
```
Background: Dark theme with subtle data visualization
Layout:
┌─────────────────────────────────────────┐
│     Data Pipeline Fundamentals         │
│                                         │
│  Raw → DLT → DuckDB → dbt → Analytics  │
│   │     │      │       │        │      │
│   └─────┼──────┼───────┼────────┘      │
│         ▼      ▼       ▼               │
│     🚀 SBDK.dev Made Simple            │
│                                         │
│     Episode 02: Understanding ETL      │
└─────────────────────────────────────────┘

Elements:
- Animated flow diagram
- Color-coded pipeline stages
- Clean typography hierarchy
```

### Template 3: Feature Focus
```
Background: Terminal screenshot with blur overlay
Layout:
┌─────────────────────────────────────────┐
│                                         │
│    ⚡ 11x Faster Installation           │
│    🏠 100% Local Development           │
│    📦 Out-of-the-Box Ready             │
│                                         │
│         SBDK.dev Features              │
│                                         │
│    Episode 03: Speed & Simplicity     │
│                                         │
└─────────────────────────────────────────┘

Elements:
- Feature highlights with icons
- Strong contrast ratios
- Emphasis on key benefits
```

## YouTube Thumbnail Templates

### Template A: Split Screen
```
Left Side (60%): Live terminal session with colorful output
Right Side (40%): 
  - Large "SBDK.dev" logo
  - Episode number in accent color
  - Key benefit text
  - Progress indicator or data visualization

Design Elements:
- High contrast for mobile visibility
- Bright accent colors for CTR
- Clear typography readable at small sizes
```

### Template B: Before/After
```
Top Half: "Traditional Way" - Complex setup, multiple tools
  - Docker logos, cloud icons, complex diagrams
  - Red/orange color scheme suggesting difficulty

Bottom Half: "SBDK Way" - Clean terminal, simple command
  - Single command: "sbdk init pipeline"
  - Green/teal color scheme suggesting simplicity
  - 🚀 rocket emoji for impact

Center Banner: "11x FASTER" or "100% LOCAL"
```

### Template C: Code Hero
```
Background: Beautiful terminal session with SBDK commands
Overlay Elements:
  - Semi-transparent dark panel
  - Large episode title
  - SBDK.dev logo
  - Key visual (chart, pipeline diagram, etc.)
  - Bright accent elements for click appeal

Typography:
  - Bold, high-contrast text
  - Multiple font sizes for hierarchy
  - Code snippets for authenticity
```

## Lower Third Graphics

### Design System
```css
.lower-third {
  background: linear-gradient(135deg, 
    rgba(0, 212, 170, 0.9) 0%, 
    rgba(99, 102, 241, 0.9) 100%);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 16px 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
```

### Content Templates

#### Key Concept
```
┌─────────────────────────────────────┐
│ 🔑 Key Concept                     │
│    Local-First Development         │
│    No cloud dependencies needed    │
└─────────────────────────────────────┘
```

#### Command Spotlight
```
┌─────────────────────────────────────┐
│ 💻 Command Spotlight               │
│    $ sbdk init my_pipeline         │
│    Creates complete project        │
└─────────────────────────────────────┘
```

#### Performance Metric
```
┌─────────────────────────────────────┐
│ ⚡ Performance                     │
│    11x Faster Installation         │
│    30 seconds to working pipeline  │
└─────────────────────────────────────┘
```

#### Tool Comparison
```
┌─────────────────────────────────────┐
│ 🆚 SBDK vs Traditional             │
│    Setup: 30s vs 4+ hours         │
│    Cost: $0 vs $200-2000/month    │
└─────────────────────────────────────┘
```

## Transition Effects

### 1. Terminal Fade
- Fade out current content
- Brief terminal cursor blink
- Fade in new content with typing effect
- Duration: 1.5 seconds

### 2. Data Flow
- Content slides out following data pipeline direction
- Brief pipeline diagram animation
- New content slides in from pipeline endpoint
- Duration: 2 seconds

### 3. Code Block Swap
- Current content transforms into code block
- Code block "executes" with terminal output
- Output becomes new content
- Duration: 2.5 seconds

### 4. Split Terminal
- Screen splits vertically like tmux/terminal
- Old content in left pane, new in right pane
- Left pane fades out, right pane expands
- Duration: 2 seconds

## End Card Templates

### Template 1: Call-to-Action Focus
```
Background: Dark theme with subtle SBDK pattern
Layout:
┌─────────────────────────────────────────┐
│              Ready to Start?            │
│                                         │
│     $ pip install sbdk-dev             │
│     $ sbdk init my_first_pipeline      │
│                                         │
│   [Subscribe Button]  [Next Video]     │
│                                         │
│        🚀 SBDK.dev                     │
│        Start Building Today            │
└─────────────────────────────────────────┘
```

### Template 2: Series Navigation
```
Background: Terminal grid pattern
Layout:
┌─────────────────────────────────────────┐
│           Continue Learning             │
│                                         │
│  [Prev] Episode 02: DLT Pipelines [Next]│
│         Episode 04: dbt Models          │
│                                         │
│         Full Playlist ↗                │
│                                         │
│    Don't forget to subscribe! 🔔       │
└─────────────────────────────────────────┘
```

### Template 3: Community Focus
```
Background: Code editor with SBDK project
Layout:
┌─────────────────────────────────────────┐
│          Join the Community             │
│                                         │
│  GitHub: github.com/sbdk-dev/sbdk-dev  │
│  Issues: Report bugs & request features │
│  Docs: docs.sbdk.dev (coming soon)     │
│                                         │
│        Star ⭐ if this helped!         │
│                                         │
│     [Subscribe] [GitHub] [Discord]      │
└─────────────────────────────────────────┘
```

## Animation Guidelines

### Timing
- Logo animations: 3-4 seconds
- Transitions: 1.5-2.5 seconds
- Lower thirds: 4-6 seconds on screen
- End cards: 8-10 seconds minimum

### Easing
- Use smooth easing curves (ease-in-out)
- Avoid harsh linear transitions
- Terminal typing: Variable speed for realism
- Data flow: Consistent speed with slight acceleration

### Performance
- 60fps for smooth playback
- Optimize for 1080p primary, 4K optional
- Consider mobile viewing (smaller screens)
- High contrast for accessibility

## Usage Guidelines

### Do's
- ✅ Use high contrast ratios (4.5:1 minimum)
- ✅ Keep text readable at thumbnail size
- ✅ Maintain consistent brand colors
- ✅ Use terminal aesthetics authentically
- ✅ Show real code and commands
- ✅ Emphasize speed and simplicity

### Don'ts
- ❌ Use low contrast color combinations
- ❌ Overcrowd thumbnails with text
- ❌ Mix brand colors inconsistently
- ❌ Fake terminal sessions
- ❌ Hide the developer-first nature
- ❌ Make data pipelines look intimidating

## File Organization

### Recommended Structure
```
video-assets/
├── brand/
│   ├── logos/
│   │   ├── sbdk-logo-light.svg
│   │   ├── sbdk-logo-dark.svg
│   │   └── sbdk-animated.gif
│   ├── colors/
│   │   └── palette.ase
│   └── fonts/
│       ├── JetBrainsMono-Regular.woff2
│       └── Inter-Variable.woff2
├── templates/
│   ├── title-cards/
│   │   ├── code-first.psd
│   │   ├── visual-workflow.psd
│   │   └── feature-focus.psd
│   ├── thumbnails/
│   │   ├── split-screen.psd
│   │   ├── before-after.psd
│   │   └── code-hero.psd
│   ├── lower-thirds/
│   │   ├── key-concept.aep
│   │   ├── command-spotlight.aep
│   │   └── performance.aep
│   └── end-cards/
│       ├── cta-focus.psd
│       ├── series-nav.psd
│       └── community.psd
└── examples/
    ├── episode-01-renders/
    ├── episode-02-renders/
    └── style-guide.pdf
```

This brand system creates a cohesive visual identity that makes data pipelines approachable while maintaining the technical authenticity that developers expect. The design emphasizes SBDK.dev's core strengths: speed, simplicity, and local-first development.