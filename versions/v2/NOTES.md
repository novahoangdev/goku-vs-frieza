# v2: anime faces + body shapes + full Namek scene

Model
- Faces drawn as textures (blender/scripts/face_textures.py, SDF + numpy): big eyes with thick lashes, lash tails, 3-tone gradient irises, iris rims, 3 highlights; hatched blush on the cheeks; smiling / screaming mouths with tongue and teeth.
- Face decal hugs the elliptical shape of the head (face_decal); chibi head with chubby cheeks, eyes lower and bigger.
- SSJ: teal eyes, upper lids lowered for a determined look; hair a deeper yellow, no longer washed-out white.
- Toon shader adds a rim light and specular highlights computed from the camera direction, so the anime look always shows.
- Frieza: glossy purple head dome, its edge curving high at the forehead and low toward the nape; red eyes with drooping lids for a contemptuous look, purple marks under the eyes; smirking purple lips.
- Body shapes: tapered arms and legs, wide-legged gi pants, blue boot cuffs; Frieza with a small waist and flat shoulder pads.

Scene
- Namek: dome-roofed houses, grass bushes, patchy grass, pebbles, rock pillars with horizontal strata, cloud clusters, thinner cracks.

Camera angles
- Shot 7b: Frieza charges in, camera placed over Goku's shoulder (in v1 nobody was visible).
- Shot 8 chase: camera flies in front of Goku looking back, showing Goku dodging and Frieza chasing behind.
- Shot 9c: camera over Goku's shoulder watching Frieza get knocked far away (in v1 he was cut off at the frame edge).

In-app effects (Skia)
- Aura with curling flame tongues; the "egg" is turned off when Goku is hidden behind a rock pillar (v1 had a floating flame blob).
- Anime-style Death Beam: purple → pink rim → white core, rippling, with a flash at the fingertip.
