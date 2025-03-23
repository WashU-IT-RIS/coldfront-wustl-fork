from typing import List

import os

from constants import STORAGE_2_PREFIX

class ACL_SpecBuilder:
    def __init__(self):
        self.base_folder_spec = ""
        self.base_file_spec = ""

        self.root_spec = ""
        self.active_spec = ""

        self.sub_alloc_file_specs = dict()
        self.sub_alloc_folder_specs = dict()
        self.sub_alloc_root_specs = dict()

        self.allocation_name = ""
        self.sub_alloc_names = []
        # jprew - TODO - need to update the get_spec_by_path method to use
        # these
        
    
    def build_specs(self, alloc_name: str, sub_alloc_names: List[str]):
        self.allocation_name = alloc_name
        self.sub_allocation_names = sub_alloc_names
        # need a spec for the root of the allocation
        with open("templates/root_spec_template.txt", "r") as root_template_file:
            root_template = root_template_file.read()
            for sub_alloc_name in sub_alloc_names:
                # need a spec for the sub-allocation
                with open("templates/root_spec_sub_alloc_entry_template.txt", "r") as sub_alloc_template_file:
                    sub_alloc_template = sub_alloc_template_file.read()
                    sub_alloc_spec_entry = sub_alloc_template.replace("<SUB_ALLOC>", sub_alloc_name)
                    root_template = root_template + sub_alloc_spec_entry
            self.root_spec = root_template.replace("<ALLOC>", alloc_name)
        
        # need a spec for the Active folder
        with open("templates/active_spec_template.txt", "r") as active_template_file:
            active_template = active_template_file.read()
            
            for sub_alloc_name in sub_alloc_names:
                # need a spec for the sub-allocation
                with open("templates/active_spec_sub_alloc_entry_template.txt", "r") as sub_alloc_template_file:
                    sub_alloc_template = sub_alloc_template_file.read()
                    sub_alloc_spec_entry = sub_alloc_template.replace("<SUB_ALLOC>", sub_alloc_name)
                    active_template = active_template + sub_alloc_spec_entry
            self.active_spec = active_template.replace("<ALLOC>", alloc_name)

        # need a spec for folders/files *OUTSIDE* sub-allocations
        with open("templates/base_folder_spec_template.txt", "r") as base_folder_template_file:
            base_folder_template = base_folder_template_file.read()
            self.base_folder_spec = base_folder_template.replace("<ALLOC>", alloc_name)

        with open("templates/base_file_spec_template.txt", "r") as base_file_template_file:
            base_file_template = base_file_template_file.read()
            self.base_file_spec = base_file_template.replace("<ALLOC>", alloc_name)
        
        # need a spec for *each* of the sub-allocations at the sub-allocation's root,
        # for folders beneath root, and for files
        # store it with the sub-allocation name as the key
        with open("templates/sub_alloc_root_spec_template.txt", "r") as sub_alloc_root_template_file:
            sub_alloc_root_template = sub_alloc_root_template_file.read()
            for sub_alloc_name in sub_alloc_names:
                self.sub_alloc_root_specs[sub_alloc_name] = sub_alloc_root_template.replace("<SUB_ALLOC>", sub_alloc_name).replace("<ALLOC>", alloc_name)
        with open("templates/sub_alloc_folder_spec_template.txt", "r") as sub_alloc_folder_template_file:
            sub_alloc_folder_template = sub_alloc_folder_template_file.read()
            for sub_alloc_name in sub_alloc_names:
                self.sub_alloc_folder_specs[sub_alloc_name] = sub_alloc_folder_template.replace("<SUB_ALLOC>", sub_alloc_name).replace("<ALLOC>", alloc_name)
        with open("templates/sub_alloc_file_spec_template.txt", "r") as sub_alloc_file_template_file:
            sub_alloc_file_template = sub_alloc_file_template_file.read()
            for sub_alloc_name in sub_alloc_names:
                self.sub_alloc_file_specs[sub_alloc_name] = sub_alloc_file_template.replace("<SUB_ALLOC>", sub_alloc_name).replace("<ALLOC>", alloc_name)

    def get_root_spec(self):
        return self.root_spec
    
    def get_active_spec(self):
        return self.active_spec
    
    def get_base_folder_spec(self):
        return self.base_folder_spec
    
    def get_base_file_spec(self):
        return self.base_file_spec
    
    def get_sub_alloc_root_spec(self, sub_alloc_name: str):
        return self.sub_alloc_root_specs.get(sub_alloc_name, "")

    def get_sub_alloc_folder_spec(self, sub_alloc_name: str):
        return self.sub_alloc_folder_specs.get(sub_alloc_name, "")
    
    def get_sub_alloc_file_spec(self, sub_alloc_name: str):
        return self.sub_alloc_file_specs.get(sub_alloc_name, "")
    
    def get_spec_by_path(self, target: str, item_type: str):
        # jprew - TODO - this is a stub
        allocation_root = f"{STORAGE_2_PREFIX}/{self.allocation_name}"
        allocation_root_active = f"{allocation_root}/Active"
        if os.path.samefile(allocation_root, target):
            return self.get_root_spec()
        elif os.path.samefile(allocation_root_active, target):
            return self.get_active_spec()

        # check if target *is* one of the sub_alloc roots
        sub_alloc_roots = []
        for name in self.sub_alloc_names:
            path = os.path.join(f"{allocation_root}/Active/", name.strip())
            sub_alloc_roots.append(str(path))

        for sub_alloc_root, sub_alloc_name in zip(sub_alloc_roots, self.sub_alloc_names):
            if os.path.samefile(sub_alloc_root, target):
                return self.get_sub_alloc_root_spec(sub_alloc_name)
            elif target.startswith(sub_alloc_root + os.sep):
                if item_type == "directory":
                    return self.get_sub_alloc_folder_spec(sub_alloc_name)
                else:
                    return self.get_sub_alloc_file_spec(sub_alloc_name)
        
        if item_type == "directory":
            return self.get_base_folder_spec()
        else:
            return self.get_base_file_spec()
