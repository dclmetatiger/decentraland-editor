textures/dcl/base
{
	cull disable
	nomipmaps
	nopicmip
	surfaceparm alphashadow
	surfaceparm nonsolid
	surfaceparm detail
	surfaceparm trans	
}

textures/dcl/_collider
{
	q3map_baseshader textures/dcl/base
	qer_editorimage textures/dcl/_collider
	qer_trans .75	
}