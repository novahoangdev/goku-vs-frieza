# v19: Goku's hair looks like the character (compared with the FighterZ reference)

SSJ hair (`goku_hair_forms`)
- Re-laid out after the FighterZ reference: two wide top locks standing nearly upright, the base leaning forward then the tip curving back
  like a flame; upper-side locks fanned ~30°, temple locks pointing sideways then flicking up at the tips, locks above the ears pointing sideways with a slight upturn. Wider
  locks (~25%), fewer thin locks → the silhouette is a flame mass of a few big points instead of an even ring of spikes like a daisy.
- From behind: two rows of long locks pointing back then flicking up + short nape locks, no longer hugging the skull like an "artichoke".
- Bangs: two big S-curved locks standing out on the crown, falling down both sides of the forehead (the main lock down to the character's right eyebrow,
  the secondary lock down to the left temple) as in the reference; the front hairline slightly jagged.
- Removed the orange base band on the front top locks (it read as a horizontal line cutting through the hair mass when seen head-on).
- Paler, FighterZ-style colors: base #FDE47A, amber-orange shadow #EFA93F, highlight #FFF2A8; base shadow #E9A53E.
- Less swept back (sweep 0.35 → 0.22) so it stands upright like real SSJ hair.

Black hair (base form)
- The front hairline cut into 6 jagged, uneven pointed bangs in Goku's style (the deepest point offset to the character's right) instead of a smooth
  arc like a headband; 3 big bang locks standing out on the crown, falling diagonally over the forehead. Reduced the bulging ridge at the front of the forehead (the light arc).
- Removed the upright top lock right above the forehead (which created a lotus shape when seen head-on), replaced with a lock leaning forward then tilting
  to the side.

Both forms
- Lock cross-section: 2 convex arcs meeting at the spine ridge and the edges (instead of an 8-sided diamond) → each half of a lock has one clean light-dark
  boundary, only the ridge + edges are sharp; no more diamond-facet speckling when locks twist.

Goku's face (`face_textures.py`, expression keys in `build_scene.py`)
- Base-form eyes: black irises (before, a doll-like gray-purple), flatter and slightly upturned upper lashes, short lash tails (removed the curly flick
  of girlish eyes), darker glow at the bottom of the iris → big, friendly eyes, but a boy's eyes like Goku's.
- Base-form eyebrows: thick, nearly straight, slightly upturned, squared inner ends (before, a thin arc mostly hidden by the bangs).
- Charging Ki (236–292): gritted teeth together with the angry brows; before, the face was still smiling while the brows frowned.

Frieza (`build_frieza`, `fr_head_surf`)
- Less scrawny (before, he looked like a light bulb stuck on a stick): neck ~40% thicker with sternocleidomastoid muscles flaring to the shoulders, chest
  ~10% broader, fuller waist + hips, upper arms and thighs ~20% sturdier.
- Moderately tapered jaw: the chin is no longer pointed like a light bulb, the face is round and full like a chibi Frieza.

Goku's arms
- Upper arms + forearms rebuilt as seamless lathed shapes (before, 2 straight capsules with gaps at the joints like a wooden mannequin):
  biceps bulging right below the sleeve, triceps at the back, the forearm swelling near the elbow then tapering into the wristband.

Goku's outfit details
- The rim light on blue cloth (sash, wristbands, undershirt) and boots uses its own vivid blue: before, it mixed with the SSJ yellow rim
  into a gray-beige band around the edges of the sash and wristbands.
- A real tied sash knot + 2 sash tails as flat cloth strips widening gradually, hanging diagonally (before, a round capsule like a spoon).
- Frieza: shoulder pads become domes (flattened base hugging the shoulder) + a thin dark purple bottom edge, replacing the bright lilac ring around a sphere
  (which looked like Saturn).
- Goku: removed the 2 separate orange shoulder pieces (sticking up like 2 knobs at the ends of the lapels); the gi body already covers the shoulders, so the V lapels run cleanly
  over the shoulders like the FighterZ gi. Slightly thicker neck, the chin shadow on the neck has a clear U curve (before, a straight edge like a strip of tape).
- SSJ eyebrows in saffron yellow (#E6AE24, orange-brown outline) to match the new pale golden hair (before, yellow-brown).
