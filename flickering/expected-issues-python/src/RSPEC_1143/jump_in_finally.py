def bad_break():
    for i in range(10):
        try:
            return i / 0
        finally:
            break # Noncompliant
    return 21

def bad_continue():
    for i in range(10):
        try:
            return i / 0
        finally:
            continue # Noncompliant
    return 21

def bad_return():
    try:
        return 3 / 0
    finally:
        return 42 # Noncompliant
    return 21

def ok():
    for i in range(10):
        try:
            return i / 0
        finally:
            for k in range(10):
                break
            for l in range(10):
                continue
            def foo():
                return
    return 21

def find_file_which_contains(expected_content, paths):
    file = None
    for path in paths:
        try:
            # "open" will raise IsADirectoryError if the provided path is a directory but it will be stopped by the  "return" and "continue"
            file = open(path, 'r')
            actual_content = file.read()
        except FileNotFoundError as exception:
            # This exception will never pass the "finally" block because of "return" and "continue"
            raise ValueError(f"'paths' should only contain existing files. File ${path} does not exist.")
        finally:
            file.close()
            if actual_content != expected_content:
                # Note that "continue" is allowed in a "finally" block only since python 3.8
                continue  # Noncompliant. This will prevent exceptions raised by the "try" block and "except" block from raising.
            else:
                return path # Noncompliant. Same as for "continue"
    return None

# This will return None instead of raising ValueError from the "except" block
find_file_which_contains("some content", ["file_which_does_not_exist"])

# This will return None instead of raising IsADirectoryError from the "try" block
find_file_which_contains("some content", ["a_directory"])

import sys

while True:
    try:
        sys.exit(1)
    except (SystemExit) as e:
        print("Exiting")
        raise
    finally:
        break  # This will prevent SystemExit from raising


import logging

def continue_whatever_happens_noncompliant():
    for i in range(10):
        try:
            raise ValueError()
        finally:
            continue  # Noncompliant


def continue_whatever_happens_compliant():
    for i in range(10):
        try:
            raise ValueError()
        except Exception:
            logging.exception("Failed")