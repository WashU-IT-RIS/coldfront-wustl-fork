
import os

class DirectoryWalker:
    def __init__(self):
        pass
    
    def walk_recursive(self, directory, verbose: bool = False):
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
                print(f"Yielding file: {next_path}")
                yield next_path, 'file'
            for name in dirs:
                next_path = os.path.join(root, name)
                print(f"Yielding directory: {next_path}")
                yield next_path, 'directory'