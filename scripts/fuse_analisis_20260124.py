#!/usr/bin/env python3
import argparse
import glob
import os
import sys


def count_lines(path):
    with open(path, 'rb') as f:
        return sum(1 for _ in f)


def main(pattern, files, output):
    file_list = files if files else sorted(glob.glob(pattern))
    # exclude the output file if it matches the pattern
    out_abspath = os.path.abspath(output)
    file_list = [f for f in file_list if os.path.abspath(f) != out_abspath]
    if not file_list:
        print(f"No se encontraron archivos para patrón: {pattern}", file=sys.stderr)
        sys.exit(2)

    per_file_lines = []
    total_data_rows = 0

    with open(output, 'w', encoding='utf-8', newline='') as out:
        for idx, p in enumerate(file_list):
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            per_file_lines.append((p, len(lines)))
            if not lines:
                continue
            header = lines[0].rstrip('\n')
            data_lines = lines[1:]
            if idx == 0:
                out.write(header + '\n')
            for dl in data_lines:
                out.write(dl.rstrip('\n') + '\n')
            total_data_rows += len(data_lines)

    # summary
    for p, c in per_file_lines:
        print(f"{c}\t{p}")
    merged_lines = 1 + total_data_rows
    print(f"Merged file: {output} -> {merged_lines} lines (including header)")
    print(f"Total source lines: {sum(c for _,c in per_file_lines)}")
    print(f"Data rows written (excluding header): {total_data_rows}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fuse CSV files with same header into one file')
    parser.add_argument('--pattern', default='analisis_mercados_20260124_*.csv', help='Glob pattern to match source CSVs')
    parser.add_argument('--output', default='analisis_mercados_20260124_fusionado.csv', help='Output CSV path')
    parser.add_argument('files', nargs='*', help='Optional explicit list of files to merge')
    args = parser.parse_args()
    files = args.files if args.files else None
    main(args.pattern, files, args.output)
