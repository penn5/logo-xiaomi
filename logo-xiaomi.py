#    Xiaomi logo.img Extractor
#    Copyright (C) <year>  <name of author>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

HEADER = b'LOGO!!!!'
BMP_HEADER = b'BM'

from struct import *
import argparse, os

def check_header(f):
    f.seek(0x4000)
    (header,) = unpack("<8s", f.read(8))
    if header != HEADER:
        print("wrong header", header)
        raise ValueError("Wrong Header")

def get_offsets(f):
    img_offset = 0
    img_offsets = []
    f.seek(0x4008)

    while True:
        last_offset = img_offset
        (img_offset,) = unpack("<I", f.read(4))
        if img_offset == 0:
            break
        else:
            if (img_offset + last_offset) * 0x1000 in img_offsets:
                # Sometimes they show up twice. Skip.
                continue
            img_offsets.append((img_offset + last_offset) * 0x1000)
    # The last one is the end of the file. Skip.
    img_offsets.pop()
    return img_offsets

def extract(f):
    check_header(f)

    img_offsets = get_offsets(f)

    # Formatted as BMP. Detect file length
    img_cnt = 0
    for img_offset in img_offsets:
        img_cnt += 1
        f.seek(img_offset)
        (header, size) = unpack("<2sI", f.read(6))
        if header != BMP_HEADER:
            print('corrupt bmp header skipping')
            continue
        f.seek(img_offset)
        yield f.read(size)

def edit(orig_imgs, new_imgs):
    binary = bytearray(orig_imgs.read())
    check_header(orig_imgs)

    img_offsets = get_offsets(orig_imgs)

    if len(img_offsets) != len(new_imgs):
        raise ValueError("All images must be replaced")

    # Formatted as BMP. Detect file length
    img_cnt = 0
    lens = []
    for img_offset in img_offsets:
        (header, size) = unpack("<2sI", binary[img_offset:img_offset+6])
        if header != BMP_HEADER:
            print('corrupt bmp header skipping')
            continue
        next_img = img_offsets[img_cnt+1]-1 if img_cnt+1 < len(img_offsets) else len(binary)
        if len(new_imgs[img_cnt])+img_offset >= next_img:
            print(next_img, len(new_imgs[img_cnt]), img_offset)
            raise ValueError("Image too big; data overlaps with next image")
        (header, size) = unpack("<2sI", new_imgs[img_cnt][:6])
        if header != BMP_HEADER:
            raise ValueError('cannot add corrupt bmp header')
        if size != len(new_imgs[img_cnt]):
            raise ValueError("Won't add image that lies about size, who knows what would happen")

        # Safety checks passed
        binary[img_offset:img_offset+size] = new_imgs[img_cnt]

        img_cnt += 1

    return binary

def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required=True)

    parser_extract = subparsers.add_parser("extract")
    parser_extract.add_argument("-i", "--input", dest='input', action='store', type=argparse.FileType('rb'), required=True)
    parser_extract.add_argument("-o", "--output", dest='output', action='store', type=str, required=True)
    parser_extract.set_defaults(func=extract_logo)

    parser_replace = subparsers.add_parser("replace")
    parser_replace.add_argument("-i", "--input", dest='input', action='store', type=argparse.FileType('rb'), required=True)
    parser_replace.add_argument("-a", "--image", dest='images', action='append', type=argparse.FileType('rb'), required=True)
    parser_replace.add_argument("-o", "--output", dest='output', action='store', type=argparse.FileType('wb'), required=True)
    parser_replace.set_defaults(func=replace_logo)
    args = parser.parse_args()
    if hasattr(args, "images"):
        print(args.func(args.input, args.images, args.output))
    else:
        print(args.func(args.input, args.output))
def extract_logo(input, output):
    os.makedirs(output, exist_ok=True)
    c = 0
    for photo in extract(input):
        f = open(os.path.join(output, "logo-"+str(c)+".bmp"), "wb")
        f.write(photo)
        f.close()
        c += 1

def replace_logo(input, images, output):
    out = edit(input, [i.read() for i in images])
    output.write(out)
    output.close()

if __name__ == "__main__":
    main()
