#!/usr/bin/python

import subprocess
import glob
import multiprocessing
import os
import sys

def encode(command):
    (status, output) = subprocess.getstatusoutput(command)
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
    FFMPEG = os.getenv("FFMPEG", "ffmpeg")
    (status, output) = subprocess.getstatusoutput(FFMPEG + " --help")
    if status != 0:
        print("'%s' could not be executed\nreturn status = %d, message:\n%s" % (FFMPEG, status, output))
        sys.exit(1)

    # verify that the output directory already exists
    if not os.path.exists(output_path):
        print("Output path does not exist: " + output_path)
        sys.exit(1)

    # search for "disc-NN" directories
    disc_count = 0
    disc_dirs = []
    while True:
        path = base_input_path + "/disc-%02d" % (disc_count + 1)
        if os.path.isdir(path):
            disc_count += 1
            disc_dirs.append(path)
        else:
            break

    if not disc_count:
        print("Could not find any 'disc-NN' subdirectories in " + base_input_path)
        sys.exit(1)

    # enumerate the files to be encoded
    sorted_disc_dirs = sorted(disc_dirs)
    track_number = 1
    ffmpeg_commands = []
    disc_number = 1
    for disc_dir in sorted_disc_dirs:
        tracks = sorted(glob.glob(disc_dir + "/track*.wav"))
        for j in range(len(tracks)):
            output_filename = "%s/%s-disc-%02d-ch-%02d.mp3" % (output_path, file_base_name, disc_number, j+1)
            command = "%s -loglevel panic -y -i %s -codec:a libmp3lame -qscale:a 8 -metadata artist=\"%s\" -metadata album=\"%s\" -metadata title=\"%s\" -metadata genre=\"Audiobooks\" %s" % (FFMPEG, tracks[j], book_author, book_title, book_title, output_filename)
            ffmpeg_commands.append(command)
        disc_number += 1

    # parallelize the encoding process
    num_workers = os.cpu_count()
    print("Performing %d track compression operations in parallel with %d processes..." % (len(ffmpeg_commands), num_workers))
    pool = multiprocessing.Pool(processes=num_workers)
    it = pool.imap_unordered(encode, ffmpeg_commands)
    try:
        while True:
            result = it.next()
            print(result)
    except StopIteration:
        pass
