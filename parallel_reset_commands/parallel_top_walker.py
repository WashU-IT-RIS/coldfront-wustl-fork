import os

import concurrent.futures

def walk_directory(root):
    all_paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            all_paths.append(os.path.join(dirpath, filename))
            # print(os.path.join(dirpath, filename))
    return all_paths

def find_subdirectories_helper(root, depth):
    subdirs = []
    for dirpath, dirnames, _ in os.walk(root):
        current_depth = dirpath[len(root):].count(os.sep)
        if current_depth == depth:
            subdirs.extend([os.path.join(dirpath, d) for d in dirnames])
        elif current_depth > depth:
            break
    return subdirs

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

def main(root, depth):
    subdirs = find_subdirectories_helper(root, depth)
    print(f"Initial subdirs: {subdirs}")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(walk_directory, subdir) for subdir in subdirs]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    target = '/storage2/fs1/prewitt_test/Active'
    sub_dir_threshold = 4
    # find threshold depth
    result = count_directories_at_depth(target, sub_dir_threshold)
    if result:
        depth, count_at_depth, sub_dirs_at_depth = result
        print(f"Threshold reached at depth {depth} subdir_count {count_at_depth} subdir_list {sub_dirs_at_depth}")
    else:
        print(f"Threshold not reached at depth {sub_dir_threshold}")
