#!/usr/bin/env python3
from argparse import ArgumentParser
from os import walk
from os.path import join, getsize, islink, abspath
from hashlib import md5
from json import dumps
from typing import Callable


def get_parser():
    '''
    get arguments and sub-commands from command-line
    '''
    parser = ArgumentParser(prog='Duplicate Files Finder')
    parser.add_argument('--path', '-p', type=str, required=True,
                        help='specify the absolute path where to find '
                             'duplicate files')
    parser.add_argument('--faster_algo', '-a', action='store_true',
                        help='use another method to find duplicate files')
    return parser.parse_args()


def scan_files(directory_path):
    '''
    scan all files in directory and returns a flat list of files,
    ignore symbolic links
    @param directory_path: a specified path of directory
    @return: a sorted list of all absolute file paths
    '''
    # check input
    if not isinstance(directory_path, str):
        raise TypeError('directory_path must be a string')
    file_path_names = []
    for root, dirs, files in walk(directory_path):
        for file_name in files:
            if islink(join(root, file_name)):
                continue
            file_path_names.append(abspath(join(root, file_name)))
    return sorted(file_path_names)


def get_file_hash(file_path):
    '''
    Generate a Hash Value for a file
    @param file_path: absolute path of a file
    @return: - a 128-bit hash value, a compact digital fingerprint of a file
             - None if there is I/O error occur in accessing the file,
               including “file not found” or “disk full”, 'PermissionError'...
    '''
    try:
        with open(file_path, 'rb') as file:
            return md5(file.read()).hexdigest()
    except OSError:
        return None


def group_files(file_path_names, get_feature_function):
    '''
    separate files to groups so that all files in a group will have
    same feature
    @param file_path_names : a sorted list of all absolute file paths in
                        considered directory
    @param get_feature_function: name of a function which can get the feature
                                of a file.
                                (examples: 'getsize', 'get_file_hash')
    @return: a list contains groups of same feature files,
            formed [[file1, file2], [file3, file4]]
    '''
    if not isinstance(file_path_names, list):
        raise TypeError("file_path_names must be a list type object")
    if not isinstance(get_feature_function, Callable):
        raise TypeError("get_feature_function must be a callable function")
    # generate a dictionary formed:
    # {key=feature(size/hash value), value=[path_names]}
    groups_dict = {}
    for file_path in file_path_names:
        try:
            file_feature = get_feature_function(file_path)
        except OSError:
            file_feature = None
        if file_feature:
            groups_dict.setdefault(file_feature, []).append(file_path)
    return [group for group in groups_dict.values() if len(group) > 1]


def group_files_by_checksum(file_path_names):
    '''
    separate files to groups so that all files in a group will have
    same hash value
    @param file_path_names : a sorted list of all absolute file paths in
                        considered directory
    @return a list contains groups of same hash value files,
            formed [[file1, file2], [file3, file4]]
    '''
    # check input
    if not isinstance(file_path_names, list):
        raise TypeError("file_path_names must be a list type object")
    return group_files(file_path_names, get_file_hash)


def group_files_by_size(file_path_names):
    '''
    separate files to groups so that all files in a group will have
    same size
    @param file_path_names : a sorted list of all absolute file paths in
                        considered directory
    @return a list contains groups of same size files,
            formed [[file1, file2], [file3, file4]]
    '''
    # check input
    if not isinstance(file_path_names, list):
        raise TypeError("file_path_names must be a list type object")
    return group_files(file_path_names, getsize)


def deep_compare_two_files(file_path1, file_path2):
    '''
    check two file if they are same or not by reading and compare its content
    @param file_path1: the absolute path of file 1
    @param file_path2: the absolute path of file 2
    @return: - True: if two files are same
             - False: if two files are different of I/O error occured
    '''
    read_size = 4*1024
    try:
        with open(file_path1, 'rb') as f1, open(file_path2, 'rb') as f2:
            while True:
                content1 = f1.read(read_size)
                content2 = f2.read(read_size)
                if content1 != content2:
                    return False
                if not content1:
                    return True
    except OSError:
        return False


def get_same_files(current_file_path, list_of_file_paths):
    '''
    find all files in a list which be doublicated with particular file
    @param current_file_path: the absolute path of particular file
    @param list_of_file_paths: a sorted list of all absolute file paths in
                        considered directory
    @return: a list of doublicate files
    '''
    if not isinstance(current_file_path, str):
        raise TypeError('current_file_path must be a string')
    if not isinstance(list_of_file_paths, list):
        raise TypeError("list_of_file_paths must be a list type object")
    same_files = [current_file_path]
    for file_path in list_of_file_paths:
        if deep_compare_two_files(current_file_path, file_path):
            same_files.append(file_path)
    return same_files


def remove_same_elements(source_list, another_list):
    '''
    remove all elements in a source list if its contained in another list
    @param source_list: source list
    @param another_list: another list
    @return: None
    '''
    if not isinstance(source_list, list):
        raise TypeError("source_list must be a list type object")
    if not isinstance(another_list, list):
        raise TypeError("another_list must be a list type object")
    for element in source_list:
        if element in another_list:
            another_list.remove(element)


def group_files_by_read_content(file_path_names):
    '''
    separate files to groups so that all files in a group will have
    same content.
    @param file_path_names : a sorted list of all absolute file paths in
                        considered directory
    @return a list contains groups of same content files,
            formed [[file1, file2], [file3, file4]]
    '''
    if not isinstance(file_path_names, list):
        raise TypeError("file_path_names must be a list type object")
    groups_list = []
    while file_path_names:
        # find all files which doublicated with the first file in original list
        current_file = file_path_names.pop(0)
        same_files = get_same_files(current_file, file_path_names)
        remove_same_elements(same_files[1:], file_path_names)
        #  filter groups which has length = 1
        if len(same_files) > 1:
            groups_list.append(same_files)
    return groups_list


def find_duplicate_files(file_path_names, group_files_function):
    '''
    find all duplicate files in a directory and group them in a list
    @param file_path_names : a sorted list of all absolute file paths in
                        considered directory
    @param group_files_function: name of a function which can group files
                                 by the same feature.
                                 (examples: 'group_files_by_read_content',
                                 'group_files_by_checksum')
    @return groups: a list contains lists of duplicate files
    '''
    # check input
    if not isinstance(file_path_names, list):
        raise TypeError("file_path_names must be a list type object")
    if not isinstance(group_files_function, Callable):
        raise TypeError("group_files_function must be a callable function")
    groups = []
    for group in group_files_by_size(file_path_names):
        groups += group_files_function(group)
    return groups


def print_result(result_list):
    '''
    print the result of find duplicate files program
    @param result_list: a list contains lists of duplicate files
    @return None
    '''
    print(dumps(result_list, separators=(',\n', '')))


def main():
    args = get_parser()
    file_path_names = scan_files(args.path)
    if args.faster_algo:
        t1 = time()
        print_result(find_duplicate_files(file_path_names,
                                          group_files_by_read_content))
    else:
        print_result(find_duplicate_files(file_path_names,
                                          group_files_by_checksum))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass
