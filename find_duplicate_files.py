#!/usr/bin/env python3
from argparse import ArgumentParser
from os import walk, stat, getcwd
from os.path import join, getsize, islink, abspath
from hashlib import md5
from json import dumps
from time import time

def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--path', '-p', type=str)
    return parser.parse_args()


def scan_files(whatever_directory):
    file_path_names = []
    for root, dirs, files in walk(whatever_directory):
        for file_name in files:
            if islink(join(root, file_name)):
                continue
            file_path_names.append(abspath(join(root, file_name)))
    return sorted(file_path_names)


def get_file_checksum(file_path):
    try:
        with open(file_path, 'rb') as file:
            return md5(file.read()).hexdigest()
    except (PermissionError, FileNotFoundError):  # OSError
        return None


def group_files(file_path_names, function):
    groups = {}
    for file_path in file_path_names:
        file_check = function(file_path)
        if file_check:
            groups.setdefault(file_check, []).append(file_path)
    return [group for group in groups.values() if len(group) > 1]


def group_files_by_checksum(file_path_names):
    return group_files(file_path_names, get_file_checksum)


def group_files_by_size(file_path_names):
    return group_files(file_path_names, getsize)


def find_duplicate_files(file_path_names):
    groups = []
    for i in group_files_by_size(file_path_names):
        groups += group_files_by_checksum(i)
    return groups


def deep_compare_two_files(file_path1, file_path2):
    read_size = 4*1024
    with open(file_path1, 'rb') as f1, open(file_path2, 'rb') as f2:
        while True:
            b1 = f1.read(read_size)
            b2 = f2.read(read_size)
            if b1 != b2:
                return False
            if not b1:
                return True


def group_files_by_LCS(same_size_files):
    groups = []
    while same_size_files:
        current_file = same_size_files.pop(0)
        same_files = [current_file]
        for file in same_size_files:
            if deep_compare_two_files(current_file, file):
                same_files.append(file)
        for file in same_files[1:]:
            same_size_files.remove(file)
        groups.append(same_files)
    return groups


def print_result(result):
    print(dumps(result, separators=(',\n', '')))


def main():
    args = get_parser()
    file_path_names = scan_files(args.path)
    t1 = time()
    print_result(find_duplicate_files(file_path_names))
    print(time()-t1)
    t2 = time()
    print_result(group_files_by_LCS(file_path_names))
    print(time()-t2)

if __name__ == '__main__':
    main()
