textures/frankfurt_alpha/base
{
	cull disable
	nomipmaps
	nopicmip
	surfaceparm alphashadow
	surfaceparm trans
}

textures/frankfurt_alpha/nikolaiwindow
{
	q3map_baseshader textures/frankfurt_alpha/base
	qer_editorimage textures/frankfurt_alpha/nikolaiwindow.tga
	qer_trans 1.0
	implicitMask -
}

textures/frankfurt_alpha/curtain
{
	q3map_baseshader textures/frankfurt_alpha/base
	qer_editorimage textures/frankfurt_alpha/curtain.tga
	qer_trans 1.0
	implicitMask -
}

textures/frankfurt_alpha/roemer_clock
{
	q3map_baseshader textures/frankfurt_alpha/base
	qer_editorimage textures/frankfurt_alpha/roemer_clock.tga
	qer_trans 1.0
	implicitMask -
}

textures/frankfurt_alpha/sandrose
{
	q3map_baseshader textures/frankfurt_alpha/base
	qer_editorimage textures/frankfurt_alpha/sandrose.tga
	qer_trans 1.0
	implicitMask -
}

textures/frankfurt_alpha/sandstone_arch_gothic
{
	q3map_baseshader textures/frankfurt_alpha/base
	qer_editorimage textures/frankfurt_alpha/sandstone_arch_gothic.tga
	qer_trans 1.0
	implicitMask -
}

models/mapobjects/frankfurt/tree/leaves1
{
	q3map_baseshader textures/models/base
	qer_editorimage models/mapobjects/frankfurt/tree/leaves1.tga
	qer_trans 1.0
	qer_alphafunc greater 0.5
	cull twosided
	implicitMask -
}