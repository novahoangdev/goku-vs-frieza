# v15: sharper Frieza face, fingered hands, short chibi legs (+ Goku and app effects, 3 parallel workstreams)

Frieza (`build_frieza`, `face_textures.py`, `extras/frieza_details.py`)
- Almond eyes: thick dark upper lids slanting down toward the bridge of the nose, flicking up at the outer corners; red irises half covered by the lids, narrow vertical pupils;
  faint brow ridges (Frieza has no eyebrows). He looks confident and sinister instead of drowsy as in v1–v14.
- Purple marks under the eyes true to the original (a separate decal, unchanged when the expression changes); dark purple lips smirking on one side when
  idle; open mouth / big laugh with thick purple lip outlines. Panicked eyes redrawn wide with small irises, the blink becomes a smug curve.
- Hands with 3 fingers + a thumb (before, a round lump): relaxed / half-curled hands, spread hands when panicking after the Super Saiyan transformation and when he loses
  track of Goku and then gets hit; the index finger curls when the Death Beam finger extends.
- Shorter chibi legs (thigh 0.26 → 0.21); the body, head and anchors stay in place so the app effects don't drift.

Goku (`build_goku`, `choreograph`)
- Fixed a bug present since the early versions: black-haired Goku had no mouth for the whole opening (frames 0–292, including the face close-up while powering up)
  because the mouth's first hide/show key was "hidden" at frame 292. Scanned every other object; nothing else has this problem.
- Hands become real chibi fists (before, round balls): four curled fingers with knuckle ridges on the back, ink lines between the
  fingers on the palm side, a thick thumb wrapped across the index + middle fingers; the punch uses a vertical fist.
- Black hair gets 3 more spikes at the front of the crown so the row of spikes still shows from below (before, it looked like a smooth cap with two spikes);
  vertical ink lines at the hair roots for both forms (most visible on the golden hair).

App (`composite.ts`, `useFxUniforms.ts`)
- Anime-style impact sparks on the 3 landed punches (frames 719, 747, 1030): a sharp 9-point star pops out for 2 frames then shrinks
  back, 4 hard color bands (ink rim → orange → yellow → white core), a thin white ring expanding, white streaks shooting out; it stays fixed at
  the point where the fist lands instead of following the hand. In the black-and-white impact frame it becomes a black star silhouette.
- Aura: flame tongues licking up as separate pointed flames (before, a soft orange rim), thin red-orange outer rim, brighter core.
- Explosion: 3-tone cel smoke with ink outlines and glowing ember lines where it meets the fire, eaten away by holes then dissolving; 16 rock shards spinning outward.
- The demo recording is muted in the simulator.
