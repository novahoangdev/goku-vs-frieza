# Saiyan Awakening: Goku vs Frieza

> Original plan written on October 29, 2026, before the first version. Some numbers here (20 s, 3 render passes, the
> 1728×2496 pack) describe that first version; see [README.md](README.md) and [versions/](versions/README.md) for how it evolved.

A 20-second cinematic for iPhone: Goku transforms into a Super Saiyan on Namek, then fights Frieza.

Concept and technical plan, written on October 29, 2026. Implementation follows the default choices in section 10.

> **Status (October 29, 2026):** runs end to end from Blender to the app.
> - Blender: `build_scene.py` builds all 10 shots in code (Namek, placeholder toon Goku/Frieza, choreography, cameras, FX tracks, markers). `render_passes.py`, `bake_timeline.py`, `synth_audio.py` (self-synthesized music + SFX) and `tools/pack.sh` all work; a single `tools/build.sh` command produces `cinematic.mp4` + `timeline.json`.
> - App: video goes through `react-native-webgpu` into Skia v3; composite shader (matte-driven aura, beam, ki blast, explosion, shockwave, god rays, chromatic, impact frame, grade); overlay layer; lightning, sparks, title; 120Hz clock; haptics; Ki charge screen; scrub bar for the dev build. Typecheck and lint are clean; the iOS build succeeds.
> - Remaining: replace the placeholders with real models (P2), polish animation (P3), measure performance on a real iPhone (P6).

---

## 0. Summary

**Product.** A single iPhone app screen about 20 seconds long. On a storm-swept planet Namek, Goku powers up, his hair flickers gold, then he explodes into Super Saiyan for the first time. Frieza fires a Death Beam, Goku dodges, the two chase each other through the rock spires, and finally Goku counters with a single punch. The camera uses crash zooms, orbits, dolly zooms, whip pans and slow-mo. The screen shakes and the iPhone vibrates (haptics) on every impact.

**Chosen architecture: cinematic video + real-time FX.**

- Blender does all the 3D work: models, rigs, animation, every camera angle, lighting, cel-shading. The output is an HEVC "pack" video, meaning each frame contains the color image, Goku's matte (mask) and the energy layer.
- Blender also exports `timeline.json`: the on-screen coordinates of Goku's chest, head and fist, Frieza's finger, and so on for every frame, together with the effect tracks (aura, flash, shake...) that you keyframe right inside Blender.
- In the app, `react-native-webgpu` hardware-decodes the video straight into a GPU texture. `react-native-skia` v3 draws that texture through an SkSL shader: a fiery aura behind Goku (thanks to the matte), rim light, shockwave, impact frame, color grading. It then draws lightning, sparks, speed lines and the Death Beam on top, following the coordinates exported from Blender. Reanimated keeps a 120Hz clock locked to video time and drives the virtual camera (shake, punch-in), the UI and haptics.

**Why this approach.** Offline rendering gives the highest quality (motion blur, DOF, outlines, aura light spilling onto bodies and the ground), and hardware video decoding is always smooth. Small, fast-flickering details like fire, lightning and particles are drawn in real time at native resolution, because baking them into the video would break them up under compression. Real-time 3D rendering in the app is saved for version 2 (section 9); that version reuses all the assets and the FX layer.

**Estimate:** about 20–28 person-days. The bottleneck is character animation.

### Stack (checked on October 29, 2026)

| Part | Uses | Version | Notes |
|---|---|---|---|
| 3D | Blender | 5.2.2 LTS (your machine), latest 5.2.3 LTS | EEVEE + Shader to RGB for toon |
| App | Expo SDK 58, React Native | expo 58.0.21, RN 0.88.1, React 19.3 | dev build, New Architecture |
| 2D/GPU | `react-native-skia` | **3.8.1** | New name of `@shopify/react-native-skia` (the old package stops at 2.14). Graphite backend, running on Metal via Dawn |
| Video → GPU | `react-native-webgpu` | 0.19.2 | `createVideoPlayer()`. Shares the GPU device with Skia, so versions must match (0.17+ goes with Skia 3.7+) |
| Animation | `react-native-reanimated`, `react-native-worklets` | 4.7.1, 0.13.1 | `useFrameCallback`, `useDerivedValue`, `scheduleOnRN` |
| Gesture, haptics | `react-native-gesture-handler`, `expo-haptics` | per SDK 58 | "hold to charge Ki" screen |
| Encode | FFmpeg + libx265 | already installed (Homebrew) | HEVC Main10 |
| Concept, storyboard | Codex CLI (image gen) | already installed | |
| Controlling Blender externally | Blender MCP | | Not connected yet: Blender must be open with the addon enabled (section 5.0) |

---

## 1. Corrections to the research you sent

| Research | Reality as of October 2026 | Plan uses |
|---|---|---|
| `@shopify/react-native-skia` | The package was renamed to `react-native-skia`. v3 (released early October 2026) renders with Graphite. The `@shopify` package stops at 2.14 | `react-native-skia@3.8.1` |
| Custom GLSL shader | Skia uses SkSL (syntax close to GLSL, `half4 main(float2 xy)` function) | SkSL via `Skia.RuntimeEffect.Make` |
| `react-native-video` / `expo-av` plays the video, Skia overlays on top | Skia v3 drops `useVideo`. Video goes through `react-native-webgpu` into a texture and Skia draws that texture directly without copying, so shaders apply to the video itself rather than just overlaying it. `expo-av` is no longer in Expo SDK 58 | `createVideoPlayer()` → `copyExternalImageToTexture` → `Skia.Image.MakeFromGPUTexture` |
| Quick testing with Expo Go | Expo Go only ships Skia v2 | Dev build: `npx expo run:ios --device` |
| Low-poly models for mobile | The video is pre-rendered, so poly count doesn't affect the iPhone | Prioritize good-looking models and clean rigs |
| MP4/WebM with alpha | iOS hardware-decodes HEVC/H.264 best; WebM alpha isn't the main path on iOS | Pack the matte into the video frame itself (section 4.3) |
| Loading GLB in real time is "very heavy" | With Skia v3, three.js (WebGPU) shares the GPU device with Skia and hands over textures without copying, so it's more feasible than before | Left for version 2 (section 9) |
| 0–5s powering up, 5–10s transformation, 10–20s flying and dodging | If the transformation runs until second 10, there's no time left for the fight | Transformation fits in seconds 2–6.5, the rest is fighting (10 shots) |

---

## 2. The 20-second script

The setting is taken from the classic scene on Namek: Frieza has just killed Krillin, Goku is enraged and transforms for the first time (rewatch DBZ episode 95 to study composition and pacing). Namek's green sky turns stormy, purple lightning, the ground cracks.

Vertical 9:19.5 frame (fits the iPhone screen), 60fps, 1200 frames.

| # | Time (frames) | Shot | Camera (Blender) | Performance |
|---|---|---|---|---|
| 1 | 0.0–2.0 (0–119) | Storm over Namek | High drone shot, dolly-in while descending, 24mm | Black-haired Goku, torn gi, head bowed, fists clenched; Frieza hovers, smirking; the sky darkens |
| 2 | 2.0–4.0 (120–239) | Powering up | Low-angle, 40° orbit around Goku, 35mm | Fists tighten, rock debris floats up, the ground cracks outward |
| 3 | 4.0–5.0 (240–299) | The eyes | Eye close-up, slow push-in, crash zoom-in on the last 4 frames | Pupils flicker black ↔ teal, hair flashes gold in 3 beats |
| 4 | 5.0–6.5 (300–389) | Explosion | Crash zoom-out 135→24mm over 8 frames, pulling back | Hair stands up gold, aura explodes, shockwave flattens the ground, rocks fly |
| 5 | 6.5–8.5 (390–509) | Super Saiyan | Slow 180° orbit, stopping on a low-angle hero shot | Goku stands still, aura blazing, hair whipping, cold stare |
| 6 | 8.5–10.0 (510–599) | Frieza attacks | Dolly zoom on Frieza's face, cut to an over-the-shoulder angle behind Frieza | Frieza freezes, raises a finger and fires a volley of Death Beams |
| 7 | 10.0–13.0 (600–779) | Dodge | Bullet-time 90° orbit (speed 1 → 0.25 → 1), ending in a whip pan | Goku dodges beams with just a tilt of the head and a turn of the body; Frieza charges in with a combo, Goku dodges with afterimages (zanzoken) |
| 8 | 13.0–16.5 (780–989) | Aerial chase | Tailing shot along a curve threading through the rock spires, banking into turns, 2 whip pans | Frieza fires ki blasts, Goku flips to dodge, rock spires explode |
| 9 | 16.5–18.5 (990–1109) | Counter | Cut as Goku vanishes, 0.25s freeze, crash zoom into the point of impact | Goku appears behind Frieza, a single punch to the gut |
| 10 | 18.5–20.0 (1110–1199) | Ending | Slow pull-out to a wide shot, freeze frame | Frieza is knocked into the sea, a water column shoots up; Goku hovers, aura calming; title appears |

Effect layers per shot (audio is pre-mixed into the video):

| # | Skia (real-time) | Virtual camera (Reanimated) | Haptics | Audio |
|---|---|---|---|---|
| 1 | 2–3 purple lightning bolts in the sky, dust blowing sideways, vignette deepening, cool colors | | | wind, distant thunder, low music |
| 2 | Dust and small rocks rising, heat haze around the body, small electric sparks at the feet | shake 0 → 0.35 | light ticks, getting denser (140 → 50ms) | rising rumble, powering-up grunt |
| 3 | Chromatic aberration and a 2-frame gold flash on every hair flicker | slight punch-in on each beat | 3× `Rigid` | heartbeat |
| 4 | 3-frame impact frame (inverted black and white) → white flash → shockwave ring → aura explodes (spikes to 1.4 then back to 1) → god rays → radial speed lines | shake 1.0, decaying over 0.6s | 2× `Heavy` | big explosion, scream |
| 5 | 3-band aura burning continuously, gold sparks rising, gold rim, colors shift warm | | | aura hum, music swells |
| 6 | Pinkish-purple Death Beam from Frieza's finger, purple flare at the screen edges | small punch-in on each shot | `Light` per beam | beam sound, tense music |
| 7 | Beam sweeps past the camera, motion trails, particles and fire slow down with the slow-mo | | `Soft` on dodge, `Rigid` on block | slow-mo whoosh |
| 8 | Speed lines along the flight direction, ki blasts, cel-shaded explosions at points of impact | shake with explosions | `Medium` per explosion | speed wind, explosions |
| 9 | During the freeze: desaturate everything except gold; 2-frame impact frame, shockwave, speed lines from the point of impact | punch-in 1.0 → 1.12, shake 1.0 | 3× `Heavy` in a row | 0.25s of silence, then explosion |
| 10 | Calm aura, slow-drifting particles, letterbox slides in, gold "SUPER SAIYAN" title with a light sweep | spring scale for the title | `Success` | closing music |

Overall rhythm: build-up (0–5s) → explosion (5–6.5s) → show of power (6.5–8.5s) → action (8.5–18.5s) → wind-down (18.5–20s).

---

## 3. Art direction

Style: 3D anime cel-shading like Dragon Ball FighterZ. Worth watching the GDC 2015 talk "GuiltyGear Xrd's Art Style: The X Factor Between 2D and 3D" by Arc System Works, the studio behind FighterZ.

| Element | Color |
|---|---|
| Namek sky → storm | `#8FD18A` → `#24382E` |
| Grass/ground · water · rock spires | `#5FA38F` · `#3E9C9A` · `#7E9F86` |
| Lightning | core `#F1E6FF`, edge `#A27BFF` |
| SSJ aura | core `#FFF6C8`, middle `#FFD23F`, edge `#FF9F1C` |
| SSJ hair · SSJ eyes | `#FFD54A` (shadow `#E2A21B`) · `#2EC4B6` |
| Goku's gi | orange `#F28C28`, blue `#1F3A93` |
| Frieza · Death Beam | white `#F4F1F8`, purple `#8E3FBF`, eyes `#D7263D` · white core, edge `#FF5FD2` |

Principles:

- Shadows are colored (skin leans pinkish orange, the orange gi leans reddish brown), never black. Outlines are dark brown, thick on the silhouette, thin on interior lines.
- Aura and explosions are painted in 2–3 hard color bands like anime; soft glow only in the core.
- Big impacts get a 2–3 frame black-and-white impact frame.
- Smooth vs. "anime feel": by default character motion is interpolated at 60fps for smoothness; on impacts, hold the pose for 2–4 frames (hit-stop). Holding each pose for 2 frames like FighterZ can be tried at a few moments. Camera and FX are always smooth.

---

## 4. Technical architecture

### 4.1 Pipeline

```
Codex (concept, storyboard) ──► Blender 5.2: model · rig · animation · camera · EEVEE toon
                                   │
                                   ├─ render_passes.py ─► PNG beauty / matte / energy (1152×2496, 60fps)
                                   ├─ bake_timeline.py ─► timeline.json (2D anchors + FX tracks + markers)
                                   └─ VSE or DAW ───────► mix.wav (music + SFX)
                                              │
                        tools/pack.sh (FFmpeg) ─► cinematic.mp4 (HEVC Main10, 1728×2496, 60fps, BT.709)
                                              │
iPhone app (Expo SDK 58, dev build) ◄─────────┘
  react-native-webgpu   createVideoPlayer → copyExternalImageToTexture → GPUTexture
  react-native-skia v3  MakeFromGPUTexture → composite shader (tile split, aura, grade…) + FX layers
  Reanimated 4          120Hz clock locked to the video · virtual camera · UI · markers → haptics
```

### 4.2 What gets done where

| Effect | Done in | Reason |
|---|---|---|
| Models, cel-shading, outlines, motion blur, DOF | Blender | needs 3D geometry |
| Aura light spilling onto bodies and the ground | Blender (yellow light, intensity driven by `FX.aura`) | only 3D lights it correctly |
| Black → gold hair, black → teal eyes, flicker beats | Blender (material keyframes, mesh swap) | Skia only adds flash and chromatic |
| Flying rocks, cracking ground, water column, afterimages | Blender | tied to geometry |
| All camera moves (orbit, crash zoom, dolly zoom, whip pan) | Blender | real perspective, real motion blur |
| Golden fire aura | Skia, shader reading the matte | lively, sharp at any resolution, no compression artifacts |
| Lightning, electric sparks, speed lines, shockwave, impact frame, flash, color grading, grain | Skia | small details or pure post-processing |
| Death Beam, ki blasts, explosions | Skia following anchors, plus a light flash in Blender | |
| Dust, sparks, small debris | Skia (`Atlas` ≤ 300 sprites; fine dust drawn in the shader) | |
| Shake, punch-in | Reanimated (virtual camera) | in sync with haptics |
| Haptics | `expo-haptics` driven by markers | |
| Audio | Pre-mixed into the video | the player keeps picture and sound in sync on its own |

### 4.3 The "pack" video

```
           1152 px              576 px
  ┌─────────────────────┬────────────────┐
  │                     │ MATTE Goku     │ 1248
  │  BEAUTY (color)     │ (gray, ½ res)  │
  │  1152 × 2496        ├────────────────┤
  │  visible area       │ ENERGY         │ 1248
  │  1080×2340 + margin │ (gray, ½ res)  │
  └─────────────────────┴────────────────┘
     Frame 1728 × 2496 · 60fps · HEVC Main10 · BT.709
```

- Beauty is 1152×2496 (9:19.5, like recent iPhones). The visible part is the 1080×2340 in the middle; the roughly 3.3% margin on each side means virtual camera shake or punch-in never exposes the edges.
- Matte and energy are stored as grayscale (luma) images at ½ resolution. HEVC 4:2:0 halves the resolution of the color channels: if each matte were packed into its own R/G/B channel they would bleed into each other, while luma stays intact.
- Every dimension is a multiple of 16 to line up with the coding blocks. The shader clamps coordinates within each tile so it never samples pixels from the neighboring tile.
- Each frame is 4.3 MP, smaller than 4K (8.3 MP), so the iPhone's hardware decoder handles 60fps comfortably. Estimated size is 25–45 MB for 20 seconds (CRF 17).
- For a landscape frame, rotate the spec: beauty 2496×1152, with the two 1248×576 tiles stacked below.

### 4.4 `timeline.json`

```jsonc
{
  "fps": 60, "frames": 1200, "plate": [1152, 2496],
  "anchors": {               // 3 numbers per frame: x, y (px on the plate, origin top-left), z (depth to camera)
    "goku_chest": [576.2, 1320.5, 6.41 /* … */],
    "goku_head": [], "goku_fist_r": [], "frieza_finger": [], "beam_target": []
  },
  "tracks": {                // custom props of the "FX" Empty in Blender, 1 number per frame
    "aura": [], "flash": [], "shake": [], "punch": [], "speedlines": [], "impact": [],
    "grade": [], "lightning": [], "shock_r": [], "shock_k": [], "title": [],
    "fxclock": []            // running sum of FX.timescale: during slow-mo the in-app FX slow down too
  },
  "markers": [ { "f": 300, "name": "haptic:heavy" }, { "f": 390, "name": "cut" } ]
}
```

About 35 thousand numbers, around 200 KB, `require`d straight into the bundle.

### 4.5 Layers drawn each frame

```
<Canvas>  (Graphite · 120Hz on iPhone Pro)
 ├─ Fill + composite Shader    video frame + uniforms from the timeline
 │    virtual camera → shockwave → beauty → aura behind the back (matte) → rim → beam/ki blast (SDF)
 │    → energy glow → color grading → impact frame → grain
 ├─ Lightning                  Path + BlurMask, pinned to an anchor or the sky area
 ├─ Sparks / debris            Atlas ≤ 300 sprites, driven by fxclock
 ├─ SpeedLines                 SkSL, centered on an anchor or the middle of the screen
 ├─ Flash · vignette · letterbox
 └─ TitleCard                  Text + LinearGradient + spring
```

### 4.6 Clock and sync

- The video is the master clock. The audio lives in the video, so the player keeps picture and sound in sync on its own.
- The frame-pulling loop runs on JS (`requestAnimationFrame`, 60Hz): it grabs the new frame along with `player.currentTime` and writes it to the `videoTime` shared value.
- The UI thread (`useFrameCallback`, 120Hz) keeps a variable `t`: each frame it adds dt, then nudges it toward `videoTime`. If it drifts by more than 2 frames (seek, hitch), it jumps straight to `videoTime`.
- FX attached to characters (aura center, beams, lightning around the body) read anchors at exactly the video frame currently on screen (`round(videoTime × 60)`). The display runs at 120Hz but the video is only 60fps, so interpolating anchors would make the FX slide half a frame relative to the character. Free FX (fire noise, particles, shake) use `t` for smoothness.

---

## 5. Blender (5.2 LTS)

### 5.0 Connecting Blender MCP

Open Blender 5.2.2 and enable the MCP addon (if it isn't installed, run `uvx mcp-for-blender install-addon`, then re-enable the addon). From then on, scenes, cameras, materials and view layers can be built, and renders and bakes run, by script. At the time this plan was written, MCP couldn't connect to Blender because Blender wasn't open.

### 5.1 File structure

```
goku_vs_frieza.blend   60fps · 1152×2496 · frames 0–1199
├─ CHARS/   GOKU_RIG (body, hair_base, hair_ssj, eyes) · FRIEZA_RIG (body, tail)
├─ ENV/     terrain, spires, ajisa_trees, sea, sky_dome, clouds, debris
├─ LIGHTS/  key_sun, rim, aura_lights (driven by FX.aura)
├─ CAMS/    CAM_01 … CAM_10 (bound to markers)
└─ CTRL/    FX (Empty, custom props), BEAM_TARGET
```

### 5.2 Assets

Goku, in order of preference:

1. A rigged, downloadable model on Sketchfab with a license that allows it (filter with `search_assets` once MCP is running).
2. Codex draws a T-pose turnaround → `generate_3d` (image → 3D, 1–3 minutes, may cost credits) → remesh, clean up the mesh, rig.
3. Build it ourselves.

Whatever the source, it must:

- Split the hair into separate meshes: `hair_base` (black) and `hair_ssj` (gold, spiked up). The transformation is a mesh swap plus shape keys.
- Use separate materials for the eyes and eyebrows so their colors can change.
- Have shape keys `ssj_bulk` (slightly bigger muscles), `angry`, `scream`. The torn Namek-style gi is optional.

Frieza (final form): simple shapes, a white body with purple patches, the easiest to build ourselves. The tail is rigged with a bone chain + Spline IK.

Namek: built procedurally with a script or Geometry Nodes. Includes ground with cracks (animated mask), flat-topped rock spires, Ajisa trees (slender trunks, round canopies), sea, gradient sky, toon clouds. For a bit of extra detail, pull CC0 textures from Poly Haven.

Poly count doesn't affect the iPhone because the video is pre-rendered; all that matters is a clean rig and fast renders.

### 5.3 Toon in EEVEE

1. Character material: `Diffuse BSDF → Shader to RGB → ColorRamp (Constant, 2–3 steps)` multiplied by the base color → `Emission`. Add `Layer Weight → ColorRamp` for the rim.
2. Lights: 1 Sun as the key, with its direction tuned per shot (cheating per camera angle is allowed); flat-colored world.
3. Inverted-hull outline: `Solidify` modifier (negative offset, Flip Normals, Material Offset pointing to a dark-brown outline material, Backface Culling on), thickness from a vertex group. For interior lines, add Grease Pencil Line Art.
4. Face: custom normals (Data Transfer from an ellipsoid) so facial shading stays clean like anime, the exact technique used by Guilty Gear Xrd and FighterZ.
5. Color Management: View Transform **Standard** (the default AgX washes out anime colors), Look None, keep Dither 1.0; Film Filter around 1.0px for crisp lines.
6. Aura lights: yellow point/area lights around Goku, intensity driven by `FX["aura"]`. That way the aura Skia draws in the app always matches the light spilling onto the body and ground in Blender.

### 5.4 Rig and animation

- Rig: Mixamo auto-rig (fast) or Rigify. Grab base clips from Mixamo (fighting stance, punch, dodge, hover, getting hit) → retarget → hand-tweak to match the animatic.
- Poses must read strongly from that shot's camera; per-shot pose tweaks are allowed. Impacts get 2–4 frames of hit-stop; fast moves rely on motion blur.
- Transformation keyframes:
  - f240–299: `hair_base` and `hair_ssj` alternate 3 times (3–4 frames each), eyes change color on the same beat.
  - f300: switch fully to `hair_ssj`; shape key `grow` 0 → 1 over 6 frames (hair stands up); `ssj_bulk` 0 → 1; hair emission 3 → 1 (flare then settle); aura lights 0 → max.
  - f300–330: rocks fly (rigid body bake or keyframes), cracks spread.
- Zanzoken (shot 7): duplicate Goku's mesh at the old spot, transparent material fading out over 8–10 frames.
- Slow-mo (shot 7): animate slowly directly, don't use Time Stretching since it applies to the whole file. Keyframe `FX.timescale` 1 → 0.25 → 1 so the in-app FX slow down to match.

### 5.5 Camera

- One `CAM_xx` camera per shot. Place a marker at the start of each shot, then **Bind Camera to Markers** (Ctrl+B in the timeline): render the full 20 seconds in one go, with cuts happening automatically.
- Crash zoom: animate the focal length (e.g. 135 → 24mm over 6–8 frames, strong ease-in) with a slight move.
- Dolly zoom: pull the camera back while increasing focal length so the subject stays the same size, driver `focal = focal0 × distance / distance0`.
- Orbit: parent the camera to an Empty placed at Goku, rotate the Empty around Z; `Track To` the chest bone.
- Chase: `Follow Path` along a Bezier curve threading through the rock spires, `Track To` Goku, roll into the turns.
- Whip pan: rotate 60–90° over 4–6 frames with motion blur on; put the cut in the middle of the pan.
- Handheld shake: a very light Noise modifier on the rotation F-curves. Leave strong shake to the app to avoid shaking twice.
- Light DOF for close-ups; EEVEE motion blur (shutter 0.5) for the whole clip.

### 5.6 FX tracks and markers

- The `FX` Empty has float custom props: `aura, flash, shake, punch, speedlines, impact, grade, lightning, shock_r, shock_k, timescale, title`. Keyframe them in the Graph Editor like any other animation, so effect timing is tuned right next to the animatic.
- Markers follow a naming convention: `haptic:heavy`, `haptic:rigid`, `cut`, `beam`, `explode`. Camera-binding markers keep the shot name.

### 5.7 Render

- EEVEE, 1152×2496, 60fps, frames 0–1199, motion blur on.
- View layers `BEAUTY` (full) and `MATTE_GOKU` (ENV and Frieza collections set to Holdout, flat white material override, Alpha channel taken). This gives the matte exactly the same motion blur and DOF as the beauty.
- Energy: the Emission pass of `BEAUTY`, converted to grayscale in the compositor.
- Output 16-bit PNG through File Output nodes: `render/beauty/####.png`, `render/matte/####.png`, `render/energy/####.png`.
- Estimate on an M5 Pro: 1–2 seconds per frame per layer, about 1 hour for a full render. A 50% preview without motion blur takes about 10 minutes.

### 5.8 `bake_timeline.py`

```python
# Run: /Applications/Blender.app/Contents/MacOS/Blender -b blender/goku_vs_frieza.blend -P blender/scripts/bake_timeline.py
import bpy, json
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.context.scene
W, H = scene.render.resolution_x, scene.render.resolution_y        # 1152 × 2496
FPS = scene.render.fps
ANCHORS = {                                                         # rename bones to match the real rig
    "goku_chest":    ("GOKU_RIG", "mixamorig:Spine2"),
    "goku_head":     ("GOKU_RIG", "mixamorig:Head"),
    "goku_fist_r":   ("GOKU_RIG", "mixamorig:RightHand"),
    "frieza_finger": ("FRIEZA_RIG", "mixamorig:RightHandIndex3"),
    "beam_target":   ("BEAM_TARGET", None),
}
TRACKS = ["aura", "flash", "shake", "punch", "speedlines", "impact", "grade",
          "lightning", "shock_r", "shock_k", "title"]
fx = bpy.data.objects["FX"]

out = {"fps": FPS, "frames": 0, "plate": [W, H],
       "anchors": {k: [] for k in ANCHORS}, "tracks": {k: [] for k in TRACKS + ["fxclock"]}}
clock = 0.0
for f in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(f)                                              # marker-bound cameras switch here too
    for name, (obj, bone) in ANCHORS.items():
        ob = bpy.data.objects[obj]
        world = ob.matrix_world @ ob.pose.bones[bone].head if bone else ob.matrix_world.translation
        v = world_to_camera_view(scene, scene.camera, world)       # x, y ∈ [0, 1] origin bottom-left; z = depth
        out["anchors"][name] += [round(v.x * W, 1), round((1 - v.y) * H, 1), round(v.z, 2)]
    for k in TRACKS:
        out["tracks"][k].append(round(float(fx[k]), 4))
    out["tracks"]["fxclock"].append(round(clock, 4))
    clock += float(fx["timescale"]) / FPS                           # during slow-mo the in-app FX slow down too
    out["frames"] += 1

out["markers"] = sorted(({"f": m.frame, "name": m.name} for m in scene.timeline_markers),
                        key=lambda m: m["f"])
with open(bpy.path.abspath("//../app/assets/cinematic/timeline.json"), "w") as fp:
    json.dump(out, fp, separators=(",", ":"))
```

### 5.9 Pack and encode

```bash
# tools/pack.sh: 3 PNG sequences + audio → 1 pack video
ffmpeg -y \
  -framerate 60 -i render/beauty/%04d.png \
  -framerate 60 -i render/matte/%04d.png \
  -framerate 60 -i render/energy/%04d.png \
  -i render/audio/mix.wav \
  -filter_complex "
    [1:v]format=gray16le,scale=576:1248:flags=area,format=gbrp16le[m];
    [2:v]format=gray16le,scale=576:1248:flags=area,format=gbrp16le[e];
    [m][e]vstack=inputs=2[data];
    [0:v]format=gbrp16le[b];
    [b][data]hstack=inputs=2,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le[v]" \
  -map "[v]" -map 3:a \
  -c:v libx265 -preset slow -crf 17 -x265-params keyint=60:min-keyint=60 \
  -tag:v hvc1 -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  app/assets/cinematic/cinematic.mp4
```

- `-tag:v hvc1`: without it, iOS won't accept the HEVC file.
- `out_color_matrix=bt709`: if not forced, FFmpeg may convert colors with the BT.601 matrix, and colors shift on the iPhone.
- A keyframe every second for fast seeking and "Replay".
- For previews, switch to the Mac's `hevc_videotoolbox` hardware encoder for speed.

### 5.10 Audio

Music and SFX come from royalty-free sources (Freesound CC0, Pixabay). Mix in the Blender VSE to hear it alongside the animatic, or in a DAW, then export `render/audio/mix.wav` at 48kHz. Don't use the anime's original music or voices.

---

## 6. App

### 6.1 Setup

```bash
cd ~/Documents/git/personal-repo/goku-vs-frieza
npx create-expo-app@latest app --template blank-typescript        # Expo SDK 58
cd app
npx expo install react-native-reanimated react-native-worklets react-native-gesture-handler \
  expo-haptics expo-asset expo-font expo-dev-client
npm i react-native-skia@^3.8.1 react-native-webgpu@^0.19.2
npm ls react-native-webgpu-dawn       # there must be only 1 version (Skia and WebGPU share Dawn)
npx expo run:ios --device              # dev build on a real iPhone
```

- Expo SDK 58 still pins `@shopify/react-native-skia@2.14` (v2), so install `react-native-skia` v3 manually as above. Don't install both packages side by side, since they share the same native module.
- Installing on an iPhone: a free Apple ID can sign the dev build (expires after 7 days); TestFlight needs a paid developer account.

`app.json`:

```json
{
  "expo": {
    "orientation": "portrait",
    "ios": {
      "supportsTablet": false,
      "infoPlist": { "CADisableMinimumFrameDurationOnPhone": true }
    }
  }
}
```

`CADisableMinimumFrameDurationOnPhone` unlocks 120Hz on ProMotion iPhones; without it, animation is capped at 60Hz.

### 6.2 Folder structure

```
goku-vs-frieza/
├─ PLAN.md
├─ blender/
│  ├─ goku_vs_frieza.blend
│  └─ scripts/   setup_scene.py · toon_materials.py · render_passes.py · bake_timeline.py
├─ render/       (not committed) beauty/ · matte/ · energy/ · audio/mix.wav
├─ tools/        pack.sh · preview.sh (render 50% → pack → copy into the app)
└─ app/          Expo
   ├─ assets/cinematic/   cinematic.mp4 · timeline.json · sparks.png · fonts/
   └─ src/
      ├─ screens/CinematicScreen.tsx
      ├─ cinematic/
      │  ├─ useCinematicVideo.ts    video → SkImage
      │  ├─ timeline.ts             reads tracks and anchors (worklet)
      │  ├─ haptics.ts              markers → expo-haptics
      │  ├─ shaders/                composite · speedLines · explosion
      │  └─ layers/                 Lightning · Sparks · SpeedLines · Flash · TitleCard
      ├─ ui/                        KiChargeIntro · ReplayButton
      └─ dev/Scrubber.tsx           frame scrubbing, toggle each FX layer
```

### 6.3 Video → Skia

```ts
// src/cinematic/useCinematicVideo.ts
import { useEffect, useRef } from "react";
import { useSharedValue } from "react-native-reanimated";
import { Skia, type SkImage } from "react-native-skia";
import { createVideoPlayer, importDevice, type VideoPlayer } from "react-native-webgpu";

// Hardware decode → texture on Skia's GPU device → SkImage, never touching the CPU
export function useCinematicVideo(uri: string | null) {
  const frame = useSharedValue<SkImage | null>(null);
  const videoTime = useSharedValue(0);
  const player = useRef<VideoPlayer | null>(null);

  useEffect(() => {
    if (!uri) return;
    const device = importDevice(Skia.getNativeDevice());
    const p = createVideoPlayer(uri);
    p.loop = false;    // defaults to true
    p.volume = 1;
    p.currentTime = 0; // still returns the first frame while paused, for the intro screen
    player.current = p;

    let texture: GPUTexture | null = null;
    let raf = 0;
    const pump = () => {
      const f = p.copyLatestFrame();
      if (f) {
        if (!texture || texture.width !== f.width || texture.height !== f.height) {
          const old = frame.value;
          frame.value = null;
          old?.dispose();
          texture?.destroy();
          texture = device.createTexture({
            size: [f.width, f.height],
            format: navigator.gpu.getPreferredCanvasFormat(),
            usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING,
          });
        }
        // YUV → RGB happens on the GPU; the video is encoded upright, so no need to swap width/height
        device.queue.copyExternalImageToTexture(
          { source: f, rotation: p.rotation },
          { texture },
          [f.width, f.height],
        );
        f.release(); // hand the buffer back to the decoder right away
        const old = frame.value;
        frame.value = Skia.Image.MakeFromGPUTexture(texture); // a new image makes the Canvas redraw
        old?.dispose();
        videoTime.value = p.currentTime;
      }
      raf = requestAnimationFrame(pump);
    };
    raf = requestAnimationFrame(pump);

    return () => {
      cancelAnimationFrame(raf);
      p.release();
      const last = frame.value;
      frame.value = null;
      last?.dispose();
      texture?.destroy();
    };
  }, [uri, frame, videoTime]);

  return { frame, videoTime, player };
}
```

- `requestAnimationFrame` on JS is capped at 60Hz, which happens to match the video's 60fps. Spike P1 tries running the frame-pulling loop in a worklet on the UI thread (120Hz, no hitches from the JS thread). Whether that works depends on whether `VideoPlayer` can be passed into a worklet.
- File path: `expo-asset`'s `useAssets(require("../../assets/cinematic/cinematic.mp4"))` → `localUri`.

### 6.4 Composite shader (sketch; constants will be tuned on device)

```ts
// src/cinematic/shaders/composite.ts
import { Skia } from "react-native-skia";

export const composite = Skia.RuntimeEffect.Make(`
uniform shader video;    // 1728×2496 pack frame
uniform float2 view;     // canvas size (pt)
uniform float  pxScale;  // plate px per screen pt (cover)
uniform float4 cam;      // xy: pan (plate px), z: zoom, w: rotation (rad)
uniform float  t;        // fxclock (seconds)
uniform float2 chest;    // Goku chest anchor (plate px)
uniform float  aura;     // 0..1.4
uniform float  grade;    // 0: cold Namek → 1: SSJ gold
uniform float  impact;   // 1: black-and-white impact frame
uniform float4 shock;    // xy: center, z: radius, w: strength

const float2 PLATE  = float2(1152.0, 2496.0);
const float2 MATTE  = float2(1152.0, 0.0);
const float2 ENERGY = float2(1152.0, 1248.0);

float hash(float2 p) { return fract(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
float noise(float2 p) {
  float2 i = floor(p); float2 f = fract(p); float2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + float2(1, 0)), u.x),
             mix(hash(i + float2(0, 1)), hash(i + float2(1, 1)), u.x), u.y);
}
float fbm(float2 p) {
  float v = 0.0; float a = 0.5;
  for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
  return v;
}
// ½-resolution tile; clamp coordinates so sampling never spills into the neighboring tile
float tile(float2 origin, float2 p) {
  return video.eval(origin + clamp(p * 0.5, float2(0.5), PLATE * 0.5 - 0.5)).r;
}

half4 main(float2 xy) {
  // 1. Screen → plate through the virtual camera (shake, punch-in, rotation)
  float2 c = xy - 0.5 * view;
  float s = sin(cam.w); float k = cos(cam.w);
  c = float2(c.x * k - c.y * s, c.x * s + c.y * k) / cam.z;
  float2 p = 0.5 * PLATE + c * pxScale + cam.xy;

  // 2. Shockwave: push the sample point around the wave ring
  float2 d = p - shock.xy;
  float r = length(d);
  float x = (r - shock.z) / 40.0;
  p -= d / max(r, 1.0) * exp(-x * x) * shock.w * 30.0;

  half4 col = video.eval(clamp(p, float2(0.5), PLATE - 0.5));
  float m = tile(MATTE, p);

  // 3. Aura behind Goku: a halo from the matte dragged upward by noise, plus an "egg" around the chest,
  //    painted in 3 hard anime color bands
  if (aura > 0.001) {
    float2 flow = float2(0.0, t * 1.6);
    float n = fbm(p / 90.0 + flow);
    float2 q = p + (float2(fbm(p / 60.0 + flow + 7.0), n) - 0.5) * float2(70.0, 160.0);
    float halo = 0.0;
    for (int i = 0; i < 8; i++) {
      float ang = float(i) * 0.785398;
      halo += tile(MATTE, q + float2(cos(ang), sin(ang) * 1.4 + 0.6) * 44.0);
    }
    float2 e = (p - chest) / float2(260.0, 430.0);
    float egg = smoothstep(1.0, 0.6, length(e) + (n - 0.5) * 0.6);
    float a = max(halo / 8.0, egg * 0.8) * aura * (1.0 - m);
    float band = a > 0.75 ? 1.0 : (a > 0.45 ? 0.66 : (a > 0.2 ? 0.33 : 0.0));
    col.rgb = mix(col.rgb, mix(half3(1.0, 0.62, 0.11), half3(1.0, 0.96, 0.78), band), band * 0.85);
    // gold rim along Goku's upper edges
    col.rgb += half3(1.0, 0.82, 0.3) * m * (1.0 - tile(MATTE, p - float2(0.0, 8.0))) * aura;
  }

  // 4. Glow from the energy layer (ki, eyes) rendered in Blender
  col.rgb += half3(1.0, 0.9, 0.6) * tile(ENERGY, p) * 0.5;

  // 5. Per-shot color grading
  float l = dot(col.rgb, half3(0.299, 0.587, 0.114));
  half3 cold = mix(half3(l), col.rgb, 0.7) * half3(0.92, 1.0, 1.05);
  col.rgb = mix(cold, col.rgb * half3(1.08, 1.02, 0.9), grade);

  // 6. Impact frame: dark areas turn white, bright areas turn black
  if (impact > 0.5) { col.rgb = half3(step(l, 0.45)); }

  // 7. Light grain against banding
  col.rgb += (hash(xy + fract(t) * 91.7) - 0.5) * 0.008;
  return col;
}`)!;
```

To be added to this same shader: beams and ki blasts drawn as line-segment or circle SDFs (up to 4, passed via uniforms), so when they fly behind Goku they're correctly occluded thanks to the matte; heat haze (noise-offset coordinates around the halo); god rays (sampling the energy tile along the direction toward the chest center).

### 6.5 Clock, timeline, virtual camera, haptics (sketch)

```tsx
// src/cinematic/timeline.ts
import data from "../../assets/cinematic/timeline.json";

export const FPS = data.fps;
export const TR = data.tracks as Record<string, number[]>;
export const AN = data.anchors as Record<string, number[]>;
export const HAPTICS = data.markers
  .filter((m) => m.name.startsWith("haptic:"))
  .map((m) => ({ t: m.f / FPS, style: m.name.slice(7) }));

// Linearly interpolate a track at a time (seconds)
export const track = (arr: number[], t: number) => {
  "worklet";
  const f = Math.min(Math.max(t * FPS, 0), arr.length - 1);
  const i = Math.floor(f);
  const j = Math.min(i + 1, arr.length - 1);
  return arr[i] + (arr[j] - arr[i]) * (f - i);
};

// Anchor at exactly the video frame on screen, so FX stick tightly to the character
export const anchor = (arr: number[], frame: number): [number, number] => {
  "worklet";
  const i = Math.min(Math.max(frame, 0), arr.length / 3 - 1) * 3;
  return [arr[i], arr[i + 1]];
};

// 1D value noise in the range -1..1, used for screen shake
export const n1 = (x: number) => {
  "worklet";
  const i = Math.floor(x);
  const u = (x - i) * (x - i) * (3 - 2 * (x - i));
  const h = (k: number) => {
    const s = Math.sin(k * 127.1) * 43758.5453;
    return s - Math.floor(s);
  };
  return (h(i) + (h(i + 1) - h(i)) * u) * 2 - 1;
};
```

```tsx
// src/cinematic/haptics.ts
import * as Haptics from "expo-haptics";

const IMPACT: Record<string, Haptics.ImpactFeedbackStyle> = {
  light: Haptics.ImpactFeedbackStyle.Light,
  medium: Haptics.ImpactFeedbackStyle.Medium,
  heavy: Haptics.ImpactFeedbackStyle.Heavy,
  rigid: Haptics.ImpactFeedbackStyle.Rigid,
  soft: Haptics.ImpactFeedbackStyle.Soft,
};

export const fireHaptic = (style: string) =>
  style === "success"
    ? Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
    : Haptics.impactAsync(IMPACT[style] ?? Haptics.ImpactFeedbackStyle.Medium);
```

```tsx
// src/screens/CinematicScreen.tsx (excerpt)
const { frame, videoTime, player } = useCinematicVideo(uri);
const { size, onLayout } = useCanvasSize();
const t = useSharedValue(0);
const lastT = useSharedValue(0);
const playing = useSharedValue(false);

useFrameCallback(({ timeSincePreviousFrame }) => {
  "worklet";
  if (!playing.value) return;
  const next = t.value + (timeSincePreviousFrame ?? 0) / 1000;
  const err = videoTime.value - next;
  // Off by more than 2 frames (seek, hitch): jump straight there; otherwise nudge gently toward the video for smoothness
  t.value = Math.abs(err) > 2 / FPS ? videoTime.value : next + err * 0.1;
  for (const h of HAPTICS) {
    if (lastT.value < h.t && t.value >= h.t) scheduleOnRN(fireHaptic, h.style);
  }
  lastT.value = t.value;
});

const uniforms = useDerivedValue(() => {
  const ft = track(TR.fxclock, t.value);
  const trauma = track(TR.shake, t.value) ** 2; // shake by trauma² for a natural feel
  const [cx, cy] = anchor(AN.goku_chest, Math.round(videoTime.value * FPS));
  return {
    view: [size.width, size.height],
    pxScale: Math.min(1080 / size.width, 2340 / size.height),
    // total shake + rotation amplitude must stay within the overscan margin (36/78 px)
    cam: [
      trauma * 24 * n1(ft * 23),
      trauma * 24 * n1(ft * 23 + 7.3),
      1 + track(TR.punch, t.value),
      trauma * 0.01 * n1(ft * 17 + 3.1),
    ],
    t: ft,
    chest: [cx, cy],
    aura: track(TR.aura, t.value),
    grade: track(TR.grade, t.value),
    impact: track(TR.impact, t.value),
    shock: [cx, cy, track(TR.shock_r, t.value), track(TR.shock_k, t.value)],
  };
});

return (
  <Canvas style={StyleSheet.absoluteFill} onLayout={onLayout}>
    <Fill>
      <Shader source={composite} uniforms={uniforms}>
        <ImageShader image={frame} />
      </Shader>
    </Fill>
    {/* Lightning, Sparks, SpeedLines, Flash, TitleCard… */}
  </Canvas>
);
```

### 6.6 Remaining FX layers

- Lightning: `usePathValue` generates bolts with midpoint displacement, changing the seed about every 70ms. Drawn in 2 layers: a thick stroke with `BlurMask` for glow and a thin white core.
- Sparks, debris: `Atlas` + `useRSXformBuffer`, up to about 300 sprites (Graphite draws atlases one sprite at a time, but a few hundred is still fine). Positions are computed directly from the seed and `fxclock`, so no state needs to be stored; the seed changes after each `cut` marker. Large amounts of fine dust are drawn in a shader.
- Speed lines: SkSL by angle (`atan2`) plus noise, masked by radius; centered on the fist anchor or the middle of the screen.
- Explosions: SkSL noise sphere painted in 3 cel bands with a smoke ring, placed at an anchor; Blender has a light flash on the same frame.
- Flash, vignette, letterbox: `Fill` with blend modes; the letterbox is 2 `Rect`s sliding in.
- Title: a bold font (Bangers or Anton, Google Fonts, OFL license), filled with a gold `LinearGradient`, a light streak sweeping across, scaled with `withSpring`, with the subtitle "スーパーサイヤ人".
- Dev scrubber (dev build only): drag to seek `currentTime`, shows the frame number and shot name, toggles each FX layer. This is the main tool for tuning timing.

### 6.7 The "hold to charge Ki" screen

- Show the first frame (the player is paused; setting `currentTime = 0` provides a frame), darkened, with the text "Hold to charge Ki".
- While holding: the Ki bar (Skia, gold gradient) fills over about 1.5 seconds, with screen shake and increasingly dense haptics. Releasing early makes the bar drain back.
- Meanwhile, get everything ready: the player is created and paused; every shader has been drawn once at zero intensity so Graphite compiles the pipelines ahead of time (avoiding a hitch on the first frame); fonts and textures are loaded.
- Bar full → white flash → `player.play()` → run the cinematic. After 20 seconds, show the title and a "Replay" button (`currentTime = 0`).

### 6.8 Performance

- Target: the FX layer runs at 120fps on iPhone Pro (13 Pro and up), a steady 60fps from iPhone 12; video at 60fps.
- GPU budget of about 6ms per frame at 120Hz: 1 composite pass (about 10 samples), 4-octave fbm aura, up to 300 sprites, 1 small blur layer.
- No `setState` and no React re-renders while running; every value goes through shared values.
- Two quality levels, `full` and `lite` (fewer noise octaves, fewer particles, god rays off), like the `fx-budget` pattern in Pastel Studio.
- Measure with Xcode Instruments (Animation Hitches, Metal System Trace) and GPU frame capture; log frames whose `timeSincePreviousFrame` exceeds 9ms.
- Memory: one 1728×2496 BGRA texture is about 17 MB, created once and reused.

---

## 7. Roadmap

| Phase | Work | Result | Estimate |
|---|---|---|---|
| P0 Script | 10-frame storyboard with Codex; animatic in the Blender VSE with temp music; lock the 20-second timing | `animatic.mp4`, final shot list | 1–2 days |
| P1 Spike (most important) | Blender renders a dummy scene (capsule blocks + camera) to 3 passes and `timeline.json` → pack → app: video through WebGPU into Skia, tile split, aura around the matte, 120Hz, marker-driven haptics, with sound | Pipeline runs end to end on a real iPhone | 2 days |
| P2 Assets and look | Goku (base + SSJ), Frieza, Namek; toon materials, outlines, rigs | 360° turntable renders of both characters | 4–6 days |
| P3 Animation and camera | Blocking from the animatic → spline → polish; 10 cameras + markers; FX keyframes | Full 20-second preview | 6–10 days |
| P4 Render pipeline | `render_passes.py`, `bake_timeline.py`, `pack.sh`, `preview.sh` | One command: render → pack → copy into the app | 1–2 days, in parallel with P2 |
| P5 FX and UI | All Skia layers, per-shot color, Ki charge intro, title, haptics, dev scrubber | Complete version | 4–6 days |
| P6 On-device polish | Instruments measurements, `lite` level, sync alignment, audio mix | Final version | 2 days |

Spike P1 passes when:

- The 1728×2496 HEVC Main10 pack video plays on a real iPhone, and the shader reads the matte tile correctly with no bleeding.
- The FX layer runs at 120Hz without hitches (per Instruments) while the video plays at 60fps.
- There is sound, i.e. `createVideoPlayer` can play audio. If not, switch to `expo-audio` and align the picture to the audio.
- FX drift from the video by no more than 1 frame: burn the frame number in with Blender, have Skia draw the frame number it computes, record the screen and compare.
- The worklet frame-pulling loop has been tried.

Version 1 is done when: the full 20 seconds plays; opening the app reaches the intro screen in under 1.5 seconds; 3 consecutive runs on an iPhone Pro have no hitches; the app is under 60 MB; "Replay" works correctly; audio and haptics land on the beat.

What can be done entirely in code: all of the app code; the Blender scripts (scene building, toon materials, view layers, render, bake, pack); procedural Namek, camera and marker placement via Blender MCP; storyboard and concepts with Codex. What needs you: choosing and approving models, polishing animation (rough poses can be blocked by script, but hand-tweaking still looks better), approving the audio, testing on a real iPhone.

---

## 8. Risks

| Risk | Level | Mitigation |
|---|---|---|
| 20 seconds of animation costs more than expected | High | Mixamo as a base; fast cuts, motion blur and FX hide a lot; if late, cut shot 8 down to 2 seconds |
| Goku/Frieza models fall short (license, quality) | Medium | The 3 sources in order from section 5.2; the hair is always made in-house |
| Skia v3 is brand new (10/2026) and has bugs | Medium | Fall back to `react-native-skia@2`, which still has `useVideo`; the shader and FX layers stay the same, only frame grabbing changes |
| `createVideoPlayer` plays no audio, or frames arrive unevenly | Medium | Check in spike P1; fallback to `expo-audio` and align the picture to the audio; grab frames in a worklet |
| First-frame hitch from pipeline compilation | Low | Warm up on the intro screen |
| Colors in Blender differ from the iPhone | Low | View Transform Standard, BT.709 tags, force the bt709 matrix when encoding, compare on a real device |
| Matte bleeds under compression | Low | Luma tiles, CRF 16–18, dimensions in multiples of 16, coordinate clamping |
| Video too heavy | Low | Tune CRF, or download the video on first launch |

---

## 9. Version 2 (optional): real-time 3D, interactive

- Skia v3 and `react-native-webgpu` share the GPU device. three.js (`three/webgpu`, r186) renders offscreen into a texture, `Skia.Image.MakeFromGPUTexture` wraps it, and it then goes through exactly the same composite shader and FX layers as version 1. The matte comes from a second render target (MRT); anchors are computed with `Vector3.project(camera)` instead of being read from JSON.
- Assets: export GLB from the same Blender file (Draco or meshopt compression, KTX2 textures), keeping the animation and shape keys. Toon uses `MeshToonNodeMaterial` with a 3-step gradient, inverted-hull outlines.
- Gains: interactivity (swipe to orbit the camera during the freeze, tap to dodge), a lighter app, sharp at any resolution, real 3D at 120Hz.
- Losses: offline-quality motion blur and DOF; roughly 2–3 extra weeks; keeping 120Hz requires running three.js on the worklet runtime (react-native-worklets Bundle Mode, still experimental).
- `react-native-filament` (1.11) can also load GLB with a native renderer, but it doesn't share the device with Skia, so shaders can't be applied to the 3D image.

---

## 10. Decisions to lock in

The plan is written around the choices in bold.

1. Frame: **vertical 9:19.5**, or landscape.
2. Style: **FighterZ-style anime cel-shading**, or semi-realistic 3D like Sparking! Zero.
3. Model source: **Sketchfab first, then `generate_3d`, finally build ourselves**.
4. "Hold to charge Ki" screen before the cinematic: **yes**, or go straight in.
5. Character motion timing: **smooth 60fps**, or anime-style 2-frame pose holds in a few scenes.

---

## 11. Copyright

Goku and Frieza are copyrighted by Bird Studio, Shueisha and Toei Animation. A personal demo or portfolio piece is fine, but don't release it on the App Store (Apple will reject it under Guideline 5.2 on intellectual property) and don't use the original music or voices. Read the license of any downloaded model: many fan-made models are CC BY-NC or forbid redistribution. To release it, replace them with characters of your own design; the pipeline stays the same.

---

## 12. References

- React Native Skia v3, migrating from v2: https://wcandillon.github.io/react-native-skia/docs/getting-started/migration
- React Native Skia and WebGPU (video, three.js, texture sharing): https://wcandillon.github.io/react-native-skia/docs/webgpu
- React Native WebGPU, Video Player API: https://wcandillon.github.io/react-native-webgpu/api/video-player
- React Native WebGPU, running on worklets: https://wcandillon.github.io/react-native-webgpu/docs/integrations/worklets
- Reanimated, performance and 120fps: https://docs.swmansion.com/react-native-reanimated/docs/guides/performance
- Blender 5.2 LTS: https://www.blender.org/download/
- GDC 2015, "GuiltyGear Xrd's Art Style: The X Factor Between 2D and 3D" (Junya C. Motomura, Arc System Works)
- GDC 2016, "Math for Game Programmers: Juicing Your Cameras With Math" (Squirrel Eiserloh): screen shake by trauma²
