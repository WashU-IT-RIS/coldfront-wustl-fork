import os

from constants import STORAGE_2_PREFIX

class ArgumentParser:

    def __init__(self):
        self.allocation_name = ""
        self.allocation_root = ""
        self.num_workers = 0
        self.target_dir = ""
        self.sub_allocations = []
    
    def get_allocation_name(self):
        return self.allocation_name
    
    def get_allocation_root(self):
        return self.allocation_root
    
    def get_num_workers(self):
        return self.num_workers
    
    def get_target_dir(self):
        return self.target_dir
    
    def get_sub_allocations(self):
        return self.sub_allocations 
    
    def retrieve_args(self):
        print("Retrieving args")

        # first, retrieve a file and confirm it exists in 
        # a passed-in validator
        # enter the root directory of the allocation
        def validate_allocation_root(value):
            # check that there is only a single part after the prefix
            # and that the path exists
            if not value.startswith(STORAGE_2_PREFIX):
                print(f"Root path must look like '{STORAGE_2_PREFIX}<ROOT>'.")
                return False
            # check that there is only a single part after the prefix
            allocation_root_name = value.replace(STORAGE_2_PREFIX, '').strip('/')
            if '/' in allocation_root_name:
                print(f"Root path must look like '{STORAGE_2_PREFIX}<ROOT>'.")
                return False
            if not (os.path.exists(value) and os.path.isdir(value)):
                print(f"Root path does not exist: {value}")
                return False
            return True
        allocation_root = self._retrieve_arg('allocation root', "Enter the root directory of the allocation: ", validate_allocation_root)
        # get the target directory (where to start the walk)
        target_dir = self._retrieve_arg('target directory', "Enter the target directory: ", lambda x: os.path.exists(x) and os.path.isdir(x) and x.startswith(allocation_root))
        
        allocation_root = STORAGE_2_PREFIX + "/prewitt"
        def validate_sub_allocation_names(value, allocation_root):
            import pdb
            pdb.set_trace()
            sub_alloc_names = value.split(',')
            sub_alloc_paths = []
            for name in sub_alloc_names:
                path = os.path.join(f"{allocation_root}/Active/", name.strip())
                sub_alloc_paths.append(path)
            return all(os.path.exists(path) and os.path.isdir(path) for path in sub_alloc_paths)
        sub_allocations = self._retrieve_arg('sub-allocation names', "Enter the sub-allocation names (comma-separated): ", lambda x: validate_sub_allocation_names(x, allocation_root)).split(',')
        if len(sub_allocations) == 1 and sub_allocations[0] == '':
            sub_allocations = []

        # all right, what else do I need *functionally*?
        # I think nothing, so what remains is stuff like workers

        # enter the number of workers
        def _validate_num_workers(value):
            try:
                value = int(value)
                if value <= 0:
                    print("Number of workers must be a positive integer.")
                    return False
                return True
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                return False
        num_workers = int(self._retrieve_arg('number of workers', "Enter the number of worker threads: ", _validate_num_workers))

        self.allocation_root = allocation_root
        self.allocation_name = allocation_root.replace(STORAGE_2_PREFIX, '').strip('/')
        self.target_dir = target_dir
        self.sub_allocations = sub_allocations
        self.num_workers = num_workers

    def _retrieve_arg(self, arg_name, prompt, validator=None):
        while True:
            value = input(prompt)
            if validator and not validator(value):
                print(f"Invalid value for {arg_name}. Please try again.")
                continue
            # self.args[arg_name] = value
            break
        return value

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.retrieve_args()