# v11: detail polish (4 workstreams in parallel)

Each workstream had its own file in `blender/scripts/extras/` (build_scene runs them last), built a test into a temporary
file, compared before/after images and only then copied it in, so they did not collide or break the version being rendered.

Goku (`extras/goku_details.py`)
- Large 悟 kanji circle on the back of the gi (most visible in the over-the-shoulder shots on Goku), sash knot at the front.
- Top and bottom ridges on the wristbands, sleeve hems, a seam along the boot toes.
- Cloth folds as ink strokes tapered at both ends on the back, chest and thighs.
- Light / dark hair strands on the SSJ and black hair (shown/hidden per form, hidden during teleports).

Frieza (`extras/frieza_details.py`)
- Crescent sheen streaks + dots on the head dome, shoulder pads, arm guards and shin guards; light purple rim at the base of the shoulder pads.
- Glossier purple-pink chest gem with a highlight; faint pec lines + abs; two round toes on each foot.

Namek scene (`extras/env_details.py`)
- Dome houses: round window frames, U-shaped door frames, bases, spires with a neck + round bulb + antenna; added a secondary dome house and 4 distant houses.
- Ajisa trees with fuller multi-tier canopies; rock clusters + grass tufts around where the characters stand (4–16 m), mesas and thin rock pillars in the distance.
- Checked that the camera passes through none of the new objects across all 1200 frames.

Screen effects (`app/src/cinematic/shaders/overlay.ts`)
- Manga-style speed lines: wedge-shaped strokes, sharp on the inside and swelling toward the edge, random thickness, slight color-split edges; ink
  halftone dots at the screen edges while accelerating.
- "Focus burst" frame on strong flashes (Super Saiyan transformation, finishing blow): ink rays radiating on a white background + a brush-stroke ring that expands.
