#!/usr/bin/env python3
import io
import os
import mimetypes
import tkinter as tk
from tkinter import filedialog, messagebox
from pygltflib import GLTF2, BufferView, Buffer
from PIL import Image

DEFAULT_MAXSIZE = 1024
DEFAULT_JPEGQUALITY = 90


def clean_image_name(name: str, mime: str) -> str:
    if not name:
        name = "image"

    known_exts = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".gif", ".webp", ".dds", ".ktx", ".ktx2"}
    base = os.path.basename(name)

    while True:
        root, ext = os.path.splitext(base)
        if ext.lower() in known_exts and root:
            base = root
        else:
            break

    if mime == "image/jpeg":
        ext = ".jpg"
    elif mime == "image/png":
        ext = ".png"
    else:
        ext = mimetypes.guess_extension(mime or "") or ".png"

    return base + ext


def get_image_bytes(gltf, img_idx):
    img = gltf.images[img_idx]

    if img.bufferView is not None and img.bufferView < len(gltf.bufferViews):
        bv = gltf.bufferViews[img.bufferView]
        blob = gltf.binary_blob()
        start = bv.byteOffset or 0
        end = start + bv.byteLength
        return blob[start:end], img.mimeType
    return None, None


def resize_and_compress(data: bytes, name: str, maxsize: int, jpegquality: int):
    with Image.open(io.BytesIO(data)) as img:
        orig_size = img.size
        w, h = img.size

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


# --- GUI ---
def run_gui():
    root = tk.Tk()
    root.title("GLB Texture Compressor")
    root.geometry("420x260")
    root.resizable(False, False)

    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select GLB File",
            filetypes=[("Binary glTF (.glb)", "*.glb")],
        )
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

    def process():
        input_file = entry_path.get().strip()
        if not os.path.isfile(input_file):
            messagebox.showerror("Error", "Please select a valid .glb file.")
            return

        try:
            maxsize = int(entry_maxsize.get())
            quality = int(entry_quality.get())
        except ValueError:
            messagebox.showerror("Error", "Max Size and Quality must be integers.")
            return

        output_file = input_file.replace(".glb", "#.glb")

        gltf = GLTF2().load(input_file)
        log_text.delete(1.0, tk.END)

        if gltf.images:
            for idx, img in enumerate(gltf.images):
                data, mime = get_image_bytes(gltf, idx)
                if not data:
                    log_text.insert(tk.END, f"Skip {img.name or f'image_{idx}'} (no data found)\n")
                    continue
                try:
                    new_bytes, new_name, new_mime, old_size, new_size = resize_and_compress(
                        data, img.name or f"image_{idx}", maxsize, quality
                    )
                    replace_image_bytes(gltf, idx, new_bytes, new_mime)
                    img.name = new_name
                    log_text.insert(
                        tk.END,
                        f"{new_name:30s} {old_size[0]}x{old_size[1]} → {new_size[0]}x{new_size[1]}\n"
                    )
                except Exception as e:
                    log_text.insert(tk.END, f"Error at {img.name or f'image_{idx}'}: {e}\n")

        gltf.save_binary(output_file)
        log_text.insert(tk.END, f"\nSaved as {output_file}")
        messagebox.showinfo("Done", f"Compressed GLB saved as:\n{output_file}")

    # Widgets
    tk.Label(root, text="Input GLB File:").pack(anchor="w", padx=10, pady=(10, 0))
    frame_path = tk.Frame(root)
    frame_path.pack(fill="x", padx=10)
    entry_path = tk.Entry(frame_path)
    entry_path.pack(side="left", fill="x", expand=True)
    tk.Button(frame_path, text="Browse", command=select_file).pack(side="right", padx=5)

    frame_opts = tk.Frame(root)
    frame_opts.pack(fill="x", padx=10, pady=10)
    tk.Label(frame_opts, text="Max Size:").grid(row=0, column=0, sticky="w")
    entry_maxsize = tk.Entry(frame_opts, width=8)
    entry_maxsize.insert(0, str(DEFAULT_MAXSIZE))
    entry_maxsize.grid(row=0, column=1, padx=5)
    tk.Label(frame_opts, text="JPEG Quality:").grid(row=0, column=2, padx=(20, 0))
    entry_quality = tk.Entry(frame_opts, width=5)
    entry_quality.insert(0, str(DEFAULT_JPEGQUALITY))
    entry_quality.grid(row=0, column=3, padx=5)

    tk.Button(root, text="Compress", command=process).pack(pady=5)

    log_text = tk.Text(root, height=8, width=60)
    log_text.pack(padx=10, pady=(0, 10))

    root.mainloop()


if __name__ == "__main__":
    run_gui()
