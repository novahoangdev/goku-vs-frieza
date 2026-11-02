# v13: heat shimmer around the aura + bloom (app only, render unchanged from v11)

App (`app/src/cinematic/shaders/composite.ts`)
- Heat haze: while the aura burns, the background around Goku (grass, horizon, sky) shimmers slightly like hot air, with noise drifting upward
  in rhythm with the flames; it fades out with distance scaled to the character's on-screen size and does not distort Goku himself (blocked by the
  matte), so his face stays sharp. In wide shots where the character is small, the shimmer area shrinks too and does not warp the whole frame.
- Soft bloom on the energy layer (golden hair, eye flashes): 4 extra offset samples around each pixel, so the glow spreads wider and warmer
  instead of only lighting the hair edge.
