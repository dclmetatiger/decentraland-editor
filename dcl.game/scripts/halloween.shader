textures/halloween/base
{
	cull disable
	nomipmaps
	nopicmip
	surfaceparm alphashadow
	surfaceparm trans
}

textures/halloween/gravestone_text
{
	q3map_baseshader textures/halloween/base
	qer_editorimage textures/halloween/gravestone_text.tga
	qer_trans 1.0
	implicitMask -
}

textures/halloween/cobweb
{
	q3map_baseshader textures/halloween/base
	qer_editorimage textures/halloween/cobweb.tga
	qer_trans 1.0
	implicitMask -
}

models/mapobjects/halloween/logo_halloween
{
	qer_editorimage models/mapobjects/halloween/logo_halloween.tga
	qer_alphaFunc gequal 0.5
	
	cull disable
	nomimaps
	nopicmip
	surfaceparm alphashadow
	surfaceparm trans
		
	implicitMask -
}