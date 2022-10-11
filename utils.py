import asyncio
import csv
import ctypes
import os
import re
import shutil

from fsplit.filesplit import Filesplit

# 524288000 500Mb
# 2097152000 2Gb
MAX_FILE_SIZE = 524288000


def separate_string(line):
    """ This func splits the string into 'sub-strings' by using 'commas' as trigger for splitting.
        It also deletes space at the beginning and at the end of the new split sub-string.
    """
    line = line.split(",")
    return [x.strip() for x in line]


def directory_mode(path):
    """ Find all files in the directory and subdirectories
    """
    name_files = []

    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            name_files.append(os.path.join(root, name))
        for name in dirs:
            name_files.append(os.path.join(root, name))

    return name_files


def async_to_sync(method):
    """Synchronizes functions.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return method
    else:
        return loop.run_until_complete(method)


def phone_match(value):
    """Checks if the phone number was entered correctly.
    """
    match = re.match(r'\+?[0-9.()\[\] \-]+', value)
    if match is None:
        raise ValueError('{} is not a valid phone'.format(value))
    return value


def empty_disk_space(directories, size):
    """Checks for free disk(s) space to download files.
    """
    disks = {}

    for directory in directories:
        if not directory[:2] in disks:
            disks[directory[:2]] = size
        else:
            disks[directory[:2]] += size

    for key in disks:
        if disks.get(key) > shutil.disk_usage(key)[2]:
            return False
    return True


def split_big_file(file):
    """ Splits a large file into smaller files.
        The size is determined by the parameter MAX_FILE_SIZE.
    """
    fs = Filesplit()

    path = "{}\\{}".format(os.path.dirname(os.path.abspath(__file__)), "upload")
    if not os.path.exists(path):
        os.mkdir(path)
    ctypes.windll.kernel32.SetFileAttributesW(path, 2)

    fs.split(file, split_size=MAX_FILE_SIZE, output_dir=path)

    os.rename(path + "\\fs_manifest.csv", path + "\\fs_manifest_" + os.path.basename(file).split('.')[0] + ".csv")
    return path


def join_big_file(path, manifest, directory):
    """ Join a large file that has been split into smaller ones.
    :param path: path to the directory where the pieces of the file are stored
    :param manifest: partition information file
    :param directory: path to the folder for storing the large file
    """
    fs = Filesplit()
    fs.merge(input_dir=path, manifest_file=manifest, cleanup=True)

    file = directory_mode(path)
    shutil.move(file[0], os.path.join(directory, os.path.basename(file[0])))

    os.rmdir(path)


def get_parts_filenames(file):
    """ Find out what chunks a file is made of.
    """
    output = []

    with open(file) as f_obj:
        reader = csv.reader(f_obj)
        for row in reader:
            if len(row) > 0:
                output.append(row[0])

    return output[1:]


def clear_directory(path):
    """ Сleans up the directory.
    """
    shutil.rmtree(path, ignore_errors=True)
