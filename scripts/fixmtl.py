import os
import argparse

parser = argparse.ArgumentParser(description="Rewrites texture paths in MTL file")
parser.add_argument("mappath", type=str, help="Path to the .bsp file")
args = parser.parse_args()

if not args.mappath.endswith(".bsp"):
    raise ValueError("ERROR: filename must end with '.bsp'")

mtl_file = args.mappath.replace(".bsp", ".mtl")

base_path = mtl_file.split(r"/maps/")[0]

with open(mtl_file, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith("map_Kd") and "../" in line:
        parts = line.split("../", 1)
        new_path = os.path.join(base_path, parts[1])#.replace("/", "\\"))
        print(new_path)

        new_line = f"map_Kd {new_path}\n"
        new_lines.append(new_line)
    else:
        new_lines.append(line)

with open(mtl_file, "w") as f:
    f.writelines(new_lines)

print("- MTL texture paths fixed.")