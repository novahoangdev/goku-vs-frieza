# Versions

Each `vN/` folder is one version, kept so the changes can be compared over time:

- `saiyan-awakening-demo.mp4`: 4:3 demo clip posted on X (iPhone mockup, 27 s, with sound)
- `screen.mp4`: the original simulator screen recording (Release build of the app)
- `cinematic-packed.mp4`: the packed video bundled in the app (beauty + matte + energy)
- `stills/`: a few beauty frames rendered from Blender (no Skia effects yet)
- `NOTES.md`: what changed in that version

| Version | Highlights |
|-----|------------|
| v1 | First chibi characters: eyes/mouth built from flat shapes, curved spiky hair, basic Namek scene |
| v2 | Anime faces drawn as textures, chibi heads, rim light + specular highlights, glossy Frieza head dome, slimmer bodies, full Namek scene, camera angle fixes; new flame aura + Death Beam |
| v3 | Hand-painted sky / ground / sea (Codex), blinking, "> <" eyes while screaming, panicked Frieza, hair shaking, heroic final shot |
| v4 | Camera-relative key light on the characters (light linking), V-neck collar + sleeves + red shoelaces, hand-painted rock pillars / tree canopies, Frieza gets an index finger + ear holes, hair fully covers the nape, SSJ eyebrows |
| v5 | Finishing blow lands on Frieza's face, seamless Frieza tail, fist with knuckles, chibi expressions (anger vein, sweat drop, smirk), app icon + launch poster, anime-style explosions |
| v6 | Impact stars on every hit, energy trails while flying, slowly drifting hand-painted sky, per-part colored lineart, golden Ki particles around the aura |
| v7 | Round contact shadows under the characters, front bangs for black-haired Goku |
| v8 | Glowing zigzag ground cracks, rocky shore + sea foam around the island, tidier sideburns for black-haired Goku, no more streaks on Frieza's chest gem, comet-style ki blasts |
| v9 | Goku gets short, chubby chibi legs, Frieza gets thumbs, index finger extends only when firing |
| v10 | Aerial perspective (distant scenery fades), fixed the chase passing through the core of a rock pillar, anime-style Death Beam |
| v11 | 4 parallel detail passes: 悟 kanji on the back + cloth folds + hair strands (Goku), armor sheen + abs + toes (Frieza), detailed Namekian dome houses + puffball trees + rock-and-grass clusters (scene) |
| v12 | Color grade: navy vignette + fine film grain (app overlay only, render unchanged from v11) |
| v13 | Heat haze (air shimmering around Goku while the aura burns) + soft bloom on the energy layer (app only) |
| v14 | 3 parallel workstreams: fixed the camera dipping below ground + close-up of the scream + 3D rock debris; Goku's hair gets a hairline, shows the forehead, adds ears, drops the SSJ "snout"; Frieza gets a large purple dome, sturdy chibi body |
| v15 | Frieza gets sharp eyes + purple marks + purple lips + fingered hands + short legs; Goku gets a real fist + spikier hair + fixed missing mouth in frames 0–292; app: impact sparks, flame-tongue aura, cel-shaded explosion smoke |
| v16 | Goku based on the FighterZ reference: SSJ hair as wide flame-shaped locks + signature bangs, black hair in the same style, no more bald nape; deep V-neck + blue undershirt, wide sash, baggy tapered pants, navy boots with red stripes and yellow laces |
| v17 | Slim Frieza body (chest, waist, slender thighs) + head with a chin; Goku gets a neck, chin, nose, collar no longer covers the mouth; fixed outline self-shadowing that kept the characters always dark → real light and shadow, a third tone, rim light, specular highlights |
| v18 | Outline thickness varies with the camera + tapered hair tips; SSJ hair from behind becomes rows of flame locks with orange shading; new anime irises + many expressions (Goku angry / gritting teeth / smirking, Frieza smug / snarling / in pain) |
| v19 | Goku's hair based on the FighterZ reference: SSJ as a flame mass of a few large upright locks, 2 S-shaped bang locks, rows of swept-up locks at the nape, pale yellow; black hair with Goku's jagged bangs; clean two-tone light/dark locks; black eyes + thick brows for base Goku, gritted teeth while charging Ki; sturdier Frieza (neck, chest, arms and legs) + domed shoulder pads; muscular Goku arms, removed the sleeve shoulder knobs, real sash knot |
| v20 | SSJ hair at the nape becomes a few large flame locks (no more pinecone look from behind), hair no longer washed-out white during the transformation, clear sideburns; black hair asymmetric like the real Goku, removed the gray arc on the bangs, shorter nape; Goku's eyes fully black + fierce angry eyes while charging Ki; Death Beam energy ball with a white core and pink rim |
| v21 | SSJ hair no longer bleached white by bloom; Frieza: clean bright face, large sharp eyes, purple lips, tapered head, neater forehead, V-shaped build; black-haired Goku with bristling triangular spikes |
| v22 | Seamless arms and legs; film slowed from 20 s → 29 s (stretched shot by shot); anime-style score + sound effects fully rewritten, synced to every visual beat |
| v23 | 5.5 s Kamehameha sequence before the ending (charging at the hip → "HA!" → blue beam engulfs Frieza), with its own music + sound effects; app effects sit on the correct layer thanks to a depth pass (Death Beam goes behind Frieza's head, aura no longer covers the shoulder pads); aura sprays along the flight direction; in-app text switched to English |
| v24 | Black-haired Goku rebuilt in the DBZ silhouette: long top cluster swept to one side, long layered side locks pointing outward, thick bangs falling over the forehead (replacing the hedgehog spike bundle + cupped bang rim) |
| v25 | Physics: Kamehameha skims the sea surface (ring waves + gravity-driven falling spray while charging, foam wake under the beam, water crown + big wave on impact, water sounds); Super Saiyan transformation debris flies on ballistic paths, kicks up dust on landing, bounces then settles; beam sticks to the hands + recoil pushes Goku back; beam glow reflected on the water; cracks cool down into dark fissures; Frieza with a slim neck and defined chin (no more bowling-pin shape) |
| v26 | Inertia: hair + Frieza's tail lag then sway with acceleration, tail pulled straight by the wind during fast flight; grass flattened by the Ki wind while powering up; Frieza gets a nose; Kamehameha beam with flowing energy streaks, deeper blue energy ball, steam rising on impact; shader-drawn lightning only shows in the sky (behind rock pillars and characters); explosion rises + casts warm light on Goku; glowing objects cast colored light on the characters; falling rock sounds |
| v27 | Goku's sash hangs with gravity + wind while flying; grass sways with storm gusts, wind sound rising and falling in sync; distant thunder rumbles matched to the lightning in the sky; Kamehameha foam breaks apart and dissolves, water droplets shrink; hot air shimmers around the energy ball / beam / explosion |
| v28 | Trees sway in the storm wind + get whipped outward by the transformation shockwave then spring back; dust ring spreads from Goku's feet at the transformation burst; neutral black hair matching the reference image; Kamehameha explosion close-up no longer blown out (sea-colored water crown, glow leaves headroom); shockwave ring thins out gradually; Kamehameha beam with a wider white core |
| v29 | Leaves fly in the storm wind, blown away by the transformation shockwave; Goku's hair pushed back by the wind against the flight direction; sky lightning casts a rim light on Goku; sea-colored Kamehameha droplets |
| v30 | Death Beam misses Goku and hits the ground behind (flash, ballistic dirt debris, dust, scorch mark, explosion sound); black-haired Goku's skin no longer looks like a gray-white mask (slight cool color correction on the characters); neck in anime shadow tone; rocks shake as the Ki lifts them; grass and leaves rustle with each gust |
| v31 | Goku's feet no longer sink into the ground while powering up (boot soles sank 8–11 cm below the grass for the whole transformation → body raised by exactly the sink depth) |
