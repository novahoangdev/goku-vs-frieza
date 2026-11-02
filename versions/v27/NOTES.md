# v27: more details (overnight session)

- Storm wind: the whole grass field leans one way and sways with each gust (shape key `storm`, added to the Ki wind
  `ki_wind`), strong during the storm at the start of the film, calmer after the transformation, nearly still during the aerial fight.
- The opening wind sound rises and falls with the exact gusts that make the grass sway (same formula as the `storm` shape key).
- Thunder matched to every lightning bolt the app draws: `synth_audio.py` rebuilds the lightning schedule exactly like the app (every 0.32 s, seeded per cut, same
  hash function) → ~1/3 of the bolts get a distant rumble echoing back after 0.4–1.1 s (far-off lightning), quieter than the main thunder claps (10 of them).
- Goku's sash tails become soft pendulums (`secondary.py: belt_tails`): they hang with real gravity (when Goku flies horizontally the
  sash tails hang toward the ground instead of sticking out sideways like sticks), get pulled back against the flight direction by the wind, swing forward on sudden stops; the 2 tails are offset
  by 1 frame. The pivot moved to the tie point at the knot.
- The foam ring under his feet while charging the Kamehameha no longer looks like a white tube drawn with a marker: thinner (0.06 → 0.035), new material
  `kame_ripple` breaks up the foam with noise, and as the ring spreads the noise threshold rises with the object color alpha (key 1 → 0), so
  the foam gradually dissolves into fragments and disappears. The recoil wave when firing and the big wave under the explosion use the same dissolve.
- Thrown-up water droplets are smaller (0.024–0.05 → 0.016–0.034) and stretch less with velocity (×34 → ×26): no longer egg-shaped.
- App: hot air shimmers around every glowing object built in Blender (energy ball, Kamehameha beam, explosions); composite shader
  section 2c takes 4 offset energy-layer samples around the pixel, and near a light source it jitters the sample point with upward-drifting noise
  (rising hot air), without shaking Goku. Before, the haze was only around Goku's aura.
- Black-haired Goku's face no longer has a blotch across the cheeks: the high key light put the lower half of the chibi face below the eyes into the shadow zone (threshold 0.1) + the third
  tone (downward-facing surfaces) → the whole lower half of the face became a darker patch. `goku_skin_face`: removed the third tone, shadow threshold 0.1 → 0.025,
  rim light 0.4 → 0.12 (shot from below, the rim light covered the whole jaw + neck as a pale patch).
- Water thrown up by the Kamehameha explosion falls back down: 36 large droplets fly out from the wall of the water crown (1.2–3.6 m high) on ballistic paths
  with real g, stretched by velocity, falling into the sea (before, the crown just shrank and the water "vanished" in midair).
- App: the Death Beam grazing past casts a pink glow on Goku (cheeks, hair near the beam), strong right next to the beam, fading out over ~120 px.
- Frieza no longer has a dotted white line along the edge of his head dome: the inside of the dome (1.035 r) nearly coincided with the head's outline shell (r + 0.007) → from
  a distance it z-fought into a dotted line. The dome expanded to `FR_DOME_RD = 1.048` (the anger vein on the dome uses the same constant).
- A plop sound for every droplet falling back into the sea: `kamehameha.py` places a `sfx:plop` marker on the exact frame a droplet hits the sea surface
  (34 droplets before the cut), `synth_audio.py` plays a short "bloop" + a small fizz, each droplet at its own pitch, with random panning.
