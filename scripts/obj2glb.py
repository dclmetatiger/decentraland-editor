#!/usr/bin/env python3
import argparse, os, mimetypes
import numpy as np
import sys
from collections import defaultdict
from pygltflib import (
    GLTF2, Scene, Node, Mesh, Buffer, BufferView, Accessor, Asset, Primitive,
    PbrMetallicRoughness, Material, Image, Texture, TextureInfo
)

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../dcl.game")))

import materials_alpha
import materials_emission
import materials_surface


# -------- helpers --------
def pad4(n: int) -> int:
    return (n + 3) & ~3


def short_name(s: str, default: str) -> str:
    if not s:
        return default
    s = s.replace("\\", "/").split("/")[-1]
    return s or default


def normalize_image_name(texpath: str, mime: str) -> str:
    known_exts = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".gif", ".webp", ".dds", ".ktx", ".ktx2"}
    name = os.path.basename(texpath)
    while True:
        root, ext = os.path.splitext(name)
        if ext.lower() in known_exts and root:
            name = root
        else:
            break
    if mime == "image/jpeg":
        ext = ".jpg"
    elif mime == "image/png":
        ext = ".png"
    else:
        ext = ".png"
    return name + ext


# --- MTL Parser with Emission Support ---
def parse_mtl(mtl_path):
    props = {}
    cur = None
    try:
        with open(mtl_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("newmtl "):
                    cur = line.split(maxsplit=1)[1]
                    if cur not in props:
                        props[cur] = {
                            "map_Kd": "", "Kd": None,
                            "map_Ke": "", "Ke": None
                        }
                elif cur:
                    ll = line.lower()
                    if ll.startswith("map_kd "):
                        props[cur]["map_Kd"] = line.split(maxsplit=1)[1]
                        #print("Found " + props[cur]["map_Kd"])
                    elif ll.startswith("kd "):
                        p = line.split()
                        try:
                            props[cur]["Kd"] = [float(p[1]), float(p[2]), float(p[3])]
                        except:
                            pass
                    elif ll.startswith("map_ke "):
                        props[cur]["map_Ke"] = line.split(maxsplit=1)[1]
                    elif ll.startswith("ke "):
                        p = line.split()
                        try:
                            props[cur]["Ke"] = [float(p[1]), float(p[2]), float(p[3])]
                        except:
                            pass
    except FileNotFoundError:
        pass
    return props


# -------- OBJ loader with VN support --------
def load_obj_with_uvs(path):
    V, VT, VN = [], [], []
    mtllibs, cur_mtl = [], None
    faces_triples = []
    face_mtls = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.lstrip()
            if s.startswith("mtllib "):
                mtllibs.extend(s.strip().split()[1:])
            elif s.startswith("usemtl "):
                cur_mtl = s.strip().split()[1]
            elif s.startswith("v "):
                p = s.strip().split()
                V.append([float(p[1]), float(p[2]), float(p[3])])
            elif s.startswith("vt "):
                p = s.strip().split()
                u = float(p[1])
                v = 1.0 - float(p[2])   # glTF V inverted
                VT.append([u, v])
            elif s.startswith("vn "):
                p = s.strip().split()
                VN.append([float(p[1]), float(p[2]), float(p[3])])
            elif s.startswith("f "):
                parts = s.strip().split()[1:]
                tri = []
                for tok in parts:
                    a = tok.split("/")
                    v  = int(a[0]) - 1 if a[0] else -1
                    vt = int(a[1]) - 1 if len(a) > 1 and a[1] else -1
                    vn = int(a[2]) - 1 if len(a) > 2 and a[2] else -1
                    tri.append((v, vt, vn))
                if len(tri) == 3:
                    faces_triples.append(tri); face_mtls.append(cur_mtl)
                elif len(tri) == 4:
                    faces_triples.append([tri[0], tri[1], tri[2]]); face_mtls.append(cur_mtl)
                    faces_triples.append([tri[0], tri[2], tri[3]]); face_mtls.append(cur_mtl)

    V  = np.array(V, dtype=np.float32) if V  else np.zeros((0,3), np.float32)
    VT = np.array(VT, dtype=np.float32) if VT else np.zeros((0,2), np.float32)
    VN = np.array(VN, dtype=np.float32) if VN else np.zeros((0,3), np.float32)
    return V, VT, VN, faces_triples, face_mtls, mtllibs


# -------- unify vertices (position, uv, normal) --------
def build_unified_vertices(V, VT, VN, faces_triples, face_mtls):
    has_uv = VT.shape[0] > 0
    has_n  = VN.shape[0] > 0
    remap = {}
    positions = []
    texcoords = []
    normals = []
    groups = defaultdict(list)

    def key(v, vt, vn):
        return (
            v,
            vt if has_uv and vt >= 0 else -1,
            vn if has_n and vn >= 0 else -1
        )

    for tri, mtl in zip(faces_triples, face_mtls):
        tri_idx = []
        for (v, vt, vn) in tri:
            k = key(v, vt, vn)
            if k not in remap:
                remap[k] = len(positions)
                positions.append(V[v] if v >= 0 else [0, 0, 0])
                if has_uv and vt >= 0:
                    texcoords.append(VT[vt])
                else:
                    texcoords.append([0.0, 0.0])
                if has_n and vn >= 0:
                    normals.append(VN[vn])
                else:
                    normals.append([0.0, 1.0, 0.0])
            tri_idx.append(remap[k])
        groups[mtl].extend(tri_idx)

    P = np.array(positions, dtype=np.float32)
    T = np.array(texcoords, dtype=np.float32) if has_uv else None
    N = np.array(normals, dtype=np.float32) if has_n else None
    return P, T, N, groups


# -------- compute normals (fallback) --------
def compute_normals(P, groups, smooth_angle_deg=30.0):
    smooth_angle = np.radians(smooth_angle_deg)
    cos_thresh = np.cos(smooth_angle)
    all_faces = []
    for idxs in groups.values():
        tris = np.array(idxs, dtype=np.int32).reshape(-1, 3)
        all_faces.append(tris)
    all_faces = np.vstack(all_faces)
    v0 = P[all_faces[:, 0]]
    v1 = P[all_faces[:, 1]]
    v2 = P[all_faces[:, 2]]
    face_normals = np.cross(v1 - v0, v2 - v0)
    face_normals /= np.linalg.norm(face_normals, axis=1, keepdims=True) + 1e-9

    vertex_faces = [[] for _ in range(len(P))]
    for fi, tri in enumerate(all_faces):
        for vi in tri:
            vertex_faces[vi].append(fi)

    normals = np.zeros_like(P)
    for vi, faces in enumerate(vertex_faces):
        if not faces:
            continue
        n_sum = np.zeros(3)
        ref_n = face_normals[faces[0]]
        for fi in faces:
            fn = face_normals[fi]
            if np.dot(fn, ref_n) >= cos_thresh:
                n_sum += fn
        norm_len = np.linalg.norm(n_sum)
        if not np.isfinite(norm_len) or norm_len < 1e-12:
            avg = np.mean(face_normals[faces], axis=0)
            if np.linalg.norm(avg) > 1e-12:
                normals[vi] = avg / np.linalg.norm(avg)
            else:
                normals[vi] = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        else:
            normals[vi] = n_sum / norm_len
    normals = np.nan_to_num(normals, nan=0.0)
    return normals

def compute_weighted_normals_face_area_keep_sharp(
    P, groups, N_src=None,
    weld_tol=1e-2, strength=0.5,
    sharp_angle_deg=30.0
):
    import numpy as np

    cos_sharp = np.cos(np.radians(sharp_angle_deg))

    # --- Alle Faces sammeln ---
    all_faces = []
    for idxs in groups.values():
        tris = np.asarray(idxs, dtype=np.int32).reshape(-1, 3)
        all_faces.append(tris)
    all_faces = np.vstack(all_faces)
    v0, v1, v2 = P[all_faces[:, 0]], P[all_faces[:, 1]], P[all_faces[:, 2]]

    # --- Flächennormalen + Areagewicht ---
    fn_raw = np.cross(v1 - v0, v2 - v0)
    areas = np.linalg.norm(fn_raw, axis=1) * 0.5
    fn = fn_raw / (np.linalg.norm(fn_raw, axis=1, keepdims=True) + 1e-20)

    # --- Vertex→Faces adjacency ---
    Vcount = len(P)
    vert_faces = [[] for _ in range(Vcount)]
    for fi, tri in enumerate(all_faces):
        for vi in tri:
            vert_faces[vi].append(fi)

    # --- „Weld“-Gruppen nur nach Position ---
    key = np.round(P / weld_tol).astype(np.int64)
    key_flat = key.view([('', key.dtype)] * key.shape[1]).ravel()
    uniq, inv = np.unique(key_flat, return_inverse=True)

    # --- Ergebnisnormalen ---
    outN = np.zeros((Vcount, 3), dtype=np.float32)

    # --- Für jede Position (mehrere Vertices möglich) ---
    for g_idx in range(len(uniq)):
        verts = np.where(inv == g_idx)[0]
        if len(verts) == 0:
            continue

        # Alle Faces an dieser Position sammeln
        face_set = set()
        for vi in verts:
            face_set.update(vert_faces[vi])
        if not face_set:
            outN[verts] = [0, 1, 0]
            continue
        face_idx = np.fromiter(face_set, dtype=np.int64)
        fn_g = fn[face_idx]
        w_g = areas[face_idx]

        # --- Clustering nach Winkel (Keep Sharp) ---
        clusters = []
        for fi, n in zip(face_idx, fn_g):
            assigned = False
            for c in clusters:
                if np.dot(n, c["dir"]) >= cos_sharp:
                    # gehört in diese „weiche“ Gruppe
                    c["faces"].append(fi)
                    c["sum"] += n * w_g[np.where(face_idx == fi)][0]
                    c["count"] += 1
                    assigned = True
                    break
            if not assigned:
                clusters.append({
                    "faces": [fi],
                    "dir": n.copy(),
                    "sum": n * w_g[np.where(face_idx == fi)][0],
                    "count": 1
                })

        # Jede Winkelgruppe einzeln mitteln
        for c in clusters:
            avg = c["sum"] / (np.linalg.norm(c["sum"]) + 1e-20)
            for vi in verts:
                # Falls dieser Vertex zu einer Face-Gruppe gehört
                if any(fi in vert_faces[vi] for fi in c["faces"]):
                    outN[vi] = avg

    # --- Optionale Mischung mit bestehenden Normalen ---
    if N_src is not None and len(N_src) == Vcount and 0.0 < strength < 1.0:
        mixed = (1.0 - strength) * outN + strength * N_src
        mixed /= (np.linalg.norm(mixed, axis=1, keepdims=True) + 1e-20)
        outN = mixed

    return np.nan_to_num(outN)

    
    
def merge_by_distance_uvsafe(P, T, N, groups, tol_pos=1e-5, tol_uv=1e-6):
    """
    Merge by Distance (UV-safe):
    Merges vertices only if positions are close AND UVs (if available) are identical
    """
    has_uv = T is not None and len(T) == len(P)
    has_n  = N is not None and len(N) == len(P)

    # 1) round/normalize
    P_rounded = np.round(P / tol_pos) * tol_pos
    if has_uv:
        T_rounded = np.round(T / tol_uv) * tol_uv

    # 2) create unique key (position + UV)
    if has_uv:
        verts = np.hstack((P_rounded, T_rounded))
    else:
        verts = P_rounded

    uniq, inverse = np.unique(verts, axis=0, return_inverse=True)

    # 3) new arrays
    new_P = uniq[:, :3]
    offset = 3
    new_T = None
    if has_uv:
        new_T = uniq[:, offset:offset + 2]
        offset += 2

    new_N = None
    if has_n:
        # Normals: create average of merged vertices
        new_N = np.zeros((len(new_P), 3), dtype=np.float32)
        counts = np.zeros(len(new_P), dtype=np.int32)
        for old_i, new_i in enumerate(inverse):
            new_N[new_i] += N[old_i]
            counts[new_i] += 1
        counts[counts == 0] = 1
        new_N /= counts[:, None]
        # normalize
        norms = np.linalg.norm(new_N, axis=1, keepdims=True) + 1e-9
        new_N = new_N / norms

    # 4) new index groups
    groups_new = {}
    for m, idxs in groups.items():
        groups_new[m] = inverse[np.array(idxs, dtype=np.int64)].tolist()

    #print(f"🧩 UV-safe Merge: {len(P)} → {len(new_P)} Vertices "
    #      f"(tol_pos={tol_pos}, tol_uv={tol_uv})")

    return new_P, new_T, new_N, groups_new



# -------- write GLB --------
def write_glb(P, T, groups, mtl_props, obj_dir, outpath, N=None):
    import numpy as np
    from pygltflib import (GLTF2, Scene, Node, Mesh, Buffer, BufferView, Accessor, Asset, Primitive,
                           PbrMetallicRoughness, Material, Image, Texture, TextureInfo)

    bin_blob = bytearray()
    bufferViews, accessors = [], []
    images, textures, materials = [], [], []
    meshes, nodes = [], []

    def add_view(data: bytes, target=None) -> int:
        off = len(bin_blob)
        bin_blob.extend(data)
        while len(bin_blob) % 4:
            bin_blob.append(0)
        idx = len(bufferViews)
        bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(data), target=target))
        return idx

    # --- POSITION ---
    P = P.astype(np.float32, copy=False)
    bv_pos = add_view(P.tobytes(), 34962)
    vmin, vmax = P.min(axis=0).tolist(), P.max(axis=0).tolist()
    acc_pos = len(accessors)
    accessors.append(Accessor(bufferView=bv_pos, componentType=5126, count=len(P), type="VEC3",
                              min=vmin, max=vmax))

    # --- NORMAL ---
    acc_n = None
    if N is not None and len(N) == len(P):
        N = N.astype(np.float32, copy=False)
        bv_n = add_view(N.tobytes(), 34962)
        acc_n = len(accessors)
        accessors.append(Accessor(bufferView=bv_n, componentType=5126, count=len(N), type="VEC3"))

    # --- UV ---
    acc_uv = None
    have_uv = T is not None and len(T) == len(P)
    if have_uv:
        T = T.astype(np.float32, copy=False)
        bv_uv = add_view(T.tobytes(), 34962)
        acc_uv = len(accessors)
        accessors.append(Accessor(bufferView=bv_uv, componentType=5126, count=len(T), type="VEC2"))

    # --- MATERIALS ---
    mtl_index = {}
    for name, p in mtl_props.items():
        lname = (name or "").lower()

        # Surface-Defaults
        metallic_value  = float(getattr(materials_surface, "default_metallic", 0.0))
        roughness_value = float(getattr(materials_surface, "default_roughness", 1.0))
        for kw, pair in getattr(materials_surface, "surfacekeywords", {}).items():
            try:
                m_val, r_val = pair
            except Exception:
                continue
            if kw in lname:
                metallic_value  = float(m_val)
                roughness_value = float(r_val)
                break

        texpath = p.get("map_Kd")
        if texpath:
            texname = os.path.basename(texpath).lower()
            for kw, pair in getattr(materials_surface, "surfacekeywords", {}).items():
                try:
                    m_val, r_val = pair
                except Exception:
                    continue
                if kw in texname:
                    metallic_value  = float(m_val)
                    roughness_value = float(r_val)
                    break

        mr = PbrMetallicRoughness(roughnessFactor=roughness_value, metallicFactor=metallic_value)

        # BaseColorTexture
        texinfo = None
        if texpath and have_uv:
            tex_full = os.path.join(obj_dir, texpath)
            if os.path.exists(tex_full):
                with open(tex_full, "rb") as f:
                    img_bytes = f.read()
                import mimetypes
                mime, _ = mimetypes.guess_type(tex_full)
                if not mime:
                    mime = "image/png"
                bv_img = add_view(img_bytes, None)
                final_name = normalize_image_name(texpath, mime)
                images.append(Image(bufferView=bv_img, mimeType=mime, name=final_name))
                textures.append(Texture(source=len(images)-1))
                texinfo = TextureInfo(index=len(textures)-1)
                mr.baseColorTexture = texinfo

        # Emissive Map (map_Ke)
        emissive_texinfo = None
        em_texpath = p.get("map_Ke")
        if em_texpath and have_uv:
            em_full = os.path.join(obj_dir, em_texpath)
            if os.path.exists(em_full):
                with open(em_full, "rb") as f:
                    em_bytes = f.read()
                em_mime, _ = mimetypes.guess_type(em_full)
                if not em_mime:
                    em_mime = "image/png"
                bv_img_e = add_view(em_bytes, None)
                em_name = normalize_image_name(em_texpath, em_mime)
                images.append(Image(bufferView=bv_img_e, mimeType=em_mime, name=em_name))
                textures.append(Texture(source=len(images)-1))
                emissive_texinfo = TextureInfo(index=len(textures)-1)

        # Emissive-Intensity by Keywords
        def match_emission(text: str):
            t = (text or "").lower()
            for kw, val in getattr(materials_emission, "emissionkeywords", {}).items():
                if kw in t or t.endswith(kw) or t.startswith(kw):
                    try:
                        return float(val)
                    except Exception:
                        pass
            return None

        emissive_intensity = None
        if p.get("Ke"):
            try:
                emissive_intensity = float(max(p["Ke"]))
            except Exception:
                pass
        if emissive_intensity is None and name:
            emissive_intensity = match_emission(name)
        if emissive_intensity is None and texpath:
            base_texname = os.path.basename(texpath).lower()
            shared_count = sum(1 for q in mtl_props.values() if q.get("map_Kd") == texpath)
            if shared_count <= 1:
                emissive_intensity = match_emission(base_texname)

        # Material object
        mat = Material(name=short_name(name, "material"), pbrMetallicRoughness=mr)

        # apply Emission
        if emissive_texinfo or (emissive_intensity is not None):
            intensity = float(emissive_intensity) if emissive_intensity is not None else 1.0
            mat.emissiveFactor = [intensity, intensity, intensity]
            # glTF needs TextureInfo:
            if emissive_texinfo is not None:
                mat.emissiveTexture = emissive_texinfo
            elif texinfo is not None:
                mat.emissiveTexture = texinfo  # Fallback: Diffuse as Emissive

        # Alpha-Keywords
        alpha_hit = False
        lname_for_match = lname
        for akw, alpha_val in getattr(materials_alpha, "alphakeywords", {}).items():
            if akw in lname_for_match:
                alpha_hit = True
                mat.alphaMode = "BLEND"
                mat.doubleSided = True
                try:
                    a = float(alpha_val)
                except Exception:
                    a = 1.0
                # set baseColorFactor to 4 Components
                if not getattr(mr, "baseColorFactor", None):
                    mr.baseColorFactor = [1.0, 1.0, 1.0, a]
                else:
                    bcf = list(mr.baseColorFactor)
                    if len(bcf) < 4:
                        bcf = (bcf + [1.0])[:4]
                    bcf[3] = a
                    mr.baseColorFactor = bcf
                break

        # if alpha is active but baseColorFactor < 4 = extend
        if getattr(mat, "alphaMode", None) == "BLEND":
            bcf = getattr(mr, "baseColorFactor", None)
            if not bcf:
                mr.baseColorFactor = [1.0, 1.0, 1.0, 1.0]
            elif len(bcf) < 4:
                mr.baseColorFactor = list(bcf) + [1.0]

        mtl_index[name] = len(materials)
        materials.append(mat)

    # --- PRIMITIVES / MESHES ---
    for m, idxs in groups.items():
        if not idxs:
            continue
        idxs = np.asarray(idxs, dtype=np.uint32)
        # glTF allows 16- or 32-bit Indices
        use_u16 = (idxs.max() <= 65535)
        dtype = np.uint16 if use_u16 else np.uint32
        comp  = 5123 if use_u16 else 5125

        bv_i = add_view(idxs.astype(dtype, copy=False).tobytes(), 34963)
        acc_i = len(accessors)
        accessors.append(Accessor(bufferView=bv_i, componentType=comp, count=len(idxs), type="SCALAR"))

        attrs = {"POSITION": acc_pos}
        if acc_n is not None:
            attrs["NORMAL"] = acc_n
        if acc_uv is not None:
            attrs["TEXCOORD_0"] = acc_uv

        prim = Primitive(attributes=attrs, indices=acc_i, material=mtl_index.get(m))
        mesh = Mesh(primitives=[prim], name=short_name(m, "mesh"))
        meshes.append(mesh)
        nodes.append(Node(mesh=len(meshes)-1, name=short_name(m, "node")))

    # --- GLTF ---
    gltf = GLTF2(
        asset=Asset(version="2.0"),
        buffers=[Buffer(byteLength=len(bin_blob))],
        bufferViews=bufferViews,
        accessors=accessors,
        images=images or None,
        textures=textures or None,
        materials=materials or None,
        meshes=meshes,
        nodes=nodes,
        scenes=[Scene(nodes=list(range(len(nodes))))],
        scene=0
    )
    gltf.set_binary_blob(bytes(bin_blob))
    gltf.save_binary(outpath)
    print(f"- Vertices: {len(P)}")
    print(f"- Materials: {len(materials)}")
    print(f"- Meshes: {len(meshes)}")


# -------- CLI --------
def main():
    ap = argparse.ArgumentParser(description="OBJ+MTL GLB (with UVs, Emission, PBR, VN).")
    ap.add_argument("mappath", type=str)
    ap.add_argument("--smooth-angle", type=float, default=30.0, help="Smoothing angle in degrees (fallback)")
    args = ap.parse_args()
    
    
    
    if not args.mappath.endswith(".bsp"):
        raise ValueError("ERROR: filename must end with '.bsp'")
    
    input_file = args.mappath.replace(".bsp", "_scaled.obj")
    output_file = args.mappath.replace(".bsp", "_uncompressed.glb")
    
    V, VT, VN, faces_triples, face_mtls, mtllibs = load_obj_with_uvs(input_file)
    P, T, N, groups = build_unified_vertices(V, VT, VN, faces_triples, face_mtls)

    #if N is None or len(N) == 0 or not np.any(N):
    #    print("- No Normals found in OBJ. Calculating Normals...")
    #    N = compute_normals(P, groups, smooth_angle_deg=args.smooth_angle)
    #else:
    #    print(f"- Normals: {len(N)}")
    
    #print("- Calculating Normals...")
    #N = compute_normals(P, groups, smooth_angle_deg=args.smooth_angle)
    
    print("- Calculating Weighted Normals...")
    N = compute_weighted_normals_face_area_keep_sharp(
        P, groups,
        N_src=None,#N if (N is not None and len(N) == len(P)) else None,
        weld_tol=0.01,       # entspricht deinem Blender-"Weld" & Modifier-Threshold
        strength=0.5,        # Blender "Weight 50"
        sharp_angle_deg=89.0     # ~0.57° (Keep Sharp)
    )
            
    # Merge by Distance
    #P, T, N, groups = merge_by_distance_uvsafe(P, T, N, groups, tol_pos=0.001, tol_uv=0.001)

    obj_dir = os.path.dirname(os.path.abspath(input_file))
    
    mtl_props = {}
    for mtl in mtllibs:
        mtl_path = os.path.join(obj_dir, mtl)
        mtl_props.update(parse_mtl(mtl_path))
        #print(mtl_path)

    write_glb(P, T, groups, mtl_props, obj_dir, output_file, N)
    print(f"- Exported to {output_file}")


if __name__ == "__main__":
    main()
