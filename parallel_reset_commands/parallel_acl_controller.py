import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from directory_walker import DirectoryWalker

from acl_spec_builder import ACL_SpecBuilder

from argument_parser import ArgumentParser

from typing import List


def process_path(result):
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
    result = result.replace(".", "\\.")
    result = result.replace("`", "\\`")
    return result

def check_acl(original_path, processed_path, expected_spec):
    if os.path.islink(original_path):
        # links don't have ACLs
        return True
    # NOTE: prefixing 'sudo' results in different behavior
    # even though the whole script is run as `sudo` and that
    # elevated status *should* be inherited by the spawned
    # subprocesses
    # getfacl_command = f"sudo nfs4_getfacl {processed_path}"
    getfacl_command = f"nfs4_getfacl {processed_path}"
    try:
        result = subprocess.check_output(getfacl_command, shell=True)
        acl_info = str(result, 'utf-8')
        import pdb
        pdb.set_trace()
    except subprocess.CalledProcessError as e:
        return False
        # print(f'Failed to get ACL: {path}, Error: {e}')

def set_acl(path: str, path_type: str, builder: ACL_SpecBuilder) -> bool:
    print(f"Setting ACL for {path_type}: {path}")
    if os.path.islink(path):
        print(f"Skipping link: {path}")
        return
    print(f"Calling process_path on {path}")
    processed_path = process_path(path)
    print(f"Processed path: {processed_path}")
    # import pdb
    # pdb.set_trace()
    spec = builder.get_spec_by_path(path, path_type)
    print(f"Spec: {spec}")
    command = f'nfs4_setfacl -s "{spec}" {processed_path}'
    print(f"Command: {command}")
    try:
        subprocess.run(command, check=True, shell=True)
        # print(f"Should run command: {command}")
    except subprocess.CalledProcessError as e:
        print(f'Failed to set ACL for {path_type}: {path}, Error: {e}')

    check_acl(path, processed_path, spec)


def reset_acls_recursive(target_directory: str, num_workers: int, alloc_name: str, sub_alloc_names: List[str]):
    print(f"Resetting ACLs recursively in {target_directory} with {num_workers} workers.")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        walker = DirectoryWalker()
        builder = ACL_SpecBuilder()
        builder.build_specs(alloc_name, sub_alloc_names)
        count = 0
        for path, path_type in walker.walk_recursive(target_directory):
            if count % 1000 == 0:
                # print(f'Number pending tasks: {executor._work_queue.qsize()}')
                print(f'Processed {count} paths')
            count += 1
            # executor.submit(set_acl, path, path_type, builder)
            set_acl(path, path_type, builder)



def main():
    # get the arguments from the user using ArgumentParser
    parser = ArgumentParser()
    parser.retrieve_args()


    # at this point, I think I can call the reset_acls_recursive function
    reset_acls_recursive(
        parser.get_target_dir(),
        parser.get_num_workers(),
        parser.get_allocation_name(),
        parser.get_sub_allocations()
    )


if __name__ == "__main__":
    main()