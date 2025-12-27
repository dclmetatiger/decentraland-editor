import argparse
import math
import os

parser = argparse.ArgumentParser(description="Scales and Rotates a Wavefront OBJ file based on a .bsp path")

parser.add_argument("mappath", type=str, help="Path to the .bsp file")
parser.add_argument("scale", type=float, help="Scale factor")
parser.add_argument("rotate", type=float, help="Rotation in degrees")

args = parser.parse_args()

if not args.mappath.endswith(".bsp"):
    raise ValueError("ERROR: filename must end with '.bsp'")

input_file = args.mappath.replace(".bsp", ".obj")
output_file = args.mappath.replace(".bsp", "_scaled.obj")

def scale_and_rotate_obj(input_file, output_file, scale_factor, rotation_degrees):
    theta = math.radians(rotation_degrees)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
        for line in f_in:
            if line.startswith("v "):
                parts = line.split()
                x = float(parts[1]) * scale_factor
                y = float(parts[2]) * scale_factor
                z = float(parts[3]) * scale_factor

                # Rotate around Y axis
                x_rot = x * cos_theta + z * sin_theta
                z_rot = -x * sin_theta + z * cos_theta

                f_out.write(f"v {x_rot} {y} {z_rot}\n")
            else:
                f_out.write(line)

scale_and_rotate_obj(input_file, output_file, args.scale, args.rotate)
print(f"- Input:  {input_file}")
print(f"- Output: {output_file}")
