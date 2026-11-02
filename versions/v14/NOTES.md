# v14: broken shots fixed + 3D rocks + reworked Goku and Frieza heads (3 parallel workstreams)

Scene + camera (`build_scene.py`: `cam_for`, `build_env`; `extras/env_details.py`)
- Zoom-out shot right after the Super Saiyan transformation (frames 300–390): in v1–v13 the camera dipped below the ground, so half the frame was the
  murky green underside of the ground slab, only Goku's boot soles showed, and the golden ki particles floated in midair. Now the camera sits low
  at knee height (a heroic angle), clearly showing the horizon, rock pillars, and SSJ Goku's full body standing over the cracks.
- Close-up of Goku screaming while powering up (frames 240–300): before, it pushed in so close that the whole screen was a flat patch of skin with the mouth at
  the bottom; now it stops where the squeezed-shut eyes + screaming mouth are clearly visible, with the zoom jolt only in the last 4 frames.
- Rock debris on the grass: before, flat brown patches like dirt stains; now naturally lumpy 3D rocks, 3 gray-green tones with outlines,
  lit on top and darker on the slopes, fading with distance like the ground; cut down to ~40% of the scattered rocks and grouped into small clusters.
- Low orbiting shot around Goku while powering up (frames 120–240): flying rock debris rose right in front of the lens, hiding half of Goku;
  now any rock that ever gets closer than 2.4 m to the camera is moved further away (`extras/debris_clear.py`), and rocks still rise around Goku in the background.

Goku (`build_goku`, `face_textures.py`)
- Hair rebuilt for both forms: the hair layer hugging the head has a real hairline (before it was a sphere capped over the head, with a hole in 3/4 view).
- Black-haired Goku: the bangs are pointed locks lying on the forehead (long middle lock, two short ones stopping above the eyebrows, temple locks,
  sideburns) leaving gaps to show the forehead and eyebrows; in v13 the hair covered the whole forehead like a helmet. The front side spikes that covered the ears now
  point outward above the ears.
- SSJ: one signature bang lock in the middle of the forehead + one short lock, showing more forehead.
- Removed the oval light patch around the SSJ mouth (it looked like a dog's snout): it was the skin material's highlight band; the head now uses
  its own skin material without that band.
- Small round ears on both sides (dark inner ear), bolder eyebrows (thick inner end, pointed tail), smiling/smirking mouth ~35% larger.

Frieza (`build_frieza`, `extras/frieza_form.py`, `extras/frieza_details.py`)
- The purple dome on the head rebuilt as a large cap in the true final-form shape: front edge right above the brows, sides coming down to the ear holes,
  low at the back of the head; the edge is one clean continuous line (in v1–v13 it was just a thin purple band at the hairline).
- Sturdier chibi body: defined hips, broad chest tapering to the waist, thicker neck and thighs tapering to the knees, bigger knees/shin guards/feet,
  bigger biceps + arm guards + hands + shoulder domes; thick tail base tapering to a point. Chest gem moved forward to match the new chest.
- Ear holes with volume (raised rim + dark inside). The anger vein sits on the dome, the sweat drop moved down to the temple.
- Fix: the added details (sheen streaks, abs, toes, shoulder rims) did not turn off with Frieza at frame 1151.

App
- The demo recording is muted in the simulator (the promo clip still takes its audio from mix.wav).
