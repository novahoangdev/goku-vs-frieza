# v29: polish + more physics (overnight session)

- App: sky lightning casts a rim light on Goku: when lightning flashes, the edge of the body facing the bolt (top + sideways toward the bolt) flashes purple-white for an instant (comparing the matte at the pixel with the matte offset 14 px toward the light source).
- Kamehameha droplets (while charging + water falling back after the explosion) use their own material `kame_drop_m`: bright core, turquoise edge (before, they shared the white foam material).
- Air drag on the hair: when flying fast the whole head of hair is pushed back by the wind against the flight direction (up to 8°, based on velocity in the head's frame, smoothed; added to the v26 inertia spring, clamped to ±14°).
- Leaves flying in the storm wind (`secondary.py: storm_leaves`, 48 leaves): carried along the wind direction + gusts like the grass/trees, drifting while
  swooping and tumbling, falling slowly; once they leave the area they hide and reappear upwind. At the transformation burst, leaves near Goku are blown
  away by the shockwave (impulse decreasing with distance) and then slow down due to drag.
