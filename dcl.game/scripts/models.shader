textures/models/base
{
	cull disable
	nomipmaps
	nopicmip
	surfaceparm alphashadow
	surfaceparm trans
}

models/mapobjects/light/chandelier
{
	q3map_baseshader textures/models/base
	qer_editorimage models/mapobjects/light/chandelier.tga
	qer_trans 1.0
	implicitMask -
}