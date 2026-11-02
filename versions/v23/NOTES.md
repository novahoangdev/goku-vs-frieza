# v23: Kamehameha + effects on the correct layer + English text

## Kamehameha sequence (5.5 s, inserted before the final shot)
`blender/scripts/kamehameha.py`. `retime.py` opens a 330-frame gap right after the punch from behind (a vertical jump
in the retime map at source frame 1109.8); every channel with keys on both sides keeps its state, and the new file keys over the channels
that need to perform during that gap. Film 28.7 s → 34.2 s.

| shot | length | content |
|---|---|---|
| A | 1.5 s | "Ka…me…": Goku hovers above the sea, pulls both hands back to his right hip, a blue sphere appears between his palms |
| B | 1.2 s | "Ha…me…": close-up of both hands + gritted-teeth face, the sphere grows, crackling sparks, blue light cast on his body |
| C | 0.6 s | Frieza freezes (eyes bulging, mouth open) |
| D | 0.6 s | "HA!": over Goku's shoulder, he thrusts both hands, the blue beam shoots out over the sea (recoil, shockwave, speedlines) |
| E | 0.9 s | the beam slams into Frieza, arms crossed to block → black-and-white impact frame → explosion sphere engulfs Frieza, shock ring |
| F | 0.7 s | wide shot behind Goku: the explosion sphere swells over the sea, the beam fades, white flash into the final shot |

- Open, slightly cupped hands (instead of fists for the whole sequence), 2-joint IK for the shoulder/elbow so both wrists meet in the right place, wrists rotated
  so the palms face the sphere (charging) and then face forward (firing).
- 4-tone cel energy depending on viewing angle (white core → ice blue → blue → azure rim), emissive → the energy layer
  in the app gets a glow. The lumpy explosion sphere churns over time + sparks flicker around it.
- Music: 4 beats "Ka–me–ha–me" (taiko + brass + choir, Dm–Bb–C–A progression) over a rising Ki hum, a held beat, then a full-ensemble D major "HA!";
  the beam roars throughout the firing; a huge explosion; the brass theme resolves exactly on the cut to the final shot.
- Promo: blue background segment + KAMEHAMEHA text, the camera zooms in tight on "HA!", shakes on the explosion.

## App effects on the correct layer (depth pass)
- `render_passes.py` adds a depth pass: depth along the view axis, log-normalized 0.05–400 m, half resolution, no AA,
  no motion blur. The packed video widens from 1728 → 2304 (new column: depth on top, black below).
- `composite.ts` compares each pixel's depth with the effect's depth (anchor z): the aura follows Goku's chest, the Death Beam interpolates
  1/z from Frieza's fingertip to the target, ki blasts follow the projectile head, explosions follow the blast point. Objects closer to the camera occlude the effects:
  the Death Beam goes behind Frieza's head (over-the-shoulder) and behind Goku's hair, and the aura no longer covers Frieza's shoulder pad in the foreground.
- The aura doesn't cover the motion-blurred parts of Goku (partial matte), motion blur shortened (shutter 0.5 → 0.3).
- The aura sprays opposite to the flight direction: new anchor `goku_trail` (where Goku was 0.25 s earlier) → flame direction in the shader.

## English text
App: HOLD TO CHARGE KI / LOADING… / REPLAY, title subtitle "THE LEGENDARY WARRIOR", shot names on the scrub bar (dev).
The promo clip was already in English; added KAMEHAMEHA.
