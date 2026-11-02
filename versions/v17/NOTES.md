# v17: focus on the two characters (Frieza's build, Goku's head, shading + lineart)

Frieza (`build_frieza`, `fr_head_surf`, `fr_body`, `extras/frieza_*.py`)
- Body rebuilt from smooth lathed shapes (before, assembled from spheres + capsules, giving a pear / bowling-pin shape): broad chest with
  pecs, slim waist, neat hips, slender thighs tapering into purple shin guards with calves, small knees, small two-toed feet.
- Final-form head: round skull under the purple dome, the lower half of the face narrowing to a small soft chin, very subtle cheekbones; the dome, eyes, cheek marks,
  mouth, ears, sweat drop and anger vein all follow the new head surface (no floating, no flickering).
- Neck tapering and flaring at the base, collarbone lines; abs/pecs moved to follow the new chest; smaller chest gem.
- Thick tail base tapering to a point, with an S curve (hanging back, sweeping outward, tip flicking up) added on top of the existing swaying motion.

Goku (`build_goku`, `goku_face_shape`, `extras/goku_outfit.py`, `face_textures.py`)
- Fixed a v16 bug: the blue undershirt collar rose up and covered the chin and mouth like a face mask in close-ups. Sloping shoulders, the blue
  collar lowered to the base of the neck, the point of the undershirt V lowered; there is now a short neck between the chin and the collar, with a cel shadow under the chin.
- The head is no longer a round ball: full cheeks right under the eyes taper to a small, soft, slightly protruding chin, clear in 3/4 view and from below.
  The hair and hairline follow it, and every face decal (eyes, brows, blush, 3 mouth types, nose) is re-projected onto the new head.
- Small anime nose: a slanted shading stroke + soft shadow underneath + a very small skin ridge. Smiling / smirking mouth ~1.2× larger, thicker center line
  with a lower-lip shadow; the screaming open mouth is bigger with a thicker outline.

Shading + lineart for both characters (`char_key_light`, `char_shading`, `CHAR_SHADE`)
- Fixed a bug present since v1: the outline shell (inverted hull) around the characters cast shadows onto the characters themselves, so the key light never
  reached them; Frieza was one flat light purple, Goku was flat in the dark tone. Now there are real light / dark areas: a sharp diagonal
  terminator on Frieza's face and body, the orange gi has a lit side and a shadow side.
- The key light is only blocked by the character itself (trees, clouds and rock pillars no longer darken the characters), shining from the top-left angled toward
  the camera so the face is always lit and the shadow falls on the far side.
- A darker third tone inside the shadow on downward-facing areas and deep creases (under the chin, armpits, under the hair, under the sash), per material
  color (orange-brown on the gi, dark purple on the armor...).
- A thin rim light on the shadow edge of the silhouette: cool rim for black-haired Goku, turning warm yellow in SSJ; light purple rim for Frieza.
- Sharp specular highlights on the golden hair, black hair and boots (the old toon shader had `spec` but with the wrong Z-axis sign, so it never showed).
- The faint light band only shows when the Ki glow is strong, so the golden hair and gi don't get washed out. Black hair adjusted to near black (less
  blue sheen), softer shading on Goku's face so the chin shadow doesn't become a blotch when seen from below.
