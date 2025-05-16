import os

from collections import deque

def walk_recursive_from_target(directory, verbose: bool = False):
    # jprew - NOTE - the walk seems to be missing the top level directory
    # need to fix
    if verbose:
        print(f'Processing directory starting at: {directory}')
    
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

def walk_to_max_depth(target, max_depth):
    q = deque([target])
    depth_at_target = target.count(os.sep)
    yield target, 'directory'
    while q:
        current_dir = q.pop()
        with os.scandir(current_dir) as it:
            for entry in it:
                file_dir_type = 'file'
                if entry.is_dir():
                    file_dir_type = 'directory'
                    # check if it is less than max_depth + depth_at_target
                    # if so, add to processing queue
                    if entry.path.count(os.sep) <= (max_depth + depth_at_target):
                        q.append(entry.path)
                yield entry.path, file_dir_type

def find_depth_for_target_dirs(root, sub_dir_threshold):
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