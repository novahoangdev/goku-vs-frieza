# v25: physics for the effects (water, flying rocks, cooling cracks) + water sounds

## Kamehameha over the sea
- Goku and Frieza descend to skim the sea surface (Goku's feet 1.3 m above the water, before ~6.5 m: every water reaction was
  out of frame). The inserted sequence starts and ends on a cut, so it doesn't mismatch the shots before/after.
- Shot A lowers the camera to look down at an angle so the water under his feet is visible.
- Charging: the Ki pressure pushes the water into ring waves spreading at an increasing pace (the stronger the Ki, the wider the rings); spray
  thrown up falls on real ballistic paths (g = 9.8 m/s² at 60 fps), droplets stretched by velocity.
- Ring waves are rippled and distorted, the foam bands unevenly thick and thin (not perfect compass circles).
- "HA!": the recoil pushes a big ring wave spreading fast under his feet. Goku is pushed back the whole time the beam is firing (0.47 m, before
  0.22 m and then standing still), and the beam's origin follows both hands every frame (before, the origin stayed fixed in midair, drifting away from the hands).
- Beam light reflected on the water: a tapered light streak following the beam head; the explosion casts a round pool of light on the sea
  surface, growing with the blast and then fading.
- The beam running over the water: two jagged foam walls pushed aside under the beam path, following the beam head (3 frames behind), collapsing when the beam ends.
- Hitting Frieza: the shockwave reaches the water after ~3 frames → a water crown (low flared wall + sharp water jets spraying
  outward) shoots up then slowly collapses; a big ring wave spreads out to 15 m.
- Sound: crackling spray + deep lapping waves growing denser while charging, water tearing while firing, crashing water on the explosion, pattering droplets raining down afterwards.

## Super Saiyan transformation
- Rock debris: lifted and floating on the Ki as before, the transformation burst throws it on ballistic paths, it bounces on landing (restitution 0.35, grass friction
  slowing the sliding and spinning) and then settles on the grass; the first impact kicks up a puff of dirt (sized by rock size and fall speed). Before: hand-keyed, rocks stuck into the ground. The number of `random` calls is kept exactly
  the same so other random objects don't change.
- Cracks: blazing yellow while powering up, flashing white at the transformation burst, cooling to orange and then to dark fissures with ember glow
  (before: bright yellow all the way to the end of the film). The energy layer for the glow fades with them.

## Frieza
- Neck slimmer at the top and flatter front-to-back, chin protruding in front of the neck: before, the front of the neck stuck out further than the chin (0.079 vs 0.048), so
  the head merged into the neck like a bowling pin with no visible jawline; now there is a clear, rounded chin line.

The whole film was re-rendered (Frieza appears in most shots).

## Other details
- SSJ Goku's face is no longer covered by a white haze: an old bug in `tex_mat` (comparing nodes with `is not`, but the Python wrappers of
  bpy nodes are recreated on every access → always true) made the eye decal's energy layer ignore alpha, so the whole rectangle
  lit up and the app bloomed it into a white patch over half the face, washing out the eyes. Now compared by name; also only the iris (the
  blue part) is emissive, the eye white + black lashes are not on the energy layer.
- Aura Ki particles (app) spread around the body, no longer speckled like snow on Goku's face/body.
- Chase flight trails: thinner cone core + 7 energy streaks of varying length around it (before, a smooth cone like a purple/yellow funnel).
- Cracks cool to a dark brown near the edges → a thin dark fissure, not a heavy brown stroke.
