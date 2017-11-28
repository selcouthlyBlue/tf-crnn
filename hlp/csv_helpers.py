#!/usr/bin/env python
__author__ = 'solivr'

import csv
import os
import argparse
from tqdm import tqdm, trange


def csv_rel2abs_path_converter(csv_files: str, csv_delimiter: str= ' ', csv_encoding='utf8') -> None:
    for filename in tqdm(csv_files):
        absolute_path, basename = os.path.split(os.path.abspath(filename))
        labels, relative_paths = get_labels_and_relative_paths(csv_delimiter, csv_encoding, filename)
        export_filename = os.path.join(absolute_path, '{}_abs{}'.format(*os.path.splitext(basename)))
        with open(export_filename, 'w', encoding=csv_encoding) as f:
            csv_writer = csv.writer(f, delimiter=csv_delimiter)
            for i in trange(0, len(relative_paths)):
                csv_writer.writerow([os.path.abspath(os.path.join(absolute_path, relative_paths[i])), labels[i]])


def get_labels_and_relative_paths(csv_delimiter, csv_encoding, filename):
    relative_paths = list()
    labels = list()
    with open(filename, 'r', encoding=csv_encoding) as f:
        csv_reader = csv.reader(f, delimiter=csv_delimiter)
        for row in csv_reader:
            relative_paths.append(row[0])
            labels.append(row[1])

    return labels, relative_paths


def csv_filtering_chars_from_labels(csv_filename: str, chars_to_remove: str,
                                    delimiter: str=' ', encoding='utf8') -> int:
    if not isinstance(chars_to_remove, list):
        chars_to_remove = list(chars_to_remove)

    paths = list()
    labels = list()
    n_deleted = 0
    with open(csv_filename, 'r', encoding=encoding) as file:
        csv_reader = csv.reader(file, delimiter=delimiter)
        for row in csv_reader:
            if not any((d in chars_to_remove) for d in row[1]):
                paths.append(row[0])
                labels.append(row[1])
            else:
                n_deleted += 1

    with open(csv_filename, 'w', encoding=encoding) as file:
        csv_writer = csv.writer(file, delimiter=delimiter)
        for i in tqdm(range(len(paths)), total=len(paths)):
            csv_writer.writerow([paths[i], labels[i]])

    return n_deleted


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_files', type=str, required=True, help='CSV filename to convert', nargs='*')
    parser.add_argument('-d', '--delimiter_char', type=str, help='CSV delimiter character', default=' ')

    args = vars(parser.parse_args())

    csv_filenames = args.get('input_files')

    csv_rel2abs_path_converter(csv_filenames, csv_delimiter=args.get('delimiter_char'))
