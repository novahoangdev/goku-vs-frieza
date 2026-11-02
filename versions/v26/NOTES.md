# v26: small details (overnight session)

- Frieza has a nose: two small slanted dark purple nostrils + a soft shadow under the bridge (decal `frieza_nose`); before, the face was smooth like a mask.
- Secondary motion with inertia (`secondary.py`, runs at the end of the build after retime + Kamehameha): spring–damper
  (natural period ~0.5 s, settles after ~2 oscillations) driven by the acceleration of the head/hips in their own local frame.
  - Frieza's tail: speeding up → the tail lags down, turning → the tail swings to the opposite side; the tip whips harder than the base, the wave travels
    along the tail (1.5 frame delay per segment). Max ±22°.
  - Drag: the faster he flies, the straighter the tail is pulled back (removing up to 80% of the built-in S curve at ~18 m/s, smoothed),
    and it curls back as before when he is still.
  - Goku's hair (black + SSJ): lunging forward → the hair leans back, turning → it shifts to the opposite side, then sways back. Max ±11°.
  - Added on top of the existing keys (shaking in the Ki flow, tail sway); reset at every cut and when a character teleports between
    two shots (> 0.9 m/frame) to avoid fake whips.
- Grass bends with the Ki wind: shape key `ki_wind` on `grass_tufts` + `env_grass_clumps` bends each blade radially outward from
  where Goku powers up (curving with blade height, weakening with distance, up to ~66° right next to Goku); pulsing while charging, fully
  flattened at the transformation burst, easing off until he flies away.
- Black hair: added a third, blue-gray light tone on the side facing the light (`hi` 1.35 → 0.82, before it was never reached) + stronger specular highlights
  → the black locks separate into distinct shapes like anime black hair, instead of one black mass.
- Kamehameha beam: the beam body has billowing energy streaks flowing from the hands forward (noise stretched along the beam added to the
  Facing factor of the cel ramp, flowing at ~70 m/s), no longer a smooth plastic tube.
- Falling rock sounds: every piece of rock debris hitting the ground (frames taken from the ballistic simulation, marker `sfx:thud`) gets a deep thud
  + a small crunch, with varied timbre/volume/pan (~-33 dB under the music, 46 sounds in the ~1.5 s after the transformation).
- Kamehameha shot F (wide shot from behind): camera pulled back to the rear-right → Goku's full back in the lower-left third, the beam leads the eye to
  the explosion + water crown (before, Goku was cut off at the left edge, only a patch of hair visible).
- Steam: the explosion energy right at the sea surface evaporates water → 9 gray-white cel cloud puffs (lumpy via noise) swell
  around the base of the explosion, spreading out and rising more and more slowly until the end of the sequence.
- Kamehameha sphere: its own material, a small white core with turquoise → blue → deep blue layers toward the edge (before, almost white
  throughout, looking like a rice ball in Goku's hands).
- Kamehameha shot E (beam hits Frieza): camera pulled back to ~5 m from the explosion instead of 2.6 m; before, the explosion sphere + glow blew the whole
  frame out to white for ~0.5 s, now the whole explosion, the shock ring and the water crown are visible.

## App (shader)
- Sky lightning drawn in the composite instead of the `Lightning` layer on top: it only shows where the depth is sky (> ~120 m), so it
  sits behind rock pillars, hair, characters and the ground (before, lightning was drawn over Goku's head). On each flash the whole scene briefly brightens as if lit by the lightning.
- Ki blast explosions: hot gas rises (fireball → smoke drifting upward as it cools), the still-hot fire lights up Goku
  (warm orange, weakening with distance and as the fire dies out).
- Light spill: glowing objects that aren't part of Goku (energy ball, Kamehameha / Death Beam, explosions built in Blender) cast
  their color onto Goku (16 samples around the pixel, closer is brighter); the SSJ hair is in the matte, so it doesn't light itself.
- Ki particles (Sparks): golden sparks rising along both edges of the body like aura flames, no longer scattered evenly over the face/body (before, close-ups
  looked like snow speckled on Goku's face).
- The energy layer glow follows the glowing object's own color (70%) instead of adding a fixed warm yellow → SSJ irises stay turquoise
  when they flash, instead of turning pale green.
