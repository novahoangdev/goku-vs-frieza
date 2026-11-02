# v30: polish + more physics (overnight session)

- The Death Beam that misses Goku now hits the ground behind him (`secondary.py: beam_impacts`): the beam is cast from Frieza's fingertip through the target, then
  ray-cast to find the ground hit point (~5 m behind Goku) → pink-white flash (energy layer for the app glow), 7 clods of dirt flying on ballistic
  paths with real g, a dust puff rising, breaking up and dissolving, a scorch mark left on the ground; marker `sfx:pop` → a small ground explosion sound
  (deep thump + pattering dirt) on the exact hit frame.
- Goku's neck in anime shadow tone (the chin casts a shadow onto the neck, its own material `goku_neck_skin` darker than the face): before, it was the same color as the face, so the neck was bright like a block of wood under the chin.
- Rocks lifted by the Ki before the Super Saiyan transformation no longer float smoothly: they shake + bob in the Ki field, more violently closer to the burst (own RNG, the ballistic paths after the burst are unchanged).
- App: black-haired Goku no longer has a gray-white mask: the "cold stormy Namek" grade (28 % desaturation + blue tint) now applies only lightly to Goku (matte: keeps 93 % saturation, very slight blue tint); the scene stays as cold and gloomy as before, the face skin + orange gi keep their warm colors.
- Grass + leaves rustle with the gusts (same gust as the grass/trees/flying leaves in the picture): a high-frequency rustle only clear on strong gusts, fading after the transformation burst as the storm calms.
- Storm clouds in the sky drift fast during the storm at the start of the film (strong wind, ~0.65°/s, 3× faster than before), and much slower after the transformation burst (before, a steady ~0.2°/s for the whole film).
- Frieza's neck in a light shadow tone (`fr_neck_skin`, a more purplish white than the head) to separate the chin from the neck in angles where the neck is visible.
