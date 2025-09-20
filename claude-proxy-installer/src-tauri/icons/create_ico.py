#!/usr/bin/env python3
"""Create a basic ICO file for Windows builds."""
import struct

# Create a minimal 16x16 ICO file with blue background and white square
def create_basic_ico():
    # ICO header (6 bytes)
    ico_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type (1=ICO), Count

    # ICO directory entry (16 bytes)
    width, height = 16, 16
    colors = 0  # 0 = more than 256 colors
    reserved = 0
    planes = 1
    bits_per_pixel = 32
    image_size = width * height * 4 + 40  # RGBA + BMP header
    image_offset = 22  # 6 + 16 = 22 bytes

    ico_dir_entry = struct.pack('<BBBBHHLL', width, height, colors, reserved,
                               planes, bits_per_pixel, image_size, image_offset)

    # BMP header (40 bytes)
    bmp_header = struct.pack('<LLLHHLLLLLL', 40, width, height*2, 1, bits_per_pixel,
                            0, width*height*4, 0, 0, 0, 0)

    # Create 16x16 RGBA pixel data (blue background, white center square)
    pixels = []
    for y in range(height):
        for x in range(width):
            if 4 <= x <= 11 and 4 <= y <= 11:
                # White square in center
                pixels.extend([255, 255, 255, 255])  # BGRA
            else:
                # Blue background
                pixels.extend([255, 0, 0, 255])  # BGRA (Blue)

    # Write ICO file
    with open('icon.ico', 'wb') as f:
        f.write(ico_header)
        f.write(ico_dir_entry)
        f.write(bmp_header)
        f.write(bytes(pixels))

    print("Created basic icon.ico file")

if __name__ == '__main__':
    create_basic_ico()