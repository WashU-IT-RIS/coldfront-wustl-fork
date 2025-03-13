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

def count_directories_at_depth(root, depth):
    count = 0
    dirnames_found = []
    for dirpath, dirnames, _ in os.walk(root):
        current_depth = dirpath[len(root):].count(os.sep)
        if current_depth == depth:
            count += len(dirnames)
            dirnames_found.extend(dirnames)
        # elif current_depth > depth:
        #     break
    return count, dirnames_found

def main(root, depth):
    subdirs = find_subdirectories_helper(root, depth)
    print(f"Initial subdirs: {subdirs}")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(walk_directory, subdir) for subdir in subdirs]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    target = '/storage2/fs1/prewitt_test/Active'
    for i in range(4):
        print(f"Depth {i}: {count_directories_at_depth(target, i)}")