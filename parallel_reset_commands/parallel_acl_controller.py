import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from directory_walker import DirectoryWalker

from acl_spec_builder import ACL_SpecBuilder

from argument_parser import ArgumentParser

from typing import List


def process_path(self, result):
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

def set_acl(path: str, path_type: str, builder: ACL_SpecBuilder):
    if os.path.islink(path):
        return
    path = process_path(path)
    spec = builder.get_spec_by_path(path)
    command = f'nfs4_setfacl -s {spec} {path}'
    try:
        subprocess.run(command, check=True, shell=True)
        # print(f"Should run command: {command}")
    except subprocess.CalledProcessError as e:
        print(f'Failed to set ACL for {path_type}: {path}, Error: {e}')


def reset_acls_recursive(target_directory: str, num_workers: int, alloc_name: str, sub_alloc_names: List[str]):
    print(f"Resetting ACLs recursively in {target_directory} with {num_workers} workers.")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        walker = DirectoryWalker()
        builder = ACL_SpecBuilder()
        builder.build_specs(alloc_name, sub_alloc_names)
        # print(f"THIS IS WHAT SUB_ALLOC_NAMES LOOKS LIKE {sub_alloc_names}")
        # return
        count = 0
        for path, path_type in walker.walk_recursive(target_directory):
            if count % 1000 == 0:
                # print(f'Number pending tasks: {executor._work_queue.qsize()}')
                print(f'Processed {count} paths')
            count += 1
            executor.submit(set_acl, path, path_type, builder)



def main():
    # get the arguments from the user using ArgumentParser
    parser = ArgumentParser()
    parser.retrieve_args()
    import pdb
    pdb.set_trace()
    return


    # at this point, I think I can call the reset_acls_recursive function
    reset_acls_recursive(
        parser.get_target_dir(),
        parser.get_num_workers(),
        parser.get_allocation_name(),
        parser.get_sub_allocations()
    )


if __name__ == "__main__":
    main()