# v22: seamless arms and legs (no more mannequin joints)

`skin_limb` (build_scene.py): each arm/leg is ONE continuous mesh from shoulder/hip through elbow/knee to wrist/ankle, replacing
2 rigid segments attached to 2 joints. The upper part follows the upper joint (the object is a child of the shoulder/hip joint), the lower part bends with the
elbow/knee joint via a Hook modifier with weights blending smoothly over ±4–4.5 cm around the joint (linear blend skinning; the choreography is unchanged
because the Hook follows the existing joint Empties that carry the rotation keys).

- Goku: the whole arm is continuous skin (biceps + triceps + forearm muscles kept as in v19). Before, when bending the elbow (guard, punch)
  the 2 segments stuck into each other, leaving a hard crease + a gap at the elbow; now the elbow bends in a smooth, continuous curve like a real arm.
- Frieza: continuous white arm from under the shoulder pad to the wrist, running under the purple forearm guard (before, a thin upper arm stuck straight into
  the armor tube like 2 joined pipes). Continuous white leg from the hip through the knee to the ankle, removed the separate knee sphere; the purple shin guard stays
  as an outer shell → the thigh flows smoothly into the shin when the knee bends (flying, dodging, getting hit).
- Checks: test bends of 110° at the elbow / 75° at the knee compared with the old version from the same camera angle; scanned the action shots 250–1150 with no errors,
  no objects wrongly hidden (vischeck).

Slower pacing: 20 s → 28.7 s (`retime.py`, runs at the end of build_scene)
- The old film had 14 shots in 20 s (~1.4 s/shot), so it felt abrupt. Old → new frames are mapped piecewise-linearly per
  shot, applied to every keyframe (objects, materials, nodes, camera, FX) and marker: opening ×1.6, powering up ×1.4, the eyes ×1.3,
  burst ×1.6, Super Saiyan ×1.5, Frieza ×1.4, dodge ×1.25, combo ×1.2 (kept frantic), chase ×1.25,
  counterattack ×1.3, the punch ×1.5 (slow-mo), ending ×2.0 (lingering on the title).
- The map is written to timeline.json ("retime"); the app (impact spark timings, speedline center, tint, dust), the promo clip
  (device camera, big text, background, "29s" end card), capture (still frames, poster), compare, fx-preview and audio all convert
  through it (`tools/rt.py`). The app's FX clock still runs in real time, so fire/smoke isn't slowed down with it.

New audio (`synth_audio.py` rewritten): an anime-style score, synced to every visual beat
- Synthesized instruments: brass (resonant, brightening on the attack), strings (supersaw, tremolo), formant choir
  "aah/ooh", timpani + rolls, taiko, drum kit (kick/snare/hi-hat/crash), bass, power chords; concert hall reverb.
- Structure: opening storm in D minor (low strings + choir) → powering up (tremolo strings rising Dm–Bb–C–A, timpani roll, riser) →
  3 SSJ flash beats (full-ensemble hits + reverse cymbal) → 0.12 s of silence → BURST (D major brass chord + choir + crash) →
  heroic theme (brass) → Frieza (low strings in B-flat minor, tritone brass, pizzicato) → battle at 150 BPM →
  counterattack (drums drop out, high tremolo strings + riser, 0.3 s held breath) → THE PUNCH (full-ensemble stinger, long reverb) → brass theme reprise
  + final D major chord + title chime.
- Sound effects: thunder for every lightning flash, ground rumble while powering up, electric crackle on the SSJ flashes, aura Ki fire following its track, Death Beam
  (charge + piercing screech, panned left/right), teleport "shun" on dodges, layered punches (whoosh + thud + crack), wind rushing while flying
  with the speedlines, ki blasts + explosions with debris, the 3 final punches, water column, title chime.
- Mix: music normalized by RMS + ducked under loud sound effects; sound effects softly compressed so the punches / beams / teleports
  aren't drowned out by the transformation burst. Opening ~-30 dB → transformation burst ~-12 dB → battle ~-16..-19 dB.
- Custom music (optional): put `render/audio/bgm.mp3|m4a|wav|…` → the build converts it to bgm.wav and uses it instead of the synthesized
  music (sound effects are kept, the music ducks under them automatically).

## Fixed a crash with the longer film
- The first v22 recording crashed the app at ~20 s into the film: Hermes on the UI thread ran out of memory (`HadesGC::oom`).
  Cause: `useCinematicVideo` created a new `SkImage` for every video frame and assigned it through a shared value from JS;
  the UI runtime held on to the old images waiting for GC on the JS side. A 20 s film just barely held up, a 29 s film overflowed.
- Fix: the `SkImage` wraps the GPU texture directly (reading its content at draw time), so it is created only once per texture; each frame
  only updates `videoTime` to make the Canvas redraw.
