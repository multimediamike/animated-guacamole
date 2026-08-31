#!/usr/bin/python

import argparse
import glob
import multiprocessing
import os
import subprocess
import sys


def encode(command):
    (status, output) = subprocess.getstatusoutput(command)
    return (status, command)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a sequence of raw CD rips to a sequence of compressed files."
    )
    parser.add_argument(
        "--base-input-path",
        help="Path to the base input directory/file.",
    )
    parser.add_argument(
        "--output-path",
        help="Path to write output to.",
    )
    parser.add_argument(
        "--book-title",
        help="Title of the book.",
    )
    parser.add_argument(
        "--book-author",
        help="Author of the book.",
    )
    parser.add_argument(
        "--file-base-name",
        help="Base name to use for generated output files.",
    )
    parser.add_argument(
        "--encode-opus",
        action="store_true",
        help="If set, encode audio output using the Opus codec instead of MP3.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    base_input_path: str = args.base_input_path
    output_path: str = args.output_path
    book_title: str = args.book_title
    book_author: str = args.book_author
    file_base_name: str = args.file_base_name
    encode_opus: bool = args.encode_opus

    # verify that the FFmpeg build is available
    if args.encode_opus:
        OPUSENC = "opusenc"
        (status, output) = subprocess.getstatusoutput(OPUSENC + " --help")
        if status != 0:
            print("'%s' could not be executed\nreturn status = %d, message:\n%s" % (OPUSENC, status, output))
            sys.exit(1)
    else:
        FFMPEG = os.getenv("FFMPEG", "ffmpeg")
        (status, output) = subprocess.getstatusoutput(FFMPEG + " --help < /dev/null")
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
            output_filename = "%s/%s-disc-%02d-ch-%02d." % (output_path, file_base_name, disc_number, j+1)
            track_title = "Disc %d, track %d" % (disc_number, j+1)
            if args.encode_opus:
                output_filename += "opus"
                command = (
                    "%s --bitrate 40 --music --vbr "
                    "--artist \"%s\" --album \"%s\" --title \"%s\" "
                    "\"%s\" \"%s\""
                ) % (OPUSENC, book_author, book_title, track_title, tracks[j], output_filename)
            else:
                output_filename += "mp3"
                command = (
                    "%s -loglevel panic -y -i \"%s\" -codec:a libmp3lame -qscale:a 8 "
                    "-metadata artist=\"%s\" -metadata album=\"%s\" "
                    "-metadata title=\"%s\" -metadata genre=\"Audiobooks\" \"%s\" < /dev/null"
                ) % (FFMPEG, tracks[j], book_author, book_title, track_title, output_filename)
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


if __name__ == "__main__":
    main()
