import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from directory_walker import DirectoryWalker

from acl_spec_builder import ACL_SpecBuilder

from argument_parser import ArgumentParser

from typing import List, Set

from constants import BATCH_SIZE
import datetime

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

def _piece_out_acl(acl_info: str) -> Set[str]:
    acl_lines = acl_info.splitlines()
    acl_set = set()
    for line in acl_lines:
        if "#" in line or line.strip() == "":
            continue
        acl_set.add(line)
    return acl_set

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
        result_set = _piece_out_acl(acl_info)
        expected_set = _piece_out_acl(expected_spec)
        if result_set != expected_set:
            return False
        return True
    except subprocess.CalledProcessError as e:
        return False
        # print(f'Failed to get ACL: {path}, Error: {e}')

def set_acl(path: str, path_type: str, builder: ACL_SpecBuilder) -> bool:

    # jprew - NOTE: this is test code to exercise the error logs
    # it will make this method fail at random
    import random

    if random.random() < 0.3:
        return False, path
    if os.path.islink(path):
        return True
    processed_path = process_path(path)
    spec = builder.get_spec_by_path(path, path_type)
    command = f'nfs4_setfacl -s "{spec}" {processed_path}'
    try:
        subprocess.run(command, check=True, shell=True)
        # print(f"Should run command: {command}")
        return check_acl(path, processed_path, spec), path
    except subprocess.CalledProcessError as e:
        print(f'Failed to set ACL for {path_type}: {path}, Error: {e}')
        return False, path



def reset_acls_recursive(target_directory: str, num_workers: int, alloc_name: str, sub_alloc_names: List[str], error_file: str):
    print(f"Resetting ACLs recursively in {target_directory} with {num_workers} workers.")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        walker = DirectoryWalker()
        builder = ACL_SpecBuilder()
        builder.build_specs(alloc_name, sub_alloc_names)
        count = 0
        batch_count = 0
        result_futures = []
        for path, path_type in walker.walk_recursive(target_directory):
            if count % 1000 == 0:
                # print(f'Number pending tasks: {executor._work_queue.qsize()}')
                print(f'Processed {count} paths')
            count += 1
            ret = executor.submit(set_acl, path, path_type, builder)
            # ret = set_acl(path, path_type, builder)
            # isn't this single-threaded for each return?
            # though of course, so is the submission...
            result_futures.append(ret)
            if len(result_futures) == BATCH_SIZE:
                print(f"Batch count: {batch_count}")
                batch_count += 1
                for future in result_futures:
                    result = future.result()
                    print(f"Result: {result}")
                result_futures = []


def _create_error_file_name(target_dir: str) -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = os.path.basename(target_dir.rstrip('/'))
    return f"{base_name}_errors_{timestamp}.log"


def main():
    # get the arguments from the user using ArgumentParser
    parser = ArgumentParser()
    parser.retrieve_args()


    # at this point, I think I can call the reset_acls_recursive function
    reset_acls_recursive(
        parser.get_target_dir(),
        parser.get_num_workers(),
        parser.get_allocation_name(),
        parser.get_sub_allocations(),
        _create_error_file_name(parser.get_target_dir())
    )


if __name__ == "__main__":
    main()