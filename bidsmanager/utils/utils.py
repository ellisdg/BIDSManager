import filecmp
import shutil
import os


def update_file(old_file, new_file, move=False):
    if not os.path.exists(new_file) or not filecmp.cmp(old_file, new_file):
        copy_or_move(old_file, new_file, move=move)


def copy_or_move(in_file, out_file, move=False):
    if move:
        shutil.move(in_file, out_file)
    else:
        shutil.copy(in_file, out_file)
