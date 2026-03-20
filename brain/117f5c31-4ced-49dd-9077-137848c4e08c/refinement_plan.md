# 🛠️ Implementation Plan: Pet Passport Refinement

**Goal:** Fix critical issues identified in Code Review and enhance the visual appeal (Vibe Upgrade).

## 1. 🐛 Bug Fixes & Stability
- [ ] **Image Optimization**: Implement client-side image resizing (max width 800px) before setting state to prevent crashes with large photos.
- [ ] **Text Overflow**: Add `maxLength` attributes to inputs and CSS truncation (`truncate`) to the card display.
    - Name: Max 12 chars
    - Breed: Max 15 chars

## 2. 🎨 Design Enhancements (Vibe Polish)
- [ ] **Background Upgrade**: Replace plain white background with a **"Mesh Gradient"** or **"Abstract Shapes"** to make the app look fuller and more modern.
- [ ] **Card Detail Upgrade (The "Official" Look)**:
    - Add a "stamped" texture overlay.
    - Add a dynamic "Date of Issue" field (today's date).
    - Add a "Signature" area (using a script font).
    - Add a "Holographic" strip effect using CSS gradients.

## 3. 📱 UX Improvements
- [ ] **Keyboard Accessibility**: Add `onKeyDown` handler to the upload area.
