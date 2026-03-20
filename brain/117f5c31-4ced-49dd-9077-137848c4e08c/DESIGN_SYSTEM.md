# 🎨 Design System: Pet Passport

**Role:** UI/UX Designer (Vibe Coding Mode)
**Concept:** "Official Cute" - A mix of serious bureaucratic aesthetics (stamps, holograms) with adorable, vibrant pet elements.

## 1. 🌈 Color Palette (Tailwind Classes)
- **Primary (Core Identity)**: `bg-indigo-600` (Official Badge Blue)
- **Secondary (Fun/Pop)**: `bg-pink-500` (Stamps, Hearts, Highlights)
- **Background**: `bg-slate-50` (Clean Paper Texture Feel)
- **Accent (Hologram Effect)**: `bg-gradient-to-r from-sky-400 via-rose-400 to-lime-400` (For the shiny laminate effect)
- **Text**: `text-slate-800` (Legible, official ink color)

## 2. 🔤 Typography
- **Headings (Official Look)**: `font-serif` (Playfair Display or similar) - Used for "REPUBLIC OF CUTENESS".
- **Body / Data Fields**: `font-mono` (Courier Prime or similar) - Used for "Name: Dooboo", "DOB: 2020.05.05".
- **Buttons (Call to Action)**: `font-sans font-bold` (Inter/System UI) - Rounded pills.

## 3. 🧩 UI Components

### A. The "Card" (The Product)
- Determining Aspect Ratio: ID Card standard (85.60 × 53.98 mm).
- **CSS**:
    ```css
    .id-card-container {
      aspect-ratio: 1.586;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
      position: relative;
      overflow: hidden;
    }
    .hologram-overlay {
      background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.4) 50%, rgba(255,255,255,0) 100%);
      mix-blend-mode: overlay;
      pointer-events: none;
    }
    ```

### B. The "Uploader" (Draggable Area)
- Dashed border `border-dashed border-2 border-indigo-300`.
- "Drop your fur baby here" text.
- Preview image must be resizable/moveable within the card frame.

### C. The "Stamps" (Decoration)
- Absolute positioned SVG icons (Paw print, "APPROVED", "GOOD BOY").
- Random slight rotation `rotate-[-6deg]` to feel stamped by hand.

## 4. 📱 Responsive Layout
- **Mobile First**: The ID Card takes up 90% of width.
- **Desktop**: Split screen. Left: Editor Controls. Right: Live Preview.
