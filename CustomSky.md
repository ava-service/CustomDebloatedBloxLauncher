📦 Step 1: Understand Skybox Structure

A skybox is a cube with 6 faces:
   •    Up (top)
   •    Down (bottom)
   •    Left
   •    Right
   •    Front
   •    Back

Each face gets its own image.

⸻

🖼️ Step 2: Create or Find the 6 Images

You can:
   •    Make your own in Photoshop, GIMP, or Blender
   •    Use a 3D rendering tool (like Unity, Blender, or Skybox AI generators)
   •    Or grab a free one from Poly Haven, AmbientCG, or similar

Make sure each image is:
   •    Square (512x512 or 1024x1024)
   •    Labeled correctly so they match the cube face (see below)

Example filenames:
```
sky512_up.png
sky512_dn.png
sky512_lf.png
sky512_rt.png
sky512_ft.png
sky512_bk.png
```

You can use a panorama-to-skybox converter (like [this one](https://matheowis.github.io/HDRI-to-CubeMap/) or [This](https://skybox-generator.vercel.app/)) to break a single 360° image into 6 cube faces.

⸻

🧰 Step 3: Convert PNGs to .tex

**You can just change the .png
To .tex**

If you’re replacing files in Roblox’s install folder (e.g. sky512_up.tex), you need .tex format.

Since Roblox uses a custom .tex format, there’s no official converter, but if you’ve already:
   •    Downloaded working .tex files
   •    Or have a tool that reads/writes .tex

Then just replace each .tex file’s contents using your PNGs.

If you don’t have a converter, try using:
   •    A modded tool like Texture Tool, Noesis, or a game-specific converter (won’t work 100% unless it targets Roblox-style .tex)
   •    Or inject your textures at runtime via shaders, scripts, or asset spoofing

⸻

🔁 Step 4: Replace Roblox Files

You can use [this](https://github.com/eman225511/CustomDebloatedBloxLauncher) tool for that 
by placing all the .tex files into a folder you can also include a .PNG for a preview 
then in the app select custom skybox folder then apply
