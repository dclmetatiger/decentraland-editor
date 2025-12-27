SuperStrict

Framework openb3d.B3dglgraphics
Import "cgltf/cgltf_wrapper.c"

Extern "C"

	Function glb_load:Byte Ptr(path:Byte Ptr)
	
	Function glb_get_primitive_count:Int(h:Byte Ptr)
	Function glb_get_vertex_count:Int(h:Byte Ptr, primIndex:Int)
	Function glb_get_index_count:Int(h:Byte Ptr, primIndex:Int)
	
	Function glb_get_positions:Float Ptr(h:Byte Ptr, primIndex:Int)
	Function glb_get_normals:Float Ptr(h:Byte Ptr, primIndex:Int)
	Function glb_get_texcoords0:Float Ptr(h:Byte Ptr, primIndex:Int)
	Function glb_get_indices:Int Ptr(h:Byte Ptr, primIndex:Int)
	
	Function glb_get_basecolor_path:Byte Ptr(h:Byte Ptr, primIndex:Int)
	Function glb_get_basecolor_data:Byte Ptr(h:Byte Ptr, primIndex:Int, sizeVar:Size_T Ptr)
	Function glb_get_basecolor_factor:Float Ptr(h:Byte Ptr, primIndex:Int)
	
	Function glb_set_mirror_x(enable:Int)
	Function glb_normalize_unitcube(h:Byte Ptr)
	
	Function glb_set_generate_normals(enable:Int)
	Function glb_set_default_color(r:Float, g:Float, b:Float, a:Float)
	Function glb_set_force_default_color(enable:Int)
	Function glb_get_has_alpha:Int(h:Byte Ptr, primIndex:Int)
	
	Function glb_free(h:Byte Ptr)

End Extern

AppTitle="Decentraland Editor - GLB Viewer by METATIGER"

Global datapath:String="/dcl.game/maps/"
Global position:String[]=["Front","Back","Left","Right","Top","Bottom"]
Global pospitch:Float[]=[0.0,0.0,0.0,0.0,90.0,-90.0]
Global posyaw:Float[]=[0.0,180.0,90.0,-90.0,0.0,0.0]

Global RADIANT:Int=0

Global args:String
If AppArgs.Length > 1 Then args = AppArgs[1]

' accept BSP extension as a GLB input, too (Radiant build_menu.xml fix), also rotate by 180°
If Instr(args,".bsp") Then RADIANT=1
args=args.Replace(".bsp",".glb")

' Mesh Splitting
Const MAX_SURF_VERTS:Int = 65536
Const VERTMAP_UNSET:Int = -1

' Initial Screenshot size
Global SCREENSHOT_SIZE:Int = 4096
Global MINMAX:Int

' Flags
Global WF:Int=0   ' Wireframe
Global AT:Int=0   ' Autorotation
Global IN:Int=1   ' Infos
Global PS:Int=0   ' Front

' help variables
Global verts:Int,tris:Int,surfs:Int,meshes:Int,textures:Int
Global tverts:String,ttris:String,tsurfs:String,tmeshes:String,ttextures:String
Global MX:Int=0
Global MY:Int=0
Global ZS:Float
Global pitch:Float
Global yaw:Float=180.0
If RADIANT Then yaw=0.0


' ----------------------------------------------------------------------------
' The fun starts here
' ----------------------------------------------------------------------------
Graphics3D 1920, 1080, 0, 2,DesktopHertz()

GetScreenshotSize()

' Pivots
Global campivot:TPivot = CreatePivot()
Global meshpivot:TPivot = CreatePivot(campivot)
PositionEntity meshpivot, 0, 0, 2

' Cameras
Global cam:TCamera = CreateCamera()
CameraClsColor cam, 32,32,32
CameraRange cam, 0.1, MINMAX
PointEntity cam, meshpivot
'PositionEntity cam,0,-0.06125,0
PositionEntity cam,0,0,0

' Wireframe Textures
Global wiretex:TTexture = CreateWireframeTexture()
Global dummytex:TTexture = CreateTexture(32,32,1)
TextureBlend wiretex,1

' Faint background glow
Global sprite:TSprite=CreateSprite(cam)
PositionEntity sprite,0,0,MINMAX
ScaleSprite sprite,MINMAX/2,MINMAX/2.0
Global spritetex:TTexture=CreateBackgroundTexture()
EntityTexture sprite,spritetex
EntityBlend sprite,3
EntityFX sprite,1
EntityAlpha sprite,0.25
EntityColor sprite,100,150,255

' Light
AmbientLight 128,128,128
Global light:TLight = CreateLight(1)
RotateEntity light,45,45,45
LightColor light,255,255,255

' Model
Global ent:TEntity
Global demomesh:String

Load()
Main()



' ----------------------------------------------------------------------------
' Main Loop
' ----------------------------------------------------------------------------
Function Main()

	While Not KeyHit(KEY_ESCAPE)
	
		' Mousespeed
		MX:+MouseXSpeed()
		MY:+MouseYSpeed()
		
		' Axis-independent rotation of the Mesh object
		RotateEntity meshpivot, ((1.0 - MY * 2.0 / GraphicsHeight()) * 180)-pitch, 0, 0
		RotateEntity ent, 0, ((MX * 1.0 / GraphicsWidth() * 2.0) * 180) + yaw + 180, 0
		
		' Scroll-Zoom
		ZS :- MouseZSpeed()
		If ZS < 0.1 Then ZS = 0.1
		If ZS > 10 Then ZS = 10
		CameraZoom cam, 10.0/ZS
		
		' LMB = Reload, RMB = Change View
		If MouseHit(1) Then Load()
		If MouseHit(2) Then PS:+1 ; PS=PS Mod 6 ; AT=0 ; ResetMouse() ; pitch=pospitch[PS] ; yaw = posyaw[PS]

		' Information
		If KeyHit(KEY_I) Then IN=1-IN

		' Wireframe Mode
		If KeyHit(KEY_TAB) Then WF=1-WF ; Repaint(ent)

		' ENTER = Save Screenshot / Preview
		If KeyHit(KEY_ENTER) Then Screenshot()

		' Autorotation
		If KeyHit(KEY_SPACE) Then AT=1-AT
		If AT Then MX:+1
				
		' Wireframe Blueprint Mode
		If WF Then
		
			HideEntity sprite
			CameraClsColor cam, 20,40,60
			glPolygonMode(GL_FRONT, GL_LINE)		' alternative: GL_FRONT_AND_BACK
			glLineWidth(0.75)
			
		Else
		
			ShowEntity sprite
			CameraClsColor cam, 32,32,32
			glPolygonMode(GL_FRONT, GL_FILL)		' alternative: GL_FRONT_AND_BACK
						
		EndIf
		
		' Render
		RenderWorld
		
		' 2D stuff
		If IN Then
		
			BeginMax2D()
			
				SetColor 255,255,255
				SetBlend ALPHABLEND
			
				DrawText "Triangles.: "+tris,0,0
				DrawText "Vertices..: "+verts,0,15
				DrawText "Surfaces..: "+surfs,0,30
				DrawText "Meshes....: "+meshes,0,45
				DrawText "Textures..: "+textures,0,60
				DrawText "View......: "+position[PS],0,75
				
				DrawText "Left MB...: Load",0,100
				DrawText "Right MB..: Change View",0,115
				DrawText "I.........: Hide Infos",0,130
				DrawText "TAB.......: Wireframe",0,145
				DrawText "ENTER.....: Screenshot",0,160
				DrawText "SPACE.....: Autorotation",0,175
				DrawText "ESC.......: Exit",0,190
			
			EndMax2D()
			
		EndIf
		
		Flip

	Wend
	
End Function



' ----------------------------------------------------------------------------
' Repaints the Mesh in Wireframe mode, called only once when switching mode
' ----------------------------------------------------------------------------
Function Repaint(ent:TEntity=Null)

	If WF Then
	
		For Local i:Int = 1 To CountChildren(ent)

			Local e:TEntity=GetChild(ent,i)
			
			For Local j:Int=1 To CountSurfaces(TMesh(e))
			
				Local s:TSurface=GetSurface(TMesh(e),j)
				Local b:TBrush=GetSurfaceBrush(s)
				Local t:TTexture=GetBrushTexture(b,0)
				
				If TTexture(t) Then BrushTexture b,t,0,0 ; BrushTexture b,wiretex,0,1
				If TSurface(s) Then PaintSurface(s,b)

			Next

			'EntityFX e,1+
			EntityAlpha e,0.125
			EntityBlend e,3
			
		Next
		
	Else
	
		For Local i:Int = 1 To CountChildren(ent)

			Local e:TEntity=GetChild(ent,i)

			For Local j:Int=1 To CountSurfaces(TMesh(e))

				Local s:TSurface=GetSurface(TMesh(e),j)
				Local b:TBrush=GetSurfaceBrush(s)
				Local t:TTexture=GetBrushTexture(b,0)
				
				If TTexture(t) Then BrushTexture b,t,0,0 ; BrushTexture b,dummytex,0,1
				If TSurface(s) Then PaintSurface(s,b)
				
			Next

			'EntityFX e,1+2+16+32
			EntityAlpha e,1
			EntityBlend e,1
			
		Next
		
	EndIf

End Function


Function ResetMouse()

	MouseXSpeed()
	MouseYSpeed()
	MouseXSpeed()
	MouseYSpeed()

	MoveMouse GraphicsWidth()/2,GraphicsHeight()/2

End Function


' ----------------------------------------------------------------------------
' Simple square screenshot
' ----------------------------------------------------------------------------
Function Screenshot()

	' position screenshot
	Local sx:Int=GraphicsWidth()/2-(SCREENSHOT_SIZE/2)
	Local sy:Int=GraphicsHeight()/2-(SCREENSHOT_SIZE/2)
	
	' grab
	Local pixmap:TPixmap=GrabPixmap(sx,sy,SCREENSHOT_SIZE,SCREENSHOT_SIZE)
	
	' draw
	BeginMax2D()
	
		SetColor 255,0,255
		SetAlpha(0.5)
		SetBlend ALPHABLEND
		DrawRect sx,sy,SCREENSHOT_SIZE,SCREENSHOT_SIZE
		SetBlend SOLIDBLEND
		SetColor 255,255,255
		
		Flip
		
	EndMax2D()

	' save PNG with the same filename prefix like the GLB
	SavePixmapPNG(pixmap,ExtractDir(demomesh)+"/"+StripAll(demomesh)+".png",9)

End Function



' ----------------------------------------------------------------------------
' Find out maximum Screenshot size (min Graphics height or width)
' ----------------------------------------------------------------------------
Function GetScreenshotSize()

	' find out the max resolution of a screenshot
	If GraphicsWidth()>GraphicsHeight() Then minmax=GraphicsHeight() Else minmax = GraphicsWidth()

	If SCREENSHOT_SIZE > minmax Then

		Repeat
		
			SCREENSHOT_SIZE:/2
		
		Until SCREENSHOT_SIZE < minmax
		
	EndIf

End Function



' ----------------------------------------------------------------------------
' Load a new GLB Mesh
' ----------------------------------------------------------------------------
Function Load()

	tris=0
	verts=0
	surfs=0
	meshes=0
	textures=0
	ZS=6.0
	WF=0
		
	If TEntity(ent) Then FreeEntity ent
	
	' current dir logic
	Local dir:String
	If CurrentDir()<>AppDir+datapath Then dir=CurrentDir()
	If CurrentDir()=AppDir Then dir=datapath
	
	' user request to open a GLB file
	If args And RADIANT Then
	
		demomesh=args Else demomesh=RequestFile("Select a GLB Model", "GLTF Models:glb,gltf;All Files:*", Null,dir)
		
	EndIf
	
	args=""
	
	' load it
	ent=LoadMeshGLB(demomesh, meshpivot, True)
	
	If ent = Null Then 
		
		'Local msg:Int=Notify(demomesh + "GLB could not be loaded.")
		End
		'If msg Then Load() Else End
		
	EndIf
			
	CenterMesh(ent)
	Repaint(ent)
			
	MoveMouse GraphicsWidth()/2,GraphicsHeight()/2
	ShowMouse()
	
End Function



' ----------------------------------------------------------------------------
' Loads a GLB Mesh – with Surface-Splitting
' ----------------------------------------------------------------------------
Function LoadMeshGLB:TEntity(file:String, parent:TEntity = Null, flipV:Int = True, mirrorLocalX:Int = False)
	
	Local alpha:Int=1

	glb_set_mirror_x(True)
	glb_set_generate_normals(True)
	glb_set_default_color(1.0, 1.0, 1.0, 1.0)
	glb_set_force_default_color(True)
	
	If (Not FileType(file)) Then Return Null

	Local h:Byte Ptr = glb_load(file)
	If h = Null Then Return Null

	Local primCount:Int = glb_get_primitive_count(h)
	If primCount <= 0 Then glb_free h ; Notify "No valid primitives found in GLB" ; Return Null

	Local mesh:TMesh = CreateMesh(parent)
	
	meshes:+1
	
	Local dir:String = ExtractDir(file)

	glb_normalize_unitcube(h)

	For Local p:Int = 0 Until primCount
	
		Local vcount:Int = glb_get_vertex_count(h, p)
		Local icount:Int = glb_get_index_count(h, p)
		If vcount <= 0 Or icount <= 0 Then Continue

		Local pos:Float Ptr = glb_get_positions(h, p)
		Local nrm:Float Ptr = glb_get_normals(h, p)
		Local uv0:Float Ptr = glb_get_texcoords0(h, p)
		Local idx:Int Ptr = glb_get_indices(h, p)

		Local colorFac:Float Ptr = glb_get_basecolor_factor(h,p)

		Local brush:TBrush = CreateBrush()

		If colorFac <> Null Then

			BrushColor brush, colorFac[0]*255, colorFac[1]*255, colorFac[2]*255
			BrushAlpha brush, colorFac[3]

		EndIf

		Local sizeVar:Size_T
		Local dataPtr:Byte Ptr = glb_get_basecolor_data(h,p, Varptr sizeVar)
		Local tex:TTexture
		
		alpha=1
		If glb_get_has_alpha(h, p) Then alpha=2
		
		If dataPtr <> Null And sizeVar>0 Then
		
			Local tmpname:String = "glbtex_" + MilliSecs() + ".png"
			Local out:TStream = WriteStream(tmpname)
			
			If out Then
			
				For Local ii:Size_T = 0 Until sizeVar
				
					WriteByte(out, dataPtr[ii])
					
				Next
				
				CloseStream out
				tex = LoadTexture(tmpname,alpha)
				textures:+1
				
				DeleteFile tmpname
				
			EndIf
			
		Else
		
			Local colpath:Byte Ptr = glb_get_basecolor_path(h,p)
			
			If colpath <> Null Then
			
				Local path:String = String.FromCString(colpath)
				Local texpath:String = dir + "/" + path
				
				Print texpath
				
				If FileType(texpath)=1 Then tex = LoadTexture(texpath,alpha)
				
			EndIf
			
		EndIf
		
		If tex Then BrushTexture brush, tex,0,0

		If glb_get_has_alpha(h, p) Then BrushFX brush, 2+16+32

		Local surfMesh:TMesh = CreateMesh(mesh)
		Local surf:TSurface = CreateSurface(surfMesh)
		PaintSurface surf, brush

		meshes:+1
		surfs:+1

		Local vertexMap:Int[] = New Int[vcount]
		
		For Local i:Int = 0 Until vcount
		
			vertexMap[i] = -1
			
		Next

		Local surfVertCount:Int = 0

		For Local i:Int = 0 Until icount Step 3

			If surfVertCount > MAX_SURF_VERTS - 3 Then
			
				surf = CreateSurface(surfMesh)
				PaintSurface surf, brush
				surfVertCount = 0
				surfs:+1
				
				For Local j:Int = 0 Until vcount
				
					vertexMap[j] = -1
					
				Next
				
			EndIf

			Local tri:Int[3]

			For Local j:Int = 0 To 2
			
				Local src:Int = idx[i+j]
				Local dst:Int = vertexMap[src]

				If dst = -1 Then
				
					Local px:Float = pos[src*3+0]
					Local py:Float = pos[src*3+1]
					Local pz:Float = pos[src*3+2]

					Local u:Float = 0.0
					Local v:Float = 0.0
					
					If uv0 <> Null Then
					
						u = uv0[src*2+0]
						v = uv0[src*2+1]
						If Not flipV Then v = 1.0 - v
						
					EndIf

					dst = AddVertex(surf, px, py, pz, u, v)
					
					verts:+1
					
					If nrm <> Null Then VertexNormal surf, dst, nrm[src*3+0], nrm[src*3+1], nrm[src*3+2]
					
					vertexMap[src] = dst
					surfVertCount:+1
					
				EndIf

				tri[j] = dst
				
			Next

			AddTriangle surf, tri[0], tri[1], tri[2]
			
			tris:+1
			
		Next
				
	Next
		
	glb_free h
	
	Return mesh
	
End Function



' ----------------------------------------------------------------------------
' normalize a value from a given range to a given range
' ----------------------------------------------------------------------------
Function Normalize:Float(v:Float, vmin:Float, vmax:Float, nmin:Float, nmax:Float)

	Return ((v - vmin) / (vmax - vmin)) * (nmax - nmin) + nmin

End Function



' ----------------------------------------------------------------------------
' Centers and scales the Mesh to its parent (like a pivot) = normalize
' ----------------------------------------------------------------------------
Function CenterMesh(ent:TEntity)

	Local s:Float=2^16
	
	Local vx:Float,vy:Float,vz:Float
	Local minx:Float = s, miny:Float = s, minz:Float = s
	Local maxx:Float = -s, maxy:Float = -s, maxz:Float = -s
	
	For Local i:Int = 1 To CountChildren(ent)
	
		Local mesh:TEntity=GetChild(ent,i)
		Local m:TMesh=TMesh(mesh)
		
		For Local si:Int=1 To CountSurfaces(m)
		
			Local surf:TSurface=GetSurface(m,si)
			
			For Local v:Int=0 To CountVertices(surf)-1
			
				vx=VertexX(surf,v) ; vy=VertexY(surf,v) ; vz=VertexZ(surf,v)
				
				If vx<minx Then minx=vx
				If vy<miny Then miny=vy
				If vz<minz Then minz=vz
				If vx>maxx Then maxx=vx
				If vy>maxy Then maxy=vy
				If vz>maxz Then maxz=vz
				
			Next
			
		Next
		
	Next
	
	' get max dimensions
	Local ax:Float = maxx - minx
	Local ay:Float = maxy - miny
	Local az:Float = maxz - minz
	
	Local maxDim:Float = ax
	If ay>maxDim Then maxDim=ay
	If az>maxDim Then maxDim=az
	
	If maxDim<=0 Then Return
	
	' local coords center
	Local cx:Float = (minx+maxx)*0.5
	Local cy:Float = (miny+maxy)*0.5
	Local cz:Float = (minz+maxz)*0.5
	
	' move to center
	TranslateEntity ent, -cx, -cy, -cz
	
	' normalize scale
	Local Scale:Float = 1.0 / maxDim
	ScaleEntity ent, Scale, Scale, Scale
	
End Function



Function CreateWireframeTexture:TTexture()

	Local tex:TTexture = CreateTexture(32,32,1+2)
	
	BeginMax2D()
	
		SetColor 100,200,255
		DrawRect 0,0,32,32
	
	EndMax2D()
	
	BackBufferToTex(tex,0)
	
	Return tex

End Function


' ------------------------------------------------------------------------------------------------
' Creates a Gradient Texture
' ------------------------------------------------------------------------------------------------
Function CreateBackgroundTexture:TTexture()

	Local s:Int=512
	Local v1:Float=4
	Local v2:Float=4
	
	Local pixmap:TPixmap = CreatePixmap(s, s, PF_RGBA8888)
	
	Local i:Float, j:Int, col:Int, rgb:Int
	
	For j = 0 To s/2-1
				
		For i = 0 To 360 Step 0.05
			
			col = Int(255 - Normalize(j,0,s/2-1,0,255) + Rnd(-v1,v1))
			
			col = 255 - (Normalize(j,0,s/2-1,0,255) / 255)^0.5 * 255
			
			If col > 255 Then col = 255
			If col < 0 Then col = 0
			
			Local r:Int=Int(col*1.0)
			Local g:Int=Int(col*1.0)
			Local b:Int=Int(col*1.0)
			Local a:Int=255
			
			rgb = b | (g Shl 8) | (r Shl 16) | (a Shl 24)

			Local px:Int=Int(s/2-1 + (Sin(i) * j) + Rnd(-v2,v2))
			Local py:Int=Int(s/2-1 + (Cos(i) * j) + Rnd(-v2,v2))
			
			If px>=0 And px<=s-1 And py>=0 And py<=s-1 Then WritePixel(pixmap, px, py, rgb)
			
		Next
		
	Next
	
	'SavePixmapPNG(pixmap,"gradient.png",0)
	
	Local tex:TTexture = CreateTexture(s,s,1)
	
	BeginMax2D()
	
		DrawPixmap pixmap,0,0
	
	EndMax2D()
	
	BackBufferToTex(tex,0)
	
	Return tex
	
End Function