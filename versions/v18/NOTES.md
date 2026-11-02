# v18: character polish (outlines, SSJ hair from behind, eyes + expressions)

Character outlines (`char_outlines.py`, called after `char_shading`)
- Thickness follows camera distance and focal length: close-ups no longer have thick black bands (obvious in the over-the-shoulder shot showing Frieza's head dome
  at frame 560), wide shots don't lose the lines.
- Large parts (head, hair, body, legs) get thicker lines, small details (trims, buttons, ropes) thin lines; surfaces facing into the body
  (inner thighs, inner arms, sash over the gi) get thinner lines than the outer silhouette.
- Lines taper where things get thin: SSJ lock tips become sharp points instead of blunt blobs of line; fingers, ears and rope ends get thinner.
- Line color: Goku's sleeve / wristband trims use navy lines, Frieza's shoulder trims and chest gem use dark purple lines.

SSJ hair from behind and from the side (`goku_hair_forms`, `goku_blade`, `char_shading`)
- The nape rebuilt as staggered rows of locks (top row swept back, middle row, bottom row hugging the skull then flicking up, 3 nape locks
  pointing down with their tips flicked outward), with slightly varied lengths and angles; in v16–v17 every lock radiated from one point, so from behind it looked like a flat
  pale-yellow lotus (clearly visible in the over-the-shoulder shots at frames 560, 700, 870, 1060).
- Amber-orange shadow tone at the base of each lock and where locks overlap → layered depth like the FighterZ reference; the large white
  highlight in the middle of the nape (the center of the "lotus") reduced.
- From the side: the two top locks twist slightly so their width still shows, and the silhouette stays a flame.

Eyes + expressions (`face_textures.py`, decals + keys in `build_scene.py`)
- Shared anime irises for both: dark at the top fading lighter toward the bottom, radial streaks, a glow ring around the pupil, the lid's shadow
  cast on the iris, one sharp main highlight + a secondary one + a small dot. Goku's upper lid has weight variation (thin at the inner corner, thick at the
  tail, slight flick), thin lid crease and lower lid. SSJ is narrow and fierce, FighterZ style (lid covering the top of the iris, raised lower lid, small pupil).
- Goku: angry brows while powering up (236–300), screaming mouth redrawn with upper teeth + tongue + dark red mouth interior, gritting teeth and
  screaming during the combo (705–780) and the final punch (1012–1048) with narrow, fierce SSJ eyes, confident smirk at the end (1118–end).
  Blush only remains in base form when calm.
- Frieza: smug closed eyes during "ho ho ho" (501–521), startled when Goku transforms (521–532), fierce angry eyes + heavy brow ridge + forehead creases
  + bared teeth snarling (532–700), jaw dropping when he loses track of Goku (1000–1030), eyes squeezed shut with a teardrop
  + mouth twisted in pain when hit (1030–). Fix: at frame 1150 all of Frieza's faces used to show stacked on top of each other.
