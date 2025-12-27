textures/alpha/base
{
	cull disable
	nomipmaps
	nopicmip
	surfaceparm alphashadow
	surfaceparm trans
}

textures/alpha/fence1
{
	q3map_baseshader textures/alpha/base
	qer_editorimage textures/alpha/fence1.tga
	qer_trans 1.0
	implicitMask -
}

textures/alpha/fence2
{
	q3map_baseshader textures/alpha/base
	qer_editorimage textures/alpha/fence2.tga
	qer_trans 1.0
	implicitMask -
}

textures/alpha/gate
{
	q3map_baseshader textures/alpha/base
	qer_editorimage textures/alpha/gate.tga
	qer_trans 1.0
	
	qer_alphaFunc gequal 0.5
	qer_alphafunc greater 0.5

	cull twosided
	
	implicitMask -
}