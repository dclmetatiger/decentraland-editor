// cgltf_glbloader_nodes.c
// GLB-Loader für BlitzMaxNG + OpenB3D (Node- und Transform-Support)
// -> mit eingebautem X-Spiegel (Handedness-Fix) inkl. Winding-/Normal-Korrektur

#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>
#include <math.h>

#define CGLTF_IMPLEMENTATION
#include "cgltf.h"

#ifdef _WIN32
 #define API __declspec(dllexport)
#else
 #define API
#endif

/* =================== Konfiguration =================== */
static int g_mirror_x = 1; // 1 = beim Laden auf X spiegeln (empfohlen für B3D/OpenB3D)
API void glb_set_mirror_x(int enable){ g_mirror_x = enable ? 1 : 0; }

static int g_generate_normals = 1; // 0 = keine automatischen Normalen, 1 = bei fehlenden berechnen
API void glb_set_generate_normals(int enable){ g_generate_normals = enable ? 1 : 0; }

static float g_default_color[4] = {1.0f, 1.0f, 1.0f, 1.0f}; // Weiß, volle Deckkraft
static int g_use_default_color = 0; // 0 = nur verwenden wenn VertexColors fehlen, 1 = erzwingen

API void glb_set_default_color(float r, float g, float b, float a) {
    g_default_color[0] = r;
    g_default_color[1] = g;
    g_default_color[2] = b;
    g_default_color[3] = a;
}

API void glb_set_force_default_color(int enable) {
    g_use_default_color = enable ? 1 : 0;
}

/* =================== Strukturen =================== */
typedef struct {
    int vertex_count;
    int index_count;
    float* positions;
    float* normals;
    float* texcoords0;
    uint32_t* indices;

    // Material/PBR
    char* baseColorPath;
    float baseColorFactor[4];
    float metallicFactor;
    float roughnessFactor;
    unsigned char* baseColorData;
    size_t baseColorSize;
	
	char* mimeType;
	int has_alpha;
		
} Prim;

typedef struct {
    int prim_count;
    Prim* prims;
    cgltf_data* owned;
} GLBHandle;

/* =================== Utils =================== */
static char* dup_str(const char* s){
    if(!s) return NULL;
    size_t n = strlen(s);
    char* o = (char*)malloc(n+1);
    memcpy(o, s, n+1);
    return o;
}

static unsigned char* decode_base64(const char* in, size_t* outlen){
    static const unsigned char d[256] = {
        ['A']=0,['B']=1,['C']=2,['D']=3,['E']=4,['F']=5,['G']=6,['H']=7,['I']=8,['J']=9,
        ['K']=10,['L']=11,['M']=12,['N']=13,['O']=14,['P']=15,['Q']=16,['R']=17,['S']=18,['T']=19,
        ['U']=20,['V']=21,['W']=22,['X']=23,['Y']=24,['Z']=25,
        ['a']=26,['b']=27,['c']=28,['d']=29,['e']=30,['f']=31,['g']=32,['h']=33,['i']=34,['j']=35,
        ['k']=36,['l']=37,['m']=38,['n']=39,['o']=40,['p']=41,['q']=42,['r']=43,['s']=44,['t']=45,
        ['u']=46,['v']=47,['w']=48,['x']=49,['y']=50,['z']=51,
        ['0']=52,['1']=53,['2']=54,['3']=55,['4']=56,['5']=57,['6']=58,['7']=59,['8']=60,['9']=61,
        ['+']=62,['/']=63
    };
    size_t len = strlen(in);
    unsigned char* out = (unsigned char*)malloc(len * 3 / 4);
    size_t o = 0;
    for (size_t i=0; i+3<len; i+=4) {
        int pad = (in[i+2]=='='?1:0)+(in[i+3]=='='?1:0);
        uint32_t n = (d[(int)in[i]]<<18)|(d[(int)in[i+1]]<<12)|(d[(int)in[i+2]]<<6)|d[(int)in[i+3]];
        out[o++] = (n>>16)&255;
        if(pad<2) out[o++] = (n>>8)&255;
        if(pad<1) out[o++] = n&255;
    }
    *outlen = o;
    return out;
}

static int read_floats_from_accessor(const cgltf_accessor* acc,float* dst,int comp){
    if(!acc||!dst) return 0;
    for(cgltf_size i=0;i<acc->count;i++){
        cgltf_float tmp[16]={0};
        cgltf_accessor_read_float(acc,i,tmp,comp);
        memcpy(dst+i*comp,tmp,sizeof(float)*comp);
    }
    return 1;
}

static uint32_t* read_indices_u32(const cgltf_accessor* acc){
    if(!acc) return NULL;
    cgltf_size n = acc->count;
    uint32_t* out = (uint32_t*)malloc(sizeof(uint32_t)*n);
    for(cgltf_size i=0;i<n;i++){
        cgltf_uint idx = (cgltf_uint)cgltf_accessor_read_index(acc,i);
        out[i] = (uint32_t)idx;
    }
    return out;
}

/* =================== Mat4 / Transform =================== */
static void mat4_identity(float m[16]){
    memset(m,0,16*sizeof(float));
    m[0]=m[5]=m[10]=m[15]=1.0f;
}
static void mat4_mul(float o[16],const float a[16],const float b[16]){
    float r[16];
    for(int c=0;c<4;c++){
        for(int rI=0;rI<4;rI++){
            r[c*4+rI] = a[0*4+rI]*b[c*4+0] + a[1*4+rI]*b[c*4+1] + a[2*4+rI]*b[c*4+2] + a[3*4+rI]*b[c*4+3];
        }
    }
    memcpy(o,r,sizeof(r));
}
static void transform_position(const float m[16],const float in[3],float outp[3]){
    float x=in[0],y=in[1],z=in[2];
    outp[0]=m[0]*x+m[4]*y+m[8]*z+m[12];
    outp[1]=m[1]*x+m[5]*y+m[9]*z+m[13];
    outp[2]=m[2]*x+m[6]*y+m[10]*z+m[14];
}
static void transform_normal_approx(const float m[16],const float in[3],float outn[3]){
    float x=in[0],y=in[1],z=in[2];
    float ox=m[0]*x+m[4]*y+m[8]*z;
    float oy=m[1]*x+m[5]*y+m[9]*z;
    float oz=m[2]*x+m[6]*y+m[10]*z;
    float len=(float)sqrt(ox*ox+oy*oy+oz*oz);
    if(len>1e-8f){ox/=len;oy/=len;oz/=len;}
    outn[0]=ox;outn[1]=oy;outn[2]=oz;
}

/* =================== Weltmatrix mit optionalem Mirror =================== */
static void node_world_matrix(const cgltf_node* node,float world[16]){
    mat4_identity(world);
    float stack[64][16]; 
    int sp = 0;
    const cgltf_node* n = node;
    while(n){
        float local[16];
        cgltf_node_transform_local(n, local);
        memcpy(stack[sp++], local, sizeof(local));
        n = n->parent;
    }
    for(int i=sp-1; i>=0; --i){
        float tmp[16];
        mat4_mul(tmp, world, stack[i]);
        memcpy(world, tmp, sizeof(tmp));
    }
    if(g_mirror_x){
        float mirror[16];
        mat4_identity(mirror);
        mirror[0] = -1.0f;
        float tmp[16];
        mat4_mul(tmp, mirror, world);
        memcpy(world, tmp, sizeof(tmp));
    }
}

/* =================== Utility: Compute Face Normals =================== */
static void compute_missing_normals(Prim* pr) {
    if(!pr || !pr->positions || !pr->indices) return;
    int vcount = pr->vertex_count;
    int icount = pr->index_count;
    if(vcount <= 0 || icount <= 0) return;

    if(!pr->normals) {
        pr->normals = (float*)calloc(vcount * 3, sizeof(float));
    } else {
        memset(pr->normals, 0, vcount * 3 * sizeof(float));
    }

    for(int i=0; i<icount; i+=3) {
        int i0 = pr->indices[i+0];
        int i1 = pr->indices[i+1];
        int i2 = pr->indices[i+2];
        if(i0 >= vcount || i1 >= vcount || i2 >= vcount) continue;

        float* v0 = &pr->positions[i0*3];
        float* v1 = &pr->positions[i1*3];
        float* v2 = &pr->positions[i2*3];

        float ux = v1[0]-v0[0];
        float uy = v1[1]-v0[1];
        float uz = v1[2]-v0[2];
        float vx = v2[0]-v0[0];
        float vy = v2[1]-v0[1];
        float vz = v2[2]-v0[2];

        float nx = uy*vz - uz*vy;
        float ny = uz*vx - ux*vz;
        float nz = ux*vy - uy*vx;

        pr->normals[i0*3+0] += nx;
        pr->normals[i0*3+1] += ny;
        pr->normals[i0*3+2] += nz;
        pr->normals[i1*3+0] += nx;
        pr->normals[i1*3+1] += ny;
        pr->normals[i1*3+2] += nz;
        pr->normals[i2*3+0] += nx;
        pr->normals[i2*3+1] += ny;
        pr->normals[i2*3+2] += nz;
    }

    for(int i=0; i<vcount; ++i) {
        float* n = &pr->normals[i*3];
        float len = sqrtf(n[0]*n[0] + n[1]*n[1] + n[2]*n[2]);
        if(len > 1e-8f) {
            n[0] /= len;
            n[1] /= len;
            n[2] /= len;
        }
    }
}

static int detect_has_alpha(const unsigned char* data, size_t size, const char* mime) {
    if (!data || size < 16) return 0;

    if (mime) {
        if (strstr(mime, "png")) {
            // PNG prüfen
            if (memcmp(data, "\x89PNG\r\n\x1a\n", 8) != 0) return 0;
            unsigned char colorType = data[25];
            return (colorType == 6);
        }
        if (strstr(mime, "jpeg") || strstr(mime, "jpg")) return 0; // JPEG nie Alpha
        if (strstr(mime, "tga")) {
            // TGA 32bit?
            if (size > 17) {
                unsigned char bpp = data[16];
                unsigned char attrib = data[17];
                return (bpp == 32 && (attrib & 0x0F) != 0);
            }
        }
    }

    // Wenn kein Mime-Type bekannt, versuchen wir Heuristik:
    if (memcmp(data, "\x89PNG\r\n\x1a\n", 8) == 0) {
        unsigned char colorType = data[25];
        return (colorType == 6);
    }

    return 0;
}

/* =================== Loader =================== */
API void* glb_load(const char* filename){
    cgltf_options opt; memset(&opt,0,sizeof(opt));
    cgltf_data* data=NULL;
    if(cgltf_parse_file(&opt,filename,&data)!=cgltf_result_success) return NULL;
    if(cgltf_load_buffers(&opt,data,filename)!=cgltf_result_success){ cgltf_free(data); return NULL; }

    int prim_total=0;
    for(cgltf_size i=0;i<data->nodes_count;i++){
        const cgltf_node* n=&data->nodes[i];
        if(n->mesh) prim_total+=(int)n->mesh->primitives_count;
    }
    if(prim_total<=0){ cgltf_free(data); return NULL; }

    GLBHandle* h=(GLBHandle*)calloc(1,sizeof(GLBHandle));
    h->prims=(Prim*)calloc(prim_total,sizeof(Prim));
    h->prim_count=prim_total;
    h->owned=data;

    int pidx=0;
    for(cgltf_size ni=0;ni<data->nodes_count;ni++){
        const cgltf_node* node=&data->nodes[ni];
        if(!node->mesh) continue;

        float world[16];
        node_world_matrix(node,world);

        for(cgltf_size pr=0;pr<node->mesh->primitives_count;pr++,pidx++){
            const cgltf_primitive* prim=&node->mesh->primitives[pr];
            if(prim->type!=cgltf_primitive_type_triangles){--pidx; continue;}
			
			// --- Attribute suchen ---
			const cgltf_accessor* acc_pos = NULL;
			const cgltf_accessor* acc_nrm = NULL;
			const cgltf_accessor* acc_uv0 = NULL;
			const cgltf_accessor* acc_col0 = NULL;			

            for(cgltf_size a=0;a<prim->attributes_count;a++){
                const cgltf_attribute* at=&prim->attributes[a];
                if(at->type==cgltf_attribute_type_position) acc_pos=at->data;
                else if(at->type==cgltf_attribute_type_normal) acc_nrm=at->data;
                else if(at->type==cgltf_attribute_type_texcoord && at->index==0) acc_uv0=at->data;
				else if (at->type == cgltf_attribute_type_texcoord && at->index == 0) acc_uv0 = at->data;
				else if (at->type == cgltf_attribute_type_color && at->index == 0) acc_col0 = at->data;				
            }
			
            if(!acc_pos){ --pidx; continue; }
			
            int vcount=(int)acc_pos->count;
            h->prims[pidx].vertex_count=vcount;
            h->prims[pidx].positions=(float*)malloc(sizeof(float)*3*vcount);
            if(acc_nrm) h->prims[pidx].normals=(float*)malloc(sizeof(float)*3*vcount);
            if(acc_uv0) h->prims[pidx].texcoords0=(float*)malloc(sizeof(float)*2*vcount);

            // --- Vertex-Daten einlesen ---
			float* pos_tmp=(float*)malloc(sizeof(float)*3*vcount);
            read_floats_from_accessor(acc_pos,pos_tmp,3);
            float* nrm_tmp=NULL;
            if(acc_nrm){ nrm_tmp=(float*)malloc(sizeof(float)*3*vcount); read_floats_from_accessor(acc_nrm,nrm_tmp,3); }
            if(acc_uv0) read_floats_from_accessor(acc_uv0,h->prims[pidx].texcoords0,2);

			if (acc_col0) {
				// GLTF hat Vertex Colors → optional einlesen (RGBA oder RGB)
				float* cols = (float*)malloc(sizeof(float) * 4 * vcount);
				read_floats_from_accessor(acc_col0, cols, 4);
				// Du könntest sie z. B. in die BaseColorFactor übernehmen
				// oder in Zukunft im Prim speichern (falls du willst)
				// z. B. memcpy(h->prims[pidx].baseColorFactor, cols, 4*sizeof(float));
				free(cols);
			} else if (g_use_default_color) {
				// Keine Vertex Colors → Default BaseColor verwenden
				for (int i = 0; i < 4; i++) h->prims[pidx].baseColorFactor[i] = g_default_color[i];
			}			
			
            // --- Vertexdaten transformieren ---
            for(int i=0;i<vcount;i++){
                float ip[3]={pos_tmp[i*3+0],pos_tmp[i*3+1],pos_tmp[i*3+2]};
                float op[3];
                transform_position(world,ip,op);
                memcpy(&h->prims[pidx].positions[i*3],op,sizeof(float)*3);

                if(nrm_tmp){
                    float in[3]={nrm_tmp[i*3+0],nrm_tmp[i*3+1],nrm_tmp[i*3+2]};
                    float on[3];
                    transform_normal_approx(world,in,on);
                    if(g_mirror_x) on[0] = -on[0];
                    memcpy(&h->prims[pidx].normals[i*3],on,sizeof(float)*3);
                }
            }
            free(pos_tmp); if(nrm_tmp) free(nrm_tmp);

            // --- Indices laden + Winding korrigieren ---
            if(prim->indices) h->prims[pidx].indices=read_indices_u32(prim->indices);
            else {
                h->prims[pidx].indices=(uint32_t*)malloc(sizeof(uint32_t)*vcount);
                for(int i=0;i<vcount;i++) h->prims[pidx].indices[i]=(uint32_t)i;
            }
            h->prims[pidx].index_count=prim->indices?(int)prim->indices->count:vcount;

            if(g_mirror_x){
                for(int i=0;i<h->prims[pidx].index_count;i+=3){
                    uint32_t t=h->prims[pidx].indices[i+1];
                    h->prims[pidx].indices[i+1]=h->prims[pidx].indices[i+2];
                    h->prims[pidx].indices[i+2]=t;
                }
            }
			
            // --- Material (BaseColor/Metal/Rough + data:URI/embedded) ---
            if(prim->material){
				cgltf_material* mat=prim->material;
                cgltf_pbr_metallic_roughness* pbr=&mat->pbr_metallic_roughness;

				// --- Transparenz aus Material ableiten ---
				int has_alpha = 0;
				if (mat->alpha_mode == cgltf_alpha_mode_blend ||
					mat->alpha_mode == cgltf_alpha_mode_mask ||
					pbr->base_color_factor[3] < 0.999f) {
					has_alpha = 1;
				}
				h->prims[pidx].has_alpha = has_alpha;

                for(int i=0;i<4;i++) h->prims[pidx].baseColorFactor[i]=pbr->base_color_factor[i];
                h->prims[pidx].metallicFactor=pbr->metallic_factor;
                h->prims[pidx].roughnessFactor=pbr->roughness_factor;

                if(pbr->base_color_texture.texture){
                    cgltf_image* img=pbr->base_color_texture.texture->image;
                    if(img){
                        if (img->mime_type) {
							h->prims[pidx].mimeType = dup_str(img->mime_type);
						}
						
						if(img->uri){
                            if(strncmp(img->uri,"data:",5)==0){
                                const char* comma=strchr(img->uri,',');
                                if(comma){
                                    size_t len=0;
                                    unsigned char* dat=decode_base64(comma+1,&len);
                                    h->prims[pidx].baseColorData=dat;
                                    h->prims[pidx].baseColorSize=len;
                                }
                            }else h->prims[pidx].baseColorPath=dup_str(img->uri);
                        }else if(img->buffer_view){
                            cgltf_buffer_view* bv=img->buffer_view;
                            h->prims[pidx].baseColorData=(unsigned char*)malloc(bv->size);
                            memcpy(h->prims[pidx].baseColorData,(uint8_t*)bv->buffer->data+bv->offset,bv->size);
                            h->prims[pidx].baseColorSize=bv->size;
                        }
                    }
                }
				
				// Nach dem Laden prüfen, ob Textur Alpha hat
				if (h->prims[pidx].baseColorData && h->prims[pidx].baseColorSize > 0) {
					if (detect_has_alpha(h->prims[pidx].baseColorData,
										 h->prims[pidx].baseColorSize,
										 h->prims[pidx].mimeType)) {
						h->prims[pidx].has_alpha = 1;
					}
				}
				
            }
			
			// --- Falls Normalen fehlen und aktiviert: berechne sie automatisch ---
			if(g_generate_normals && !acc_nrm) {
				compute_missing_normals(&h->prims[pidx]);
			}
        }
    }
    return h;
}

/* =================== Normalize to Unit Cube =================== */
API void glb_normalize_unitcube(void* handle) {
    if(!handle) return;
    GLBHandle* h = (GLBHandle*)handle;

    float minx=1e30f, miny=1e30f, minz=1e30f;
    float maxx=-1e30f, maxy=-1e30f, maxz=-1e30f;

    // 1) Grenzen über alle Vertices sammeln
    for(int p=0; p<h->prim_count; ++p) {
        Prim* pr = &h->prims[p];
        for(int i=0; i<pr->vertex_count; ++i) {
            float x = pr->positions[i*3+0];
            float y = pr->positions[i*3+1];
            float z = pr->positions[i*3+2];
            if(x<minx) minx=x; if(y<miny) miny=y; if(z<minz) minz=z;
            if(x>maxx) maxx=x; if(y>maxy) maxy=y; if(z>maxz) maxz=z;
        }
    }

    // 2) Mittelpunkt und Größe
    float cx = (minx+maxx)*0.5f;
    float cy = (miny+maxy)*0.5f;
    float cz = (minz+maxz)*0.5f;

    float sx = maxx-minx;
    float sy = maxy-miny;
    float sz = maxz-minz;
    float maxdim = fmaxf(sx, fmaxf(sy, sz));
    if(maxdim < 1e-6f) maxdim = 1.0f; // Schutz gegen Nullgröße
    float scale = 1.0f / maxdim;

    // 3) Anwenden auf alle Vertices
    for(int p=0; p<h->prim_count; ++p) {
        Prim* pr = &h->prims[p];
        for(int i=0; i<pr->vertex_count; ++i) {
            float* v = &pr->positions[i*3];
            v[0] = (v[0]-cx) * scale;
            v[1] = (v[1]-cy) * scale;
            v[2] = (v[2]-cz) * scale;
        }
    }
}

/* =================== Getter =================== */
API int glb_get_primitive_count(void* H){return H?((GLBHandle*)H)->prim_count:0;}
API int glb_get_vertex_count(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?0:h->prims[p].vertex_count;}
API int glb_get_index_count(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?0:h->prims[p].index_count;}
API float* glb_get_positions(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?NULL:h->prims[p].positions;}
API float* glb_get_normals(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?NULL:h->prims[p].normals;}
API float* glb_get_texcoords0(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?NULL:h->prims[p].texcoords0;}
API uint32_t* glb_get_indices(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?NULL:h->prims[p].indices;}
API const char* glb_get_basecolor_path(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?NULL:h->prims[p].baseColorPath;}
API const void* glb_get_basecolor_data(void* H,int p,size_t*outSize){GLBHandle*h=(GLBHandle*)H;if(!h||p<0||p>=h->prim_count)return NULL;if(outSize)*outSize=h->prims[p].baseColorSize;return h->prims[p].baseColorData;}
API const float* glb_get_basecolor_factor(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?NULL:h->prims[p].baseColorFactor;}
API float glb_get_metallic(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?1.0f:h->prims[p].metallicFactor;}
API float glb_get_roughness(void* H,int p){GLBHandle*h=(GLBHandle*)H;return(!h||p<0||p>=h->prim_count)?1.0f:h->prims[p].roughnessFactor;}

API int glb_get_has_alpha(void* H, int p){
    GLBHandle* h = (GLBHandle*)H;
    return (!h || p < 0 || p >= h->prim_count) ? 0 : h->prims[p].has_alpha;
}

/* =================== Free =================== */
API void glb_free(void* handle){
    if(!handle)return;
    GLBHandle*h=(GLBHandle*)handle;
    for(int i=0;i<h->prim_count;i++){
        free(h->prims[i].positions);
        free(h->prims[i].normals);
        free(h->prims[i].texcoords0);
        free(h->prims[i].indices);
        free(h->prims[i].baseColorPath);
        free(h->prims[i].baseColorData);
		free(h->prims[i].mimeType);
    }
    free(h->prims);
    if(h->owned) cgltf_free(h->owned);
    free(h);
}
