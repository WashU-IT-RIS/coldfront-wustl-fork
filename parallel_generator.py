import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
import argparse

def _process_path(result):
    result = result.replace("\\", "\\\\")
    result = result.replace("@", "\\@")
    result = result.replace("=", "\\=")
    result = result.replace(";", "\\;")
    result = result.replace("~", "\\~")
    result = result.replace("$", "\\$")
    result = result.replace("(", "\\(")
    result = result.replace(")", "\\)")
    result = result.replace("'", "\\'")
    result = result.replace(" ", "\\ ")
    result = result.replace("&", "\\&")
    return result

def walk_directory(directory):
    for root, dirs, files in os.walk(directory):
        for name in files:
            abs_path = os.path.join(root, name)
            processed_path = _process_path(abs_path)
            yield processed_path, 'file'
        for name in dirs:
            abs_path = os.path.join(root, name)
            processed_path = _process_path(abs_path)
            yield processed_path, 'directory'

def set_acl(path, file_spec, folder_spec, path_type):
    if path_type == 'file':
        spec = file_spec
    elif path_type == 'directory':
        spec = folder_spec
    else:
        print(f'Invalid path type: {path_type} for path: {path}')
        return
    command = f'nfs4_setfacl -S {spec} {path}'
    try:
        subprocess.run(command, check=True, shell=True)
        # print(f"Should run command: {command}")
    except subprocess.CalledProcessError as e:
        print(f'Failed to set ACL for {path_type}: {path}, Error: {e}')

def main(directory, num_workers, file_spec, folder_spec):
    set_acl(directory, file_spec, folder_spec, 'directory')
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        count = 0
        for path, path_type in walk_directory(directory):
            if count % 1000 == 0:
                # print(f'Number pending tasks: {executor._work_queue.qsize()}')
                print(f'Processed {count} paths')
            count += 1
            executor.submit(set_acl, path, file_spec, folder_spec, path_type)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Set ACLs for files and directories recursively.')
    parser.add_argument('directory', type=str, help='The directory to walk through.')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads.')
    parser.add_argument('--file-spec', type=str, required=True, help='ACL specification for files.')
    parser.add_argument('--folder-spec', type=str, required=True, help='ACL specification for folders.')

    args = parser.parse_args()
    failed_acls = []
    main(args.directory, args.workers, args.file_spec, args.folder_spec)