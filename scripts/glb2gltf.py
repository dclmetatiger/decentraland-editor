#!/usr/bin/env python3
import os
import sys
import mimetypes
import argparse
from copy import deepcopy
from pygltflib import GLTF2

ALIGN = 4
def _pad4(n: int) -> int:
    return (n + (ALIGN - 1)) & ~(ALIGN - 1)

# converts a GLB file into a GLTF, extracts textures to subfolder textures/
def extract_glb_to_gltf(glb_path, out_gltf_path=None):
    if not os.path.isfile(glb_path):
        print(f"- Error: GLB file not found: {glb_path}")
        return

    # target paths
    base_dir = os.path.dirname(os.path.abspath(glb_path))
    base_name = os.path.splitext(os.path.basename(glb_path))[0]
    if out_gltf_path is None:
        out_gltf_path = os.path.join(base_dir, base_name + ".gltf")

    textures_dir = os.path.join(base_dir, "textures")
    os.makedirs(textures_dir, exist_ok=True)

    print(f"Loading GLB: {glb_path}")
    gltf = GLTF2().load(glb_path)

    # extract binary data
    blob = gltf.binary_blob()
    if blob is None:
        print("- No embedded Binary Data found in GLB")
        return

    # --- Extract images from binary blob
    image_bv_idx = set()
    if not gltf.images:
        print("- No embedded Textures found in GLB")
    else:
        for i, img in enumerate(gltf.images):
            if img.bufferView is None:
                continue

            bv = gltf.bufferViews[img.bufferView]
            start = bv.byteOffset or 0
            end = start + (bv.byteLength or 0)
            img_data = blob[start:end]

            # set filename, prefers original URI if available
            orig_name = None
            if getattr(img, "uri", None):
                orig_name = os.path.basename(img.uri)
            elif getattr(img, "name", None):
                orig_name = img.name
            
            # extension according MIME type
            ext = mimetypes.guess_extension(img.mimeType or "image/png") or ".png"
            
            # determine final filename
            if orig_name:
                base, orig_ext = os.path.splitext(orig_name)
                filename = f"{base}{orig_ext or ext}"
            else:
                filename = f"image_{i}{ext}"
            
            # remove invalid characters from filename
            safe_name = "".join(c if c.isalnum() or c in "_-." else "_" for c in filename)
            tex_path = os.path.join(textures_dir, safe_name)
            rel_uri = os.path.join("textures", safe_name).replace("\\", "/")

            with open(tex_path, "wb") as f:
                f.write(img_data)
            
            # mark image as external
            img.uri = rel_uri
            image_bv_idx.add(img.bufferView)
            img.bufferView = None
            print(f"- Extracting: {img.uri}")

    # --- Repack binary: keep only non-image bufferViews
    if not gltf.buffers or not gltf.bufferViews:
        print("- No buffers or bufferViews to repack.")
        gltf.save_json(out_gltf_path)
        return

    new_blob = bytearray()
    new_bufferViews = []
    old_to_new_bv = {}

    for old_idx, bv in enumerate(gltf.bufferViews):
        if old_idx in image_bv_idx:
            continue  # skip image bufferViews

        start = (bv.byteOffset or 0)
        length = (bv.byteLength or 0)
        end = start + length

        # align to 4 bytes
        pad_len = (-len(new_blob)) % ALIGN
        if pad_len:
            new_blob += b"\x00" * pad_len

        nbv = deepcopy(bv)
        nbv.byteOffset = len(new_blob)
        new_blob += blob[start:end]

        new_idx = len(new_bufferViews)
        new_bufferViews.append(nbv)
        old_to_new_bv[old_idx] = new_idx

    # remap all accessors and sparse data to new bufferView indices
    if gltf.accessors:
        for acc in gltf.accessors:
            if acc is None:
                continue
            if acc.bufferView is not None:
                acc.bufferView = old_to_new_bv.get(acc.bufferView, acc.bufferView)
            if acc.sparse is not None:
                if acc.sparse.indices and acc.sparse.indices.bufferView is not None:
                    acc.sparse.indices.bufferView = old_to_new_bv.get(acc.sparse.indices.bufferView,
                                                                      acc.sparse.indices.bufferView)
                if acc.sparse.values and acc.sparse.values.bufferView is not None:
                    acc.sparse.values.bufferView = old_to_new_bv.get(acc.sparse.values.bufferView,
                                                                     acc.sparse.values.bufferView)

    # update GLTF structure
    gltf.bufferViews = new_bufferViews
    gltf.buffers[0].byteLength = len(new_blob)

    # write new external .bin
    bin_filename = base_name + ".bin"
    bin_path = os.path.join(base_dir, bin_filename)
    with open(bin_path, "wb") as f:
        f.write(new_blob)
    print(f"- Binary Buffer repacked: {bin_filename} ({len(new_blob)} bytes)")

    # set external reference
    gltf.buffers[0].uri = bin_filename
    gltf.set_binary_blob(None)

    # save GLTF JSON
    gltf.save_json(out_gltf_path)
    print(f"- GLTF converted to: {out_gltf_path}")

# --- main entry point ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python glb_to_gltf.py <input> [output.gltf]")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Converts GLB to GLTF and extracts embedded textures")
    parser.add_argument("mappath", type=str, help="Path to the .bsp file")
    args = parser.parse_args()
    
    # checks for .bsp extension (indicator that it is a valid map to convert)
    if not args.mappath.endswith(".bsp"):
        raise ValueError("ERROR: filename must end with '.bsp'")

    # create final filenames
    input_file = args.mappath.replace(".bsp", ".glb")
    output_file = args.mappath.replace(".bsp", ".gltf")

    extract_glb_to_gltf(input_file, output_file)
