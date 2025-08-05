# SBDK.dev Visual Assets Specifications

## Asset Library Overview

This document provides detailed specifications for creating all visual assets for the SBDK.dev video series, ensuring consistency and professional quality across all content.

## 1. Logo Assets

### Primary Logo Specifications

#### Standard Logo
```
File: sbdk-logo-standard.svg
Dimensions: 400x100px (4:1 ratio)
Colors: 
  - Rocket: #F59E0B (Amber)
  - Text: #00D4AA (Primary Teal)
  - Tagline: #CBD5E1 (Light Gray)

Text: "🚀 SBDK.dev"
Tagline: "Sandbox Development Kit"
Font: Inter Bold for main text, Inter Medium for tagline
```

#### Horizontal Logo
```
File: sbdk-logo-horizontal.svg
Dimensions: 600x120px (5:1 ratio)
Layout: Rocket + "SBDK.dev" + vertical separator + "Sandbox Development Kit"
Use case: Video headers, wide layouts
```

#### Logo Mark Only
```
File: sbdk-logomark.svg
Dimensions: 120x120px (1:1 ratio)
Content: Stylized rocket emoji with brand colors
Use case: Favicons, social media profile pictures, watermarks
```

### Animated Logo Variations

#### Terminal Boot Animation
```
File: sbdk-logo-boot.gif
Duration: 4 seconds
Frame Rate: 30fps
Dimensions: 800x200px

Animation Sequence:
Frame 0-30: $ cursor blinks
Frame 31-60: $ sbdk_ (typing effect)
Frame 61-90: $ sbdk init_ 
Frame 91-120: $ sbdk init pipeline_
Frame 121-150: Command executes, cursor disappears
Frame 151-180: 🚀 SBDK.dev fades in with glow effect
```

#### Pulse Animation
```
File: sbdk-logo-pulse.gif
Duration: 3 seconds (loop)
Frame Rate: 60fps
Dimensions: 400x100px

Animation: Subtle pulsing glow around rocket emoji
Colors cycle: Teal → Indigo → Amber → Teal
Opacity range: 0.8 to 1.0
```

## 2. Title Card Templates

### Template A: Code-First Design

#### Layout Specifications
```
Canvas: 1920x1080px
Background: Linear gradient from #0F172A to #1E293B
Grid: 24px baseline grid

Header Section (0-200px):
  Terminal prompt: "$ sbdk init my_pipeline"
  Font: JetBrains Mono, 24px
  Color: #4ADE80
  Position: 48px from left, 48px from top

Main Title Section (200-600px):
  Primary: "Building Modern Data Pipelines"
  Font: Inter Bold, 72px, Line height: 1.1
  Color: #00D4AA
  Position: Centered horizontally, 280px from top
  
  Secondary: "with SBDK.dev"
  Font: Inter Medium, 48px
  Color: #F8FAFC
  Position: Centered, 32px below primary

Episode Section (600-900px):
  Text: "Episode 01: Local-First Development"
  Font: Inter Regular, 32px
  Color: #94A3B8
  Position: Centered, 680px from top

Footer Section (900-1080px):
  Logo: Small SBDK logomark
  Position: Bottom right, 48px margins
```

#### Export Settings
```
Formats: PSD (editable), PNG (web), JPG (backup)
Color Profile: sRGB
Resolution: 300 DPI for print, 72 DPI for web
```

### Template B: Visual Workflow Design

#### Layout Specifications
```
Canvas: 1920x1080px
Background: Dark navy (#0F172A) with subtle data visualization pattern

Title Section (0-300px):
  Text: "Data Pipeline Fundamentals"
  Font: Inter Bold, 64px
  Color: #F8FAFC
  Position: Centered, 120px from top

Pipeline Diagram Section (300-700px):
  Flow: Raw Data → DLT → DuckDB → dbt → Analytics
  
  Boxes: 
    - Size: 140x80px each
    - Background: rgba(99, 102, 241, 0.2)
    - Border: 2px solid #6366F1
    - Radius: 8px
    
  Arrows:
    - Color: #00D4AA
    - Width: 4px
    - Animated flow effect
    
  Icons:
    - Raw Data: 📊
    - DLT: 🔄
    - DuckDB: 🦆
    - dbt: 📈
    - Analytics: ✨

Logo Section (700-900px):
  Text: "🚀 SBDK.dev Made Simple"
  Font: Inter Bold, 48px
  Color: #00D4AA

Episode Section (900-1080px):
  Text: "Episode 02: Understanding ETL"
  Font: Inter Regular, 28px
  Color: #CBD5E1
```

### Template C: Feature Focus Design

#### Layout Specifications
```
Canvas: 1920x1080px
Background: Blurred terminal screenshot with dark overlay (opacity: 0.7)

Features List (200-700px):
  Layout: Centered column
  
  Feature Items:
    - "⚡ 11x Faster Installation"
    - "🏠 100% Local Development"
    - "📦 Out-of-the-Box Ready"
    - "🎯 Intelligent Guided UI"
  
  Font: Inter Bold, 42px
  Color: #F8FAFC
  Line Height: 1.4
  Icon Color: #F59E0B

Main Title (750-850px):
  Text: "SBDK.dev Features"
  Font: Inter Bold, 56px
  Color: #00D4AA

Episode Info (850-1000px):
  Text: "Episode 03: Speed & Simplicity"
  Font: Inter Medium, 32px
  Color: #94A3B8
```

## 3. YouTube Thumbnail Specifications

### Template A: Split Screen Comparison

#### Layout Specifications
```
Canvas: 1280x720px (YouTube standard)
Safe Area: 1200x680px (40px margins)

Left Panel (0-768px):
  Title: "Traditional Way"
  Background: Red gradient (#EF4444 to #DC2626)
  Content: Complex diagram with multiple tools
  Icons: Docker, AWS, Kubernetes logos
  Text: "Hours of Setup"

Right Panel (768-1280px):
  Title: "SBDK Way"
  Background: Teal gradient (#00D4AA to #059669)
  Content: Single terminal command
  Command: "$ sbdk init pipeline"
  Text: "30 Seconds"

Center Badge:
  Text: "11x FASTER"
  Background: #F59E0B
  Font: Inter Black, 36px
  Position: Overlapping both panels
```

### Template B: Code Hero

#### Layout Specifications
```
Canvas: 1280x720px
Background: Beautiful terminal session (high contrast)

Terminal Content:
  - $ sbdk init my_analytics_project
  - $ cd my_analytics_project && sbdk run
  - [Animated progress bars]
  - ✅ Pipeline complete! 10K users, 50K events loaded

Overlay Panel (300x400px):
  Position: Top right
  Background: rgba(15, 23, 42, 0.9)
  Border: 2px solid #00D4AA
  Backdrop Filter: blur(10px)
  
  Content:
    - Episode number: Large, #F59E0B
    - Title: Bold, #F8FAFC
    - SBDK.dev logo
    - Key benefit badge

Typography:
  - Terminal: JetBrains Mono, 18px
  - Overlay: Inter, various weights
  - High contrast ratios (7:1 minimum)
```

### Template C: Before/After Transformation

#### Layout Specifications
```
Canvas: 1280x720px
Top Half (0-360px):
  Label: "BEFORE: Traditional Data Pipelines"
  Background: Dark red gradient
  Content: Complex architecture diagram
  Elements: Multiple services, cloud dependencies
  Text Overlay: "Complex • Expensive • Slow"

Bottom Half (360-720px):
  Label: "AFTER: SBDK.dev"
  Background: Teal gradient
  Content: Simple local setup
  Command: "sbdk init pipeline"
  Text Overlay: "Simple • Free • Fast"

Center Divider:
  Arrow pointing down
  Text: "SIMPLIFIED"
  Color: #F59E0B
```

## 4. Lower Third Graphics

### Design System

#### Base Component
```
Dimensions: 600x120px
Background: Linear gradient 135deg
  - Start: rgba(0, 212, 170, 0.9)
  - End: rgba(99, 102, 241, 0.9)
Border Radius: 12px
Drop Shadow: 0 8px 32px rgba(0, 0, 0, 0.3)
Backdrop Filter: blur(12px)
Border: 1px solid rgba(255, 255, 255, 0.1)
```

#### Typography
```
Icon: 24px, Color: #FBBF24
Title: Inter Bold, 20px, Color: #F8FAFC
Subtitle: Inter Regular, 14px, Color: #E2E8F0
Line Height: 1.3 for all text
```

#### Animation
```
Entry: Slide in from left with bounce
Duration: 0.8 seconds
Easing: cubic-bezier(0.68, -0.55, 0.265, 1.55)
Exit: Fade out with scale down
Duration: 0.5 seconds
```

### Content Variations

#### Key Concept Lower Third
```
Icon: 🔑
Title: "Key Concept"
Subtitle: "Local-First Development"
Additional: "No cloud dependencies needed"
Duration: 5 seconds
```

#### Performance Metric
```
Icon: ⚡
Title: "Performance Boost"
Subtitle: "11x Faster Installation"
Additional: "30 seconds vs 4+ hours traditional setup"
Duration: 6 seconds
```

#### Command Spotlight
```
Icon: 💻
Title: "Command Spotlight"
Subtitle: "$ sbdk init my_pipeline"
Additional: "Creates complete project structure"
Duration: 7 seconds
```

#### Tool Comparison
```
Icon: 🆚
Title: "SBDK vs Traditional"
Subtitle: "Setup Time: 30s vs 4+ hours"
Additional: "Monthly Cost: $0 vs $200-2000"
Duration: 8 seconds
```

## 5. End Card Templates

### Template A: Call-to-Action Focus

#### Layout Specifications
```
Canvas: 1920x1080px
Background: Dark theme (#0F172A) with subtle code pattern

Header Section (100-300px):
  Text: "Ready to Start Building?"
  Font: Inter Bold, 48px
  Color: #F8FAFC
  Position: Centered

Command Section (300-550px):
  Background: Terminal-style panel
  Commands:
    - "$ pip install sbdk-dev"
    - "$ sbdk init my_first_pipeline"
    - "$ sbdk run"
  Font: JetBrains Mono, 24px
  Colors: Terminal green (#4ADE80)

Action Buttons (550-750px):
  Subscribe Button:
    - Size: 200x60px
    - Background: #FF0000 (YouTube red)
    - Text: "Subscribe"
    - Font: Inter Bold, 18px
    
  Next Video Button:
    - Size: 200x60px
    - Background: #6366F1
    - Text: "Next Video"
    - Font: Inter Bold, 18px

Footer (750-1000px):
  Logo: SBDK.dev with tagline
  Text: "Start Building Today"
  Social icons: GitHub, Discord, Twitter
```

### Template B: Series Navigation

#### Layout Specifications
```
Canvas: 1920x1080px
Background: Grid pattern suggesting terminal/code

Title (150-250px):
  Text: "Continue Your Learning Journey"
  Font: Inter Bold, 40px
  Color: #F8FAFC

Navigation Grid (300-700px):
  Layout: 2x2 grid of video thumbnails
  
  Each Thumbnail:
    - Size: 320x180px
    - Background: Thumbnail preview
    - Overlay: Episode title and number
    - Border: 3px solid #00D4AA when highlighted
    - Hover effect: Scale 1.05

Current Episode Highlight:
  - Larger thumbnail: 400x225px
  - "YOU ARE HERE" badge
  - Accent border color

Playlist Link (750-850px):
  Text: "View Full Playlist"
  Icon: External link
  Button style with hover animation

Subscribe Reminder (900-1000px):
  Text: "Don't forget to subscribe for more!"
  Bell icon: 🔔
  Animated bell ring on hover
```

## 6. Animation Specifications

### Transition Effects

#### Terminal Fade Transition
```
Duration: 1.5 seconds
Frames: 45 (30fps)

Sequence:
1. Current content fades to 0.3 opacity (0.5s)
2. Terminal cursor blinks 3 times (0.5s)
3. New content types in with realistic timing (0.5s)

CSS Equivalent:
@keyframes terminalFade {
  0% { opacity: 1; }
  33% { opacity: 0.3; }
  66% { opacity: 0.3; }
  100% { opacity: 1; }
}
```

#### Data Flow Transition
```
Duration: 2 seconds
Frames: 60 (30fps)

Sequence:
1. Content slides out following data flow direction (0.7s)
2. Pipeline diagram animates data flow (0.6s)
3. New content slides in from endpoint (0.7s)

Easing: ease-in-out for slides, linear for data flow
```

#### Code Block Transformation
```
Duration: 2.5 seconds
Frames: 75 (30fps)

Sequence:
1. Content morphs into code block shape (0.8s)
2. Terminal execution animation (0.9s)
3. Output transforms into new content (0.8s)

Special Effects:
- Syntax highlighting during transformation
- Realistic typing speed variations
- Terminal cursor behavior
```

### Logo Animations

#### Boot Sequence Animation
```
Total Duration: 4 seconds
Frame Rate: 30fps
Dimensions: Variable (scalable SVG)

Keyframes:
0s: Empty terminal with blinking cursor
1s: "$ sbdk" typed
2s: "$ sbdk init" typed
3s: "$ sbdk init pipeline" typed
3.5s: Command executes, output starts
4s: Logo reveals with glow effect

Technical Notes:
- Use monospace font throughout
- Realistic typing speed (40-60 CPM)
- Terminal green (#4ADE80) for text
- Smooth glow transition using CSS filters
```

## 7. File Organization Structure

### Asset Directory Structure
```
sbdk-video-assets/
├── 01-brand/
│   ├── logos/
│   │   ├── sbdk-logo-standard.svg
│   │   ├── sbdk-logo-horizontal.svg
│   │   ├── sbdk-logomark.svg
│   │   ├── sbdk-logo-boot.gif
│   │   └── sbdk-logo-pulse.gif
│   ├── colors/
│   │   ├── sbdk-palette.ase (Adobe Swatch)
│   │   ├── sbdk-palette.gpl (GIMP)
│   │   └── colors.json
│   └── fonts/
│       ├── Inter-Variable.woff2
│       └── JetBrainsMono-Variable.woff2
├── 02-templates/
│   ├── title-cards/
│   │   ├── code-first-template.psd
│   │   ├── visual-workflow-template.psd
│   │   └── feature-focus-template.psd
│   ├── thumbnails/
│   │   ├── split-screen-template.psd
│   │   ├── code-hero-template.psd
│   │   └── before-after-template.psd
│   ├── lower-thirds/
│   │   ├── base-component.aep
│   │   ├── key-concept.aep
│   │   ├── performance-metric.aep
│   │   ├── command-spotlight.aep
│   │   └── tool-comparison.aep
│   └── end-cards/
│       ├── cta-focus-template.psd
│       ├── series-navigation-template.psd
│       └── community-focus-template.psd
├── 03-episodes/
│   ├── ep01-why-local-first/
│   │   ├── title-card.png
│   │   ├── thumbnail-variants/
│   │   │   ├── thumbnail-a.jpg
│   │   │   ├── thumbnail-b.jpg
│   │   │   └── thumbnail-c.jpg
│   │   ├── lower-thirds/
│   │   └── end-card.png
│   ├── ep02-first-pipeline/
│   └── [additional episodes]
├── 04-animations/
│   ├── transitions/
│   │   ├── terminal-fade.aep
│   │   ├── data-flow.aep
│   │   └── code-transform.aep
│   ├── logo-animations/
│   └── ui-elements/
└── 05-exports/
    ├── youtube-ready/
    ├── social-media/
    └── web-optimized/
```

## 8. Technical Specifications

### Color Profiles
- **Video Production:** Rec. 709 color space
- **Web Assets:** sRGB color space
- **Print Assets:** Adobe RGB color space

### Resolution Standards
- **4K Production:** 3840x2160px (future-proofing)
- **HD Delivery:** 1920x1080px (primary)
- **YouTube Thumbnails:** 1280x720px (minimum)
- **Social Media:** Various platform-specific sizes

### File Formats
- **Vector Graphics:** SVG (web), AI (editing)
- **Raster Graphics:** PNG (transparency), JPG (photos)
- **Video:** MP4 H.264 (delivery), ProRes (editing)
- **Audio:** WAV (editing), AAC (delivery)

### Naming Conventions
```
Format: [type]-[description]-[variant]-[size].[ext]

Examples:
- logo-sbdk-standard-400px.svg
- thumbnail-ep01-split-screen-1280x720.jpg
- title-card-code-first-1920x1080.png
- lower-third-key-concept-animated.aep
```

This comprehensive specification ensures all visual assets maintain consistency, professional quality, and brand alignment across the entire SBDK.dev video series.