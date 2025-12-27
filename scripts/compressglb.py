#!/usr/bin/env python3
import argparse
import io
import os
import mimetypes
from pygltflib import GLTF2, BufferView, Buffer
from PIL import Image

DEFAULT_MAXSIZE = 1024
DEFAULT_JPEGQUALITY = 90

# set a clean image name
def clean_image_name(name: str, mime: str) -> str:

    if not name:
        name = "image"

    # remove all known image extensions
    known_exts = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".gif", ".webp", ".dds", ".ktx", ".ktx2"}
    base = os.path.basename(name)
    
    while True:
        root, ext = os.path.splitext(base)
        if ext.lower() in known_exts and root:
            base = root
        else:
            break

    # set extension according to MIME type
    if mime == "image/jpeg":
        ext = ".jpg"
    elif mime == "image/png":
        ext = ".png"
    else:
        ext = mimetypes.guess_extension(mime or "") or ".png"

    return base + ext

# extracts GLB image data
def get_image_bytes(gltf, img_idx):
    img = gltf.images[img_idx]

    if img.bufferView is not None and img.bufferView < len(gltf.bufferViews):
        bv = gltf.bufferViews[img.bufferView]
        blob = gltf.binary_blob()
        start = bv.byteOffset or 0
        end = start + bv.byteLength
        return blob[start:end], img.mimeType
    return None, None


# scales to maxsize px and converts to PNG (if Alpha) or JPEG (no Alpha, with Quality)
def resize_and_compress(data: bytes, name: str, maxsize: int, jpegquality: int):
    with Image.open(io.BytesIO(data)) as img:
        orig_size = img.size
        w, h = img.size

        # scale if greater than maxsize
        if max(w, h) > maxsize:
            scale = maxsize / max(w, h)
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)
        else:
            new_size = orig_size

        buf = io.BytesIO()

        if "A" in img.getbands():
            mime = "image/png"
            img.save(buf, format="PNG", optimize=True)
        else:
            mime = "image/jpeg"
            img.convert("RGB").save(buf, format="JPEG", quality=jpegquality)

        final_name = clean_image_name(name, mime)
        return buf.getvalue(), final_name, mime, orig_size, new_size


# replaces embedded image data in GLB buffer
def replace_image_bytes(gltf: GLTF2, img_idx: int, data: bytes, mime: str):
    img = gltf.images[img_idx]
    blob = bytearray(gltf.binary_blob() or b"")

    if img.bufferView is not None and img.bufferView < len(gltf.bufferViews):
        bv = gltf.bufferViews[img.bufferView]
        start = bv.byteOffset or 0
        end = start + bv.byteLength

        if len(data) <= bv.byteLength:
            blob[start:start + len(data)] = data
            if len(data) < bv.byteLength:
                blob[start + len(data):end] = b"\x00" * (bv.byteLength - len(data))
            bv.byteLength = len(data)
        else:
            offset = len(blob)
            blob.extend(data)
            bv = BufferView(buffer=0, byteOffset=offset, byteLength=len(data))
            gltf.bufferViews.append(bv)
            img.bufferView = len(gltf.bufferViews) - 1
    else:
        offset = len(blob)
        blob.extend(data)
        bv = BufferView(buffer=0, byteOffset=offset, byteLength=len(data))
        gltf.bufferViews.append(bv)
        img.bufferView = len(gltf.bufferViews) - 1

    img.uri = None
    img.mimeType = mime

    if not gltf.buffers:
        gltf.buffers = [Buffer(byteLength=len(blob))]
    else:
        gltf.buffers[0].byteLength = len(blob)

    gltf.set_binary_blob(bytes(blob))


def main():
    parser = argparse.ArgumentParser(
        description="Compress GLB textures: JPEG (no alpha), PNG (with alpha). "
                    "Input must be a *_uncompressed.glb file. Output will be saved without '_uncompressed'"
    )
    parser.add_argument("mappath", type=str, help="Input BSP file (must end with .bsp)")
    parser.add_argument("--maxsize", type=int, default=DEFAULT_MAXSIZE,
                        help=f"Maximum edge size in Pixels (default: {DEFAULT_MAXSIZE})")
    parser.add_argument("--quality", type=int, default=DEFAULT_JPEGQUALITY,
                        help=f"JPEG-Quality 1-100 (default: {DEFAULT_JPEGQUALITY})")
    
    args = parser.parse_args()

    # checks for .bsp extension (indicator that it is a valid map to convert)
    if not args.mappath.endswith(".bsp"):
        raise ValueError("ERROR: filename must end with '.bsp'")
    
    # create temporary filenames
    input_file = args.mappath.replace(".bsp", "_uncompressed.glb")
    output_file = input_file.replace("_uncompressed.glb", ".glb")
        
    gltf = GLTF2().load(input_file)

    if gltf.images:
        for idx, img in enumerate(gltf.images):
            data, mime = get_image_bytes(gltf, idx)
            if not data:
                print(f"Skip {img.name or f'image_{idx}'} (no data found)")
                continue

            try:
                new_bytes, new_name, new_mime, old_size, new_size = resize_and_compress(
                    data, img.name or f"image_{idx}", args.maxsize, args.quality
                )
                replace_image_bytes(gltf, idx, new_bytes, new_mime)
                img.name = new_name
                left = f"- {new_name}:"
                new=f"{new_size[0]}x{new_size[1]}"
                old=f"{old_size[0]}x{old_size[1]}"
                old = old.strip("()").replace(", ", "x")
                new = new.strip("()").replace(", ", "x")
                
                
                print(f"{left:<{40}}{old} → {new}")
            except Exception as e:
                print(f"Error at {img.name or f'image_{idx}'}: {e}")

    gltf.save_binary(output_file)
    print(f"- Compressed GLB saved as {output_file}")


if __name__ == "__main__":
    main()
