import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from directory_walker import walk_recursive_from_target, walk_to_max_depth, find_depth_for_target_dirs

from acl_spec_builder import ACL_SpecBuilder

from argument_parser import ArgumentParser

from typing import List, Set, Callable

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
            print(f"Returning False {processed_path}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        return False

def process_acl(perform_reset: bool, path: str, path_type: str, builder: ACL_SpecBuilder) -> bool:
    if os.path.islink(path):
        return True, path
    processed_path = process_path(path)
    spec = builder.get_spec_by_path(path, path_type)
    try:
        if perform_reset:
            reset_command = f'nfs4_setfacl -s "{spec}" {processed_path}'
            subprocess.run(reset_command, check=True, shell=True)
        return check_acl(path, processed_path, spec), path
    except subprocess.CalledProcessError as e:
        print(f'Failed to set ACL for {path_type}: {path}, Error: {e}')
        return False, path



def process_acls_recursive(perform_reset: bool, target_directory: str, num_workers: int, alloc_name: str, sub_alloc_names: List[str], error_file: str, walker_method: Callable):
    print(f"Processing ACLs recursively in {target_directory} with {num_workers} workers.")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        builder = ACL_SpecBuilder()
        builder.build_specs(alloc_name, sub_alloc_names)
        count = 0
        batch_count = 0
        result_futures = []
        with open(error_file, 'w') as error_log:
            for path, path_type in walker_method(target_directory):
                if count % 1000 == 0:
                    # print(f'Number pending tasks: {executor._work_queue.qsize()}')
                    print(f'Processed {count} paths')
                count += 1
                ret = executor.submit(process_acl, perform_reset, path, path_type, builder)
                result_futures.append(ret)
                if len(result_futures) == BATCH_SIZE:
                    print(f"Batch count: {batch_count}")
                    batch_count += 1
                    for future in result_futures:
                        success, check_path = future.result()
                        if not success:
                            error_log.write(f"{check_path}\n")
                    result_futures = []


def _create_error_file_name(target_dir: str, output_dir: str) -> str:
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    base_name = os.path.basename(target_dir.rstrip('/'))
    return f"{output_dir}/{base_name}_errors_{timestamp}.log"


def main():
    # get the arguments from the user using ArgumentParser
    parser = ArgumentParser()
    parser.retrieve_args()
    # go ahead and make a directory for the logs
    if not os.path.exists(parser.get_log_dir()):
        os.makedirs(parser.get_log_dir())

    # find the depth at which there are >= num_walkers subdirectories to use as parallel targets
    if parser.get_num_walkers() > 1:
        result = find_depth_for_target_dirs(parser.get_target_dir(), parser.get_num_walkers())
    else:
        result = None

    if result is None:
        # if there are not enough subdirectories or you only have one walker, just process the whole thing
        print("Not enough subdirectories found for parallel processing. Processing the entire directory.")
        process_acls_recursive(
            parser.get_perform_reset(),
            parser.get_target_dir(),
            parser.get_num_workers_per_walk(),
            parser.get_allocation_name(),
            parser.get_sub_allocations(),
            _create_error_file_name(parser.get_target_dir(), parser.get_log_dir()),
            walk_recursive_from_target
        )
    else:
        dir_depth, dir_count, dirs_at_depth = result
        # if there are enough subdirectories, process them in parallel
        print(f"Processing {len(dirs_at_depth)} subdirectories in parallel.")
        with ProcessPoolExecutor(max_workers=parser.get_num_walkers()) as walk_executor:
            for subdir in dirs_at_depth:
                _ = walk_executor.submit(
                    process_acls_recursive,
                    parser.get_perform_reset(),
                    subdir,
                    parser.get_num_workers_per_walk(),
                    parser.get_allocation_name(),
                    parser.get_sub_allocations(),
                    _create_error_file_name(subdir, parser.get_log_dir()),
                    walk_recursive_from_target
                )
                # do I need to inspect the results of these parallel processors?
                # or just rely on the log files they produce
        # now, use walk_to_max_depth to pick up the remaining files/directories *above* that parallelization target level
        process_acls_recursive(
            parser.get_perform_reset(),
            parser.get_target_dir(),
            parser.get_num_workers_per_walk(),
            parser.get_allocation_name(),
            parser.get_sub_allocations(),
            _create_error_file_name(parser.get_target_dir(), parser.get_log_dir()),
            lambda x: walk_to_max_depth(x, dir_depth)
        )

if __name__ == "__main__":
    main()