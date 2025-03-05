
import os

class DirectoryWalker:
    def __init__(self):
        pass
    
    def walk_recursive(self, directory, verbose: bool = False):
        if verbose:
            print(f'Processing directory starting at: {directory}')
        for root, dirs, files in os.walk(directory):
            if verbose:
                print(f'Processing directory: {root}')
                print(f"Root contains: {dirs} {files}")
            for name in files:
                next_path = os.path.join(root, name)
                yield next_path, 'file'
            for name in dirs:
                next_path = os.path.join(root, name)
                yield next_path, 'directory'