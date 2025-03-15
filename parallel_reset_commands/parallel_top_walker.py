import os

import concurrent.futures

from collections import deque

# def walk_directory(root):
#     all_paths = []
#     for dirpath, dirnames, filenames in os.walk(root):
#         for filename in filenames:
#             all_paths.append(os.path.join(dirpath, filename))
#             # print(os.path.join(dirpath, filename))
#     return all_paths

# def find_subdirectories_helper(root, depth):
#     subdirs = []
#     for dirpath, dirnames, _ in os.walk(root):
#         current_depth = dirpath[len(root):].count(os.sep)
#         if current_depth == depth:
#             subdirs.extend([os.path.join(dirpath, d) for d in dirnames])
#         elif current_depth > depth:
#             break
#     return subdirs
def walk_directory_and_below(directory):
    verbose = False
    yield directory, 'directory'
    for root, dirs, files in os.walk(directory):
        if verbose:
            print(f'Processing directory: {root}')
            print(f"Root contains: {dirs} {files}")
        for name in files:
            next_path = os.path.join(root, name)
            # print(f"Yielding file: {next_path}")
            yield next_path, 'file'
        for name in dirs:
            next_path = os.path.join(root, name)
            # print(f"Yielding directory: {next_path}")
            yield next_path, 'directory'

def count_directories_at_depth(root, sub_dir_threshold):
    count = 0
    dirnames_found = []
    current_level_dirs = [root]
    reached_threshold = False
    depth = 0
    while not reached_threshold:
        next_level_dirs = []
        for dir in current_level_dirs:
            with os.scandir(dir) as it:
                for entry in it:
                    if entry.is_dir():
                        next_level_dirs.append(entry.path)
        if len(next_level_dirs) == 0:
            break
        current_level_dirs = next_level_dirs
        if len(current_level_dirs) >= sub_dir_threshold:
            reached_threshold = True
            break
        depth += 1
    if reached_threshold:
        count = len(current_level_dirs)
        dirnames_found = current_level_dirs
        return depth, count, dirnames_found
    return None

def walk_directory_with_scandir(root, max_depth):
    import pdb
    all_paths = []
    q = deque([root])
    depth_at_target = root.count(os.sep)
    # pdb.set_trace()
    while q:
        # pdb.set_trace()
        current_dir = q.pop()
        current_depth = current_dir.count(os.sep) - depth_at_target
        if current_depth > (max_depth + 1):
            # pdb.set_trace()
            break
        with os.scandir(current_dir) as it:
            for entry in it:
                if entry.is_dir():
                    # check if it is beyond the max depth
                    #if entry.path.count(os.sep) <= (max_depth - depth_at_target):
                    #    q.append(entry.path)
                    q.append(entry.path)
                all_paths.append(entry.path)
    return all_paths

# def main(root, depth):
#     subdirs = find_subdirectories_helper(root, depth)
#     print(f"Initial subdirs: {subdirs}")
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         futures = [executor.submit(walk_directory, subdir) for subdir in subdirs]
#         for future in concurrent.futures.as_completed(futures):
#             print(future.result())

if __name__ == "__main__":
    target = '/storage2/fs1/prewitt_test/Active'
    sub_dir_threshold = 10
    # find threshold depth
    result = count_directories_at_depth(target, sub_dir_threshold)
    import pdb
    # pdb.set_trace()
    if result:
        depth, count_at_depth, sub_dirs_at_depth = result

        # walk all the subdirs at that depth using walk_directory_and_below
        # in a for loop
        sub_dir_entries = []
        for subdir in sub_dirs_at_depth:
            for path, type in walk_directory_and_below(subdir):
                sub_dir_entries.append(path)
        top_level_entries = walk_directory_with_scandir(target, depth+1)

        check_entries = []
        for path, type in walk_directory_and_below(target):
            check_entries.append(path)

        combined_entries = set(sub_dir_entries).union(set(top_level_entries))

        check_entries = set(check_entries)
        missing_entries = check_entries.difference(combined_entries)
        pdb.set_trace()
        print(f"Threshold reached at depth {depth} subdir_count {count_at_depth} subdir_list {sub_dirs_at_depth}")
    else:
        print(f"Threshold not reached at depth {sub_dir_threshold}")
