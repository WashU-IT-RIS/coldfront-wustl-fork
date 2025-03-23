import os

from constants import STORAGE_2_PREFIX

class ArgumentParser:

    def __init__(self):
        self.perform_reset = False
        self.allocation_name = ""
        self.allocation_root = ""
        self.num_walkers = 0
        self.num_workers_per_walk = 0
        self.target_dir = ""
        self.sub_allocations = []
        self.log_dir = ""
    
    def get_perform_reset(self):
        return self.perform_reset
    
    def get_allocation_name(self):
        return self.allocation_name
    
    def get_allocation_root(self):
        return self.allocation_root

    def get_num_walkers(self):
        return self.num_walkers
    
    def get_num_workers_per_walk(self):
        return self.num_workers_per_walk
    
    def get_target_dir(self):
        return self.target_dir
    
    def get_sub_allocations(self):
        return self.sub_allocations
    
    def get_log_dir(self):
        return self.log_dir
    
    def retrieve_args(self):
        print("Retrieving args")

        def validate_perform_reset(value):
            if value.lower() not in ['y', 'n']:
                print("Invalid input. Please enter 'y' or 'n'.")
                return False
            return True
        perform_reset_y_n = self._retrieve_arg('perform reset', "Perform reset? (y/n): ", validate_perform_reset)
        self.perform_reset = (perform_reset_y_n == 'y')

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
        
        def validate_sub_allocation_names(value, allocation_root):
            if value == '':
                return True
            sub_alloc_names = value.split(',')
            sub_alloc_paths = []
            for name in sub_alloc_names:
                path = os.path.join(f"{allocation_root}/Active/", name.strip())
                sub_alloc_paths.append(path)
            return all(os.path.exists(path) and os.path.isdir(path) for path in sub_alloc_paths)
        sub_allocations = self._retrieve_arg('sub-allocation names', "Enter the sub-allocation names (comma-separated): ", lambda x: validate_sub_allocation_names(x, allocation_root)).split(',')
        if len(sub_allocations) == 1 and sub_allocations[0] == '':
            sub_allocations = []

        # enter the number of walkers
        def _validate_num_walkers(value):
            try:
                value = int(value)
                if value <= 0:
                    print("Number of walkers must be a positive integer.")
                    return False
                return True
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                return False
        
        num_walkers = int(self._retrieve_arg('number of walkers', "Enter the number of walkers: ", _validate_num_walkers))
        # enter the number of workers
        def _validate_num_workers_per_walk(value):
            try:
                value = int(value)
                if value <= 0:
                    print("Number of workers per walk must be a positive integer.")
                    return False
                return True
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                return False
        num_workers_per_walk = int(self._retrieve_arg('number of workers per walk', "Enter the number of worker threads per walk: ", _validate_num_workers_per_walk))

        def _validate_log_dir(value):
            if os.path.isabs(value):
                if not os.path.exists(value):
                    print(f"Absolute log directory does not exist: {value}")
                    return False
            # else the path will be built
            return True

        log_dir = self._retrieve_arg('log directory', "Enter the log directory: ",_validate_log_dir)

        if os.path.isabs(log_dir):
            self.log_dir = log_dir
        else:
            # build the log directory under wherever this script is running

            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.log_dir = os.path.join(current_dir, log_dir)
        
        self.allocation_root = allocation_root
        self.allocation_name = allocation_root.replace(STORAGE_2_PREFIX, '').strip('/')
        self.target_dir = target_dir
        self.sub_allocations = sub_allocations
        self.num_walkers = num_walkers
        self.num_workers_per_walk = num_workers_per_walk

    def _retrieve_arg(self, arg_name, prompt, validator=None):
        while True:
            value = input(prompt)
            if validator and not validator(value):
                print(f"Invalid value for {arg_name}. Please try again.")
                continue
            # self.args[arg_name] = value
            break
        return value
