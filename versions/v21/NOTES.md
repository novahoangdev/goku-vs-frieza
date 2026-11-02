# v21: SSJ hair no longer bleached white in the app

- In v19–v20 the pale yellow SSJ hair (#FDE47A) + the app shader's bloom/aura → in the chase scene (compare.mp4 at ~16 s)
  the hair turned pale pinkish white and lost its yellow. Slightly deeper yellow (#FFDA4A, shadow #EF9F30, highlight #FFEE9A) and reduced
  the hair's "energy" after the Super Saiyan transformation (0.2 → 0.1) so the bloom doesn't push the hair to white; still paler than v18 (#FFD83E).

A better-looking Frieza (`build_frieza`, `fr_head_surf`, `face_textures.py`)
- The face uses its own material, lit almost across the whole face: before, half the face was covered in a lavender shadow patch that looked dirty.
- Eyes ~18% bigger, closer together, slightly higher → a clear contemptuous look, no more dazed expression.
- The front edge of the purple dome lowered (26.5° → 19.5°): less empty white forehead, the sides still above the ear holes.
- Slightly narrower head + tapered jaw: egg-shaped instead of a round ball.
- Signature dark purple lips (full lower lip, with a gloss) and a bigger mouth.
- V-shaped build: broader chest/shoulders, slimmer waist + hips, neat thighs set close into the hips.

A better-looking black-haired Goku (`goku_blade(tri=True)`)
- Triangular hair spikes (wide at the base, tapering straight to the tip) instead of leaf-shaped locks: before, the leaves stacked into a
  black lump bigger than the head; now the hair bristles with many sharp points, true to Goku's style.
