#!/usr/bin/env python
""" This module launches the files comparison process

This modules compares all txt, docs, odt, pdf files present in path specified as argument.
It writes results in a HTML table.
It uses difflib library to find matching sequences.
It can also use Jaccard Similarity, words counting, overlapping words for similarity

"""
import webbrowser
from datetime import datetime
from os import listdir, path
from typing import List

from tqdm import tqdm

from scripts.html_writing import (
    add_links_to_html_table,
    results_to_html,
    papers_comparison,
)
from scripts.html_utils import writing_results
from scripts.processing_files import file_extension_call
from scripts.similarity import difflib_overlap
from scripts.utils import wait_for_file, parse_options
from flask import Response, jsonify


class MinimumFilesError(Exception):
    """Raised when there are fewer than two files for comparison."""

    pass


class UnsupportedFileError(Exception):
    """Raised when there are unsupported files in the input directory."""

    pass


class PathNotFoundError(Exception):
    """Raised when the specified input directory path does not exist."""

    pass


def compare(
    target_file_path: str, source_dir: str, out_dir: str, block_size: int
) -> Response:

    if not path.isfile(target_file_path) or not target_file_path.endswith(
        ("txt", "pdf", "docx", "odt")
    ):
        return (
            jsonify({"error": "Invalid target file path or unsupported file type."}),
            400,
        )

    source_files = [
        f
        for f in listdir(source_dir)
        if path.isfile(path.join(source_dir, f))
        and f.endswith(("txt", "pdf", "docx", "odt"))
    ]

    if len(source_files) < 1:
        return (
            jsonify({"error": "At least one srouce file is required for comparison."}),
            400,
        )

    source_filenames, source_files_text = [], []
    target_file_name = path.basename(target_file_path)
    target_file_text = file_extension_call(target_file_path)

    for file in source_files:
        file_words = file_extension_call(str(path.join(source_dir, file)))
        if file_words:  # If all files have supported format
            source_files_text.append(file_words)
            source_filenames.append(file)
        else:
            raise UnsupportedFileError(
                "Remove files which are not txt, pdf, docx, or odt and run the script again."
            )
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    results_directory = writing_results(timestamp)

    difflib_scores: List[float] = [0.0 for _ in range(len(source_files_text))]
    file_ind = 0

    for i, source_text in enumerate(source_files_text):
        difflib_scores[i] = difflib_overlap(target_file_text, source_text)
        saved_path = papers_comparison(
            results_directory,
            file_ind,
            source_text,
            target_file_text,
            (source_filenames[i], target_file_name),
            block_size,
        )
        print(
            "Compared ",
            target_file_name,
            "with ",
            source_filenames[i],
            "\twith difflib score:",
            difflib_scores[i],
            "\t and saved to",
            saved_path,
        )
        file_ind += 1

    results_json = {
        "target_file": target_file_name,
        "source_files": [
            {
                "source_filename": source_filenames[i],
                "difflib_score": difflib_scores[i],
                "timestamp": timestamp,
                "index": i,
            }
            for i in range(len(source_filenames))
        ],
    }

    return jsonify(results_json)
