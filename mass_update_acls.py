import os
import subprocess
import sys


def apply_acl(directory, sub_dir_acl_spec, file_acl_spec):
    # Walk through the directory and apply the ACL to each file and sub-directory
    for root, dirs, files in os.walk(directory):
        for name in dirs + files:
            if os.path.isdir(os.path.join(root, name)):
                acl_spec = sub_dir_acl_spec
            else:
                acl_spec = file_acl_spec
            path = os.path.join(root, name)
            try:
                subprocess.run(['nfs4_setfacl', '-S', acl_spec, path], check=True)
                print(f"Applied ACL to {path}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to apply ACL to {path}: {e}")

def apply_acl_top(directory, dir_acl_spec):
    # Apply the ACL to the top-level directory
    try:
        subprocess.run(['nfs4_setfacl', '-S', dir_acl_spec, directory], check=True)
        print(f"Applied ACL to {directory}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to apply ACL to {directory}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory> <dir_acl_file> <sub_dir_acl_file> <file_acl_file>")
        sys.exit(1)

    directory = sys.argv[1]
    dir_acl_file = sys.argv[2]
    sub_dir_acl_file = sys.argv[3]
    file_acl_file = sys.argv[4]


    apply_acl(directory, sub_dir_acl_file, file_acl_file)
    apply_acl_top(directory, dir_acl_file)
