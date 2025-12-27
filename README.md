# Decentraland Editor
by METATIGER, December 27 2025

If you're looking for a complete Release, precompiled with all binaries and files for Windows, go to the Release page here: https://github.com/dclmetatiger/decentraland-editor/releases/tag/decentraland


# GENERAL INFORMATION

This tool is a map/model editor for the Decentraland Creator Hub. It allows
you to create simple or complex textured GLB assets without having to use
Blender (however, the GLBs can still be imported and edited in Blender). It is
based on the old but reliable "GTK Radiant" map editor from id Software and
was originally developed and used to edit custom maps for games using the
Quake 3 engine like Return to Castle Wolfenstein, Call of Duty 1 or Doom 3.
A modern example is the Open Source Arena Shooter Xonotic.
You can get it here: https://xonotic.org



# WHY USE DECENTRALAND EDITOR?

The advantage is that editing buildings or architecture in general is much
easier with this kind of editor than with a pure 3D editor such as Blender.
It is easy to learn, editing is straightforward, and you don't really need to
know much about unwrapping or UV maps. In addition, the texture quality and
detail can be much higher compared to a baked texture, as you can reuse the
same texture over and over again, and even for different models, when using
the GLTF format with external textures, which also reduces the number of
texture files.

You get fast results and it also helps you to establish a simple workflow for
creating a scene or building using only textured blocks/ primitives
("brushes") and curved surfaces ("patches"), add custom GLTF models to the
scene, and compile everything into a single GLB or GLTF file that can then be
imported directly into Decentraland's Creator Hub tool.



# WORKFLOW (automated)

Open or create a map with the Decentraland Editor.
Click "Build > Export to GLB (High Quality)"

1. compiles the map file to BSP Format using q3map2.exe
2. converts the BSP to Wavefront OBJ Format using q3map2.exe
3. Python script: fixes MTL texture paths
4. Python script: scales the OBJ to Decentraland dimensions
5. Python script: converts the OBJ to GLB Format
6. Python script: compresses the GLB (set max. texture size / JPEG, PNG only)
7. cleanup temporary files: delete OBJ+BSP files and BSP compilation stuff
8. Preview compiled GLB in separate GLB Viewer application
9. Optional: convert the GLB to GLTF (single binary, separate textures files)



# COMPILE INSTRUCTIONS

The Editor has been precompiled for Windows and works "out of the box" and
also comes with a lot of preset assets in MAP format and also many GLTF models
for imports. However if you want to adjust or extend the tool for your own
needs, you can always compile it yourself.

Check the file "Compile Instructions" in the "source" subfolder how to do
this. It also contains information how to compile the separate "GLBviewer"
tool I've written in the BlitzmaxNG language which provides a basic GLB viewer
which is called at the end of the compilation process of a map.

As a base for this Editor, a fork of GTK Radiant called "NETradiant" has been
used. Basically it is the same Editor like NETradiant, but has been adjusted
to make it work with Decentraland's Creator Hub. You can find a ZIP with the
complete source in the "source" subfolder, or download the latest version here
from Github: https://github.com/Garux/netradiant-custom/



# ADDITIONAL NOTICES

How to install:
- Decentraland Editor runs "out of the box", it's just a ZIP with no installer
- we recommend to unzip it to C:\ root folder, like C:\DecentralandEditor
- but it may also work from different locations (it's portable)

Windows Warning:
- you may see a "Windows protected your PC" message running the executable
- this means it has no official signature by Windows
- that's why it treated suspicious in general
- to make it work you must allow the use of the software once

For paranoid and/or safety-conscious users:
- we assure that this tool does NOT contain a virus or backdoor
- its just the compiled source and we're no "official" publisher
- if you are unsure you can upload the ZIP or the executables/DLLs inside
- you can use a Virus scan page like https://virustotal.com for that

For developers:
- you can always compile the source by yourself
- you can also exchange the provided executables/DLLs with your own ones
- it uses an embedded Python 3.x for extra scripts, no need to install Python

Quake 3 related:
- many features of the Quake3 Engine are NOT supported
- it's just about to create 3D architectural geometry
- it has been fully adjusted to be compatible to Decentraland
- you can still use custom shader files to manipulate the level geometry
- see q3map2 documentation: https://q3map2.robotrenegade.com/
- BSP creates the level geometry, we usually don't need more than this for DCL
- VIS calculates the visibility of BSP nodes, this is NOT needed for DCL!
- Light creates a Lightmap based on BSP and VIS stages
- skylights and custom lights can be used to illuminate a map

Quake 3 Lightmaps:
- Decentraland Editor is also a full lightmapper, but it's currently not used
- an additional external Lightmap can be created (not supported in DCL)
- additional Lightmaps usually use the 2nd UVset of an object
- first UV map always contains the DIFFUSE texture mapping layout
- second UV map contains LIGHT texture mapping layout
- the exported GLBs currently do NOT contain this 2nd UVset
- only the BSP file does (but gets deleted in the compile process later)
- there is an Blender Addon to import BSP in Blender:
  https://github.com/SomaZ/Blender_BSP_Importer
- if you want to use the BSPs uncomment "Cleanup" section in build_menu.xml
- also uncomment the Lightmap section there



# IMPORTANT FOLDERS AND FILES

- dcl.game contains all custom map data and objects
- there are also Python files to control transparency, emission and PBR
- you can control this per surface/material there
- gamepacks contains the dcl.game information, needed for this custom build
- gamepacks/dcl.game/dcl/entities.ent contains the Quake 3 Editor Entity
  definition file (like info_player_start), stripped down for DCL
- logs contains the output of the build debuglogs, when you compile a map
- python contains the complete embedded Python to make the scripts work
- scripts contains all the custom Python scripts needed to compile the GLB
- settings makes Radiant work "portable" and contains all custom settings
- settings/1.6.0/radiant.log contains the debuglog of the Radiant Editor
- settings/1.6.0/qe3bsp.bat contains the last batch call
- settings/1.6.0/dcl.game/build_menu.xml contains the Build Menu command sets
- source contains the NETradiant+GLBviewer sources used for this Editor build
- themes/_colors contains Blueprint.json color scheme used in this Editor



# MY FIRST MAP FILE / GLB MODEL

Now we want to create our first GLB model, but how? First, it is crucial to
know the prerequisites EVERY map needs or it won't work:

- make sure there is a "worldspawn" entity in the map
- make sure there is a "info_player_start" entity in the map
- have at least one surface painted with a texture (caulk is NOT a texture!)

You can create these simply drawing a caulked brush block in the top/side view
windows with the left Mouse Button and drag the mouse a little bit and use the
right Mouse Button to open the context Menu and add "Info > info_player_start"
somewhere. You can then mark the worldspawn brush with the left Mouse Button
(turns green) and paint this brush by pressing "T" to open the Texture editor
and select a texture from there. That's it.

There is a "empty.map" located in the dcl.game/maps folder which is prepared
like that. You can then click "Build > Export to OBJ and GLB (High Quality)"
to export the map / create the GLB.

The final GLB can be found at dcl.game\maps\[mapname].glb - also the
uncompressed variant of it is there, too, just in case you want or need to
recompress the GLB again but won't recompile again.



# WHAT IS CAULK?

Caulk is simply a surface which is NEVER compiled into the final map, usually
the backside of a brush. Usually you paint all surfaces with the caulk
"texture" (which is not a texture at all but used like a texture) which shall
not be visible at all. This can be a surface hidden inside other objects,
adjacent wall parts, corners, the bottom of a floor which is usually invisible
or the backside of a transparent texture for example.

If you want to save a lot of time simply paint whole brushes with the Texture
you want and later use the great "Autocaulk" feature from the Brush Menu, or
press F4 to activate it. This feature identifies all invisible polygons of the
current selected objects and auto caulks them. It works great, so use it!



# WHAT ARE COLLIDERS?

Decentraland can use objects/surfaces with the name "_collider" in it as
ingame colliders. In Decentraland Editor, there is a special Texture called
"dcl/_collider", a green semitransparent surface. Using this, you can for
example build "smooth stairs" or "smooth corners" around difficult objects or
if stair steps are too high forcing the avatar to "jump" to the next step. But
if you simply place a slanted brush or patch over all the steps, as if you
were pouring them into glass the collider is used instead of the stair and the
avatar literally "glides" up the steps instead of getting stuck.

They can also be useful if you don't use the Decentraland Creator Hub
"Physics" feature, where the whole object becomes a collider itself, but this
can double the polygon amount, making the scene slower = less FPS. You can
instead "simplify" the collision by drawing a much simpler geometry with the
collider Texture around walls or roofs, i.e. areas that should collide with
the Avatar.

This usually saves a lot of Tris and allows you to control exactly what
collides. For examples areas the avatar can't reach usually do not need a
collision surface. You can also use it to add invisible platforms, e.g. for
a parkour or to make it easier for Avatars to jump on a high object or you can
also use them to prevent the avatar walk into areas he should not go :)



# HOW TO USE DECENTRALAND EDITOR GUI

Basic Usage of the Editor GUI:

General:

- Top Left is the 3D Preview Window
- click once with the right Mouse Button and use WASD to move the camere there
- in the other Windows click and hold the right Mouse Button to drag the map
- use the Mousewheel to Zoom
- use Key 0-9 to change the grid resolution
- Entities get snapped according to this grid size


Entities:

- if you click an Entity you can use these Keyboard Shortcuts:
  - "W" shows the XYZ Axis to drag and move an Entity around
  - "R" shows the rotation Angles to rotate an Entity
  - hold SHIFT to use fixed steps
- it is crucial to understand the difference between Brushes and Patches
- Brushes are like LEGO bricks, always cuboid, solid and can also be cutted
  into smaller pieces or joined if the connection surfaces match
- Patches are irregular shapes like Planes, Cylinders or Spheres
  they keep their shape but can also be subdivided into more detailed surfaces
- Patches also give smooth transitions on rounded shapes
- Rule of thumb: if it can't be built with Brushes, use Patches instead :)
- both get converted into level geometry on export, where Patches will get
  subdivided by a given factor which can increase the Tris!
- it is a good idea to organize subobjects into "func_groups"
  - select more than one object by holding SHIFT, left click the Object
  - right click and select "func_group"
  - the new object will turn into a blue color
  - you can still select single objects or create new func_groups from these
  - to select ALL objects of a func_group click one + "SHIFT E" / "CTRL E"
- unfortunately, Models can't be part of a func_group, keep that in mind!
- you can hide objects with "H" and show all objects again with "SHIFT H"
- you can select such a func_group and use "File > Save selected to export
  it as a so-called "prefab" - you can also use this to save separate props or
  you can also save different areas to can edit one by one and later join
- you can later import this prefab into other projects to reuse it again

  
Surfaces and Textures:

- press "S" to open the surface inspector, here you can manipulate the UVs
  and the assigned texture
- Textures can also be assigned pressing "T" to enter the Texture window
- there is a nice function to "copy" the UV properties between surfaces
  - first paint the "source" surface and scale the UV like you want
  - then - only a single source surface should be selected - click the
    MIDDLE Mouse Button once (no notice!)
  - second hold CTRL and click the target surface with the MIDDLE Mouse button
  - as a result the source surface including all UV parameters should be
    copied to the target surface
  - but keep in mind that it does not copy the UVs 1:1 - it usually sets the
    UVs according to their position in 3D space, like you extend a brick wall
  - with this technique you can paint even complex objects very easy without
    doing much UV work

  
External Models:

- you can import external GLTF models to add more detail to the level geometry
- to add a custom model RIGHT click for the Context Menu > misc_model
- there are many examples in the "models" subfolder
- these models will also be rendered into the final map on export as geometry
- you can scale and rotate them pressing the "N" key while selected
- for a general scale use "modelscale" or "modelscale_vec" for separate axis
- same for rotation angle (angle vs. angles)
- but you can also use the regular scale/rotate buttons like with the
  brushes/patches on them


Understand Caulking:

- Surfaces painted with the "CAULK" texture are NEVER exported!
- always paint ALL faces who are NOT visible with the CAULK texture to save
  unneeded draw calls on the object!
- it is also a good idea to create new Brushes with the CAULK texture only
- and then paint only the faces with different textures you want to see
- but you can also rely on the Autocaulk feature of the Editor if you want


Brushes Manipulation:

- a new brush can be created by just click and drag the left Mouse Button
- clicking a brush always select the whole brush
- to select a single Face hold CTRL+click the face with the right Mouse Button
- only a single face can be select at once
- to manipulate the Edges/Vertices of a Brush select it and press "E" or "V"
- Edges/Vertices can be dragged with the mouse or the "W" XYZ axis tool
- you can cut/split brushes selecting and pressing "X"
  - first you left click somewhere as a cutting start point (shown as "1")
  - second you left click somewhere as a cutting end point (shown as "2")
  - a line will be shown across the brush to show the cut
  - then either press Enter to cut out the part from the brush or SHIFT+Enter
    to split the Brush into two parts
  - or you can always leave the cut mode again by pressing "X" again
- you can always use the "W" key to show the axis symbol if you want to move
  Vertices more precise
- if your Vertices are not inside the current matrix anymore you can press
  CTRL-G - this will snap these to the CURRENT grid step size (but can also
  break your geometry so be careful and don't use a big step size here)
  

Patches Manipulation:
  
- a new patch can be created from the "Curve" Menu
- with Patches you can create rounded objects like arches, gates and so on
- a Patch consists of Rows and Columns
- select a Patch+press "V" to see the Vertices and Control Points of these
- for example of you create a simple 3x3 Patch and drag the center vertex
  upwards it will create a soft bulge, controlled by the control points
- Patches are always one-sided and NEVER have a backside
- to make them solid use the additional "Cap Selection" features or the
  Thicken tool
- to "flip the normals" you can use "Curve > Matrix > Invert"



# ADVANCED FEATURES

With the Decentraland Editor you can also set specific parameters for surfaces
like Transparency, Emission or PBR (Metallic / Roughness). There are three
important files in the dcl.game folder to control these:

- materials_alpha.py
- materials_emission.py
- materials_surface.py

They contain basically a simple Python array of keys and values - separated by
commas. Make sure that the LAST key/value pair NEVER has a comma at the end of
the line, or the Array becomes invalid and the compilation will run into an
error! Before you change something, check the provided files or make a backup
to go back at any time.

General:
The "key" is always the Texture filename without extension and without
"textures/" prefix. It must match the exact texture name like you can read it
in plain text in the MAP file itself.

materials_alpha.py
This should only contain Textures who really have an alpha channel, usually
transparent PNGs or 32bit TGAs. The value is simply the Alpha value for the
Decentraland Editor itself, NOT the exported GLB which always uses the
transparency value of the source Texture, this is important to know! 0.0 means
it is invisible and 1.0 is fully using the transparency value from the source
Texture. So a Fence for example should have 1.0 while semi-transparent Water
or the collider may need a 0.5 value. Experiment which fits best.

materials_emission
This should only contain Textures who are glowing in the dark, like a lantern
glass or a lit window. It will connect the Texture with the Emission node and
set the Emission value. This is usually a number between 0.0 (not glowing)
and 1.0 (full glow) but can also be much higher than 1.0 if you want more
glow / bloom ingame.

materials_surface
This sould only contain Textures who need more "shine" and "reflection" like
metal or marble. Usually, for ALL surfaces in the GLB default PBR values of
0.0 for metallic and 1.0 for roughness are set. In this file you can exclude
specific surfaces to have a different PBR value, and these are always two
parameters in the Value array (X,Y) where X is metallic and Y is roughness in
a value between 0.0 and 1.0. Experiment which fits best.



# ADDING OWN TEXTURES

Adding own textures is easy, but can be challenging too if the Textures need
to be different, like they have Transparence or Emission. Usually, you simply
create a subfolder at "textures/" and copy the custom Textures there. Only use
JPEG, PNG and TGA. PNGs and TGAs can have an alpha channel for transparency.
It's a good idea to copy transparent PNGs direct to the existing "alpha"
channel as it is already included in the materials_alpha.py - otherwise you
must add your texture there manually to make it work ingame as a transparent
Texture.

If you want to add your transparent Texture to the Decentraland Editor and
make it also transparent there it's a little bit more complex. You must edit
a "shader" file. All shader files are listed in the "shaderlist.txt", and both
can be found in the dcl.game/scripts folder. Best practice is to study the
existing files there and copy'n'paste an existing shader to your own file
(don't forget to add it to the shaderlist.txt, too) and simply edit the file
and path names.

It is important to know that "sub-sub-folders" DON'T WORK. For example, the
frankfurt texture folders have been separated into several frankfurt_XXX
folders. That is the deepest level the Editor will parse, an additional
subfolder below such a folder gets ignored! Keep that in mind.

It is in general a BAD idea to exchange a texture which has already been used
on surfaces where the UVs are finally aligned with a variant with a different
resolution (higher/lower), for example you've built the map with a 512x512
texture and now to exchange it with a higher 1024x1024 variant. This will
BREAK your UV layout and you must rearrange the UVs of the affected surfaces.
There is no way to "convert" these yet. Keep that in mind.



# ADDING OWN MODELS

A great feature is to place separate models in the map and render everything
into a single GLB file. This is useful if you have a lot of static objects and
won't like to place them in the Decentraland Creator Hub manually. But you
must prepare these models a little bit before you can use them with the Editor

Take a look at the models/mapobjects folder. Unlike textures, these may
contain further subfolders. However, it is important that the Textures of the
GLTF models are always located in the same folder as the GLTFs, otherwise the
Textures will not be displayed correctly in the editor!

The GLTFs there have been exported with Blender using the
"glTF Separate (.gltf + bin + textures)" Export option and usually only
contain the model and a single Basecolor texture. Just make suree that there
is no Texture subfolder defined on export (which is default). Unfortunately,
Normalmaps or PBR textures are NOT supported by the Editor, but you can add
these later to the exported Model in Blender if needed. As they will share the
same UVs like the Basecolor Texture and all Surfaces are separated into single
Mesh objects sharing the same Texture, this is not a problem.

If the exported GLTF does not appear at all, or only with a red texture you
should check the GLTF file in a Text Editor, and check the paths and
filenames. If the Model appears too small in the Editor you must scale it up
using the "N" key and edit the scale properties. You can also scale it up
before exporting it in Blender, usually a 1.0 size objects must be scaled by
factor 64 to get a good world scale.



# WORLD DIMENSIONS

Decentraland Editor was/is an Editor for Quake 3 maps. Unfortunately we can't
change the unit scale in the Editor which is still matching the Quake 3 world
dimension scale. But how big is such a unit in real life? The short answer is:
we don't know exactly, it depends on you.

In Quake 3, 64 world units are about 1.7 Meters. As it is easier to calculate
in the Editor in 2^X values I've defined a Decentraland 1x1 Parcel to a size
of 1024x1024 Editor Units. In Decentraland this 1x1 Parcel has a size of about
16x16 Meters. 64 Editor units is 1 Meter or 1 Unit is 64/1024 = 0,015625 Meter

So the Avatar has a height of 122 Units or 122 x 100 x 0,015625 = 1,90 Meters.
But you can always shrink it a little bit if you want different dimensions
just to give you an idea about the dimensions here.

Helpers:

You can always enable a parcel overlay in the "View > Show > Show Blocks"
which enables an orange overlay showing you a grid of 1x1 parcels in the map.
Keep in mind that these Blocks start at 0,0,0.

There is also a "male_world.gltf" model located in the mapobjects/dcl folder,
which is a model of a common DCL male avatar and gives you an idea how big a
door, a building or custom objects must be scaled to get the correct size
relation to the ingame avatars. So use this model and move it in your scene
to check if the size is still matching the avatar's size to avoid extra work.

I recommend to use it until you have a feeling about the sizes. A rule of
thumb is to use a door height of 128 Units usually fits well, and a step riser
should be about 8 to 16 Units.