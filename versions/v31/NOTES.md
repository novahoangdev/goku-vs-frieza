# v31: polish + more physics (overnight session)

- Goku's feet no longer sink into the ground: while powering up (in a lowered stance) the boot soles sank ~8–11 cm below the grass surface throughout the Super Saiyan transformation (the boots were
  cut off at the laces). `secondary.py: foot_ground_fix` measures the bottom of the boot soles every frame; when Goku is standing on the grass and the soles sink, it
  raises the whole body by exactly the sink depth (delta_location of the GOKU root, without touching existing keys), smoothed when lowering back down.
