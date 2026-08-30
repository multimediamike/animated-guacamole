#!/usr/bin/python

import commands
import glob
import multiprocessing
import os
import sys

FFMPEG = "/home/melanson/mydir/ffmpeg/build-complete/ffmpeg"

def encode(command):
    (status, output) = commands.getstatusoutput(command)
    return (status, command)

if __name__ == "__main__":
    # verify arguments
    if len(sys.argv) < 6:
        print("USAGE: rips-to-audiobook.py <base input path> <output path> <book title> <book author> <file base name>")
        sys.exit(1)
    base_input_path = sys.argv[1]
    output_path = sys.argv[2]
    book_title = sys.argv[3]
    book_author = sys.argv[4]
    file_base_name = sys.argv[5]

    # verify that the FFmpeg build is available
    if not os.path.exists(FFMPEG):
        print("'%s' is not present" % (FFMPEG))
        sys.exit(1)

    # verify that the output directory already exists
    if not os.path.exists(output_path):
        print("Output path does not exist: ") + output_path
        sys.exit(1)

    # search for "discN" directories
    disc_count = 0
    while True:
        path = base_input_path + "/disc" + str(disc_count + 1)
        if os.path.isdir(path):
            disc_count += 1
        else:
            break

    if not disc_count:
        print("Could not find any 'discN' subdirectories in ") + base_input_path
        sys.exit(1)

    # enumerate the files to be encoded
    track_number = 1
    ffmpeg_commands = []
    for i in range(disc_count):
        tracks = sorted(glob.glob(base_input_path + "/disc" + str(i + 1) + "/track*.wav"))
        for j in range(len(tracks)):
            output_filename = "%s/%s-disc-%02d-ch-%02d.mp3" % (output_path, file_base_name, i+1, j+1)
            command = "%s -loglevel panic -y -i %s -codec:a libmp3lame -qscale:a 8 -metadata artist=\"%s\" -metadata album=\"%s\" -metadata title=\"%s\" -metadata genre=\"Audiobooks\" %s" % (FFMPEG, tracks[j], book_author, book_title, book_title, output_filename)
            ffmpeg_commands.append(command)

    # parallelize the encoding process
    pool = multiprocessing.Pool()
    it = pool.imap_unordered(encode, ffmpeg_commands)
    try:
        while True:
            result = it.next()
            print(result)
    except StopIteration:
        pass
        
