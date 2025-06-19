📦 Step 1: Understand Skybox Structure

A skybox is a cube with 6 faces:
   - Up (top)
   - Down (bottom)
   - Left
   - Right
   - Front
   - Back

Each face gets its own image.

⸻

🖼️ Step 2: Create or Find the 6 Images

You can:
   - Make your own in Photoshop, GIMP, or Blender
   - Use a 3D rendering tool (like Unity, Blender, or Skybox AI generators)
   - Or grab a free one from Poly Haven, AmbientCG, or similar

Make sure each image is:
   - Square (512x512 or 1024x1024)
   - Labeled correctly so they match the cube face (see below)

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

⸻

🔁 Step 4: Replace Roblox Files

You can use [this](https://github.com/eman225511/CustomDebloatedBloxLauncher) tool for that 
by placing all the .tex files into a folder you can also include a .PNG for a preview 
then in the app select custom skybox folder then apply
