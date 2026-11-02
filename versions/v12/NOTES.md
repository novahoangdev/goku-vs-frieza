# v12: film color grade + film grain (app only, no Blender re-render)

App (`app/src/cinematic/shaders/overlay.ts`)
- Vignette changed from pure black to deep navy: the screen corners cool down while the aura, beams and flashes stay warm; it looks
  like an anime color grade instead of a dark layer over the picture.
- Fine film grain (2 px, changing 24 times per second) over the whole frame, stronger in the dark areas at the screen edges; the hash uses modded coordinates
  so no banding/moire shows at large coordinates.
- The recording keeps v11's Blender render, so comparing v11 ↔ v12 only shows differences in the screen overlay.
