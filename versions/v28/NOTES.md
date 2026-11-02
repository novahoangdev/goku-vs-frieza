# v28: polish + more physics (overnight session)

- Kamehameha beam with a wider white/ice-blue core (Layer Weight blend 0.42 → 0.3): seen from behind Goku it no longer looks like a blue plastic tube.
- The Kamehameha explosion's shockwave ring no longer looks like a solid blue hula hoop: tube 0.035 → 0.014 (scaled up 4.6× it is no longer 16 cm thick), material breaking up with noise like the v27 foam, dissolving over 32 frames.
- Swaying trees (`secondary.py: tree_wind`, 54 trees including the ones on top of rock pillars): trunk + canopy parented to an empty at the base of the trunk, which then
  rotates. The storm wind has the same direction + same gusts as the grass (gusts travel through the forest at ~9 m/s, so each tree lags a beat), taller trees lean
  less; the Ki wind while powering up pushes trees near Goku outward; the shockwave at the transformation burst whips the trees outward, then they spring back with a decaying
  oscillation, reaching distant trees later according to distance (~340 m/s).
- Shockwave dust ring at the transformation burst: 18 dust puffs spreading outward from Goku's feet, slowing down due to air drag
  (r = r0 + R·(1 − e^(−t/τ))), rising slightly, then breaking up and dissolving (material `burst_dust`, 2 flat tones, no outline, noise threshold
  driven by the object color alpha). Its own RNG (seed 4242) so the shared random sequence isn't shifted.
- The Kamehameha explosion close-up (shot E) no longer blows the whole frame out to white: the water crown has its own material `kame_crown_m` in sea-water tones
  (pale ice blue → turquoise → blue edge) instead of white foam; the app leaves headroom when adding the energy-layer glow
  (`headroom`: areas already near white get 60 % less) → the blue edge of the explosion shows again, and the glow spreading over the dark background is kept.
- Black-haired Goku's hair is a neutral black like the 3D reference image (before, it leaned navy blue): base #1F1F25, shadow #08080B, lit side #3E3F49, gray specular #767986.
