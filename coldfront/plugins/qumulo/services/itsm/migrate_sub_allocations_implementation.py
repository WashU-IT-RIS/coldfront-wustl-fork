from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from coldfront.core.allocation.models import (
    Allocation,
    AllocationLinkage,
)

import time
import os

from dotenv import load_dotenv

load_dotenv(override=True)

class MigrateSubAllocationsImplementation:

    def create_sub_allocations(self, parent_allocation_id: str, sub_allocs_to_create: dict, dry_run: bool=True):
        if not Allocation.objects.filter(pk=parent_allocation_id).exists():
            raise Exception(f"Parent allocation with id {parent_allocation_id} does not exist.")
        
        # confirm that the parent allocation is active
        parent_allocation = Allocation.objects.get(pk=parent_allocation_id)

        if parent_allocation.status.name != "Active":
            raise Exception(f"Parent allocation with id {parent_allocation_id} is not active.")

        # confirm that no sub-allocation with this name already exists
        child_already_exists = False
        try:
            linkage = AllocationLinkage.objects.get(parent=parent_allocation)
            child_already_exists = linkage.children.filter(name__in=[entry["project_dir_name"] for entry in sub_allocs_to_create]).exists()
        except:
            # no linkage exists, so continue
            pass
        
        if child_already_exists:
            raise Exception(f"Sub-allocation with name {entry['project_dir_name']} already exists.")
        
        parent_pi_user = parent_allocation.project.pi

        if dry_run:
            print("Not creating sub-allocations due to dry-run mode.")
            return


        for entry in sub_allocs_to_create:
            sub_alloc_info = dict()
            sub_alloc_info["project_pk"] = parent_allocation.project.id
            sub_alloc_info["parent_allocation_name"] = parent_allocation.get_attribute("storage_name")
            sub_alloc_info["storage_filesystem_path"] =  entry["project_dir_name"]
            sub_alloc_info["storage_export_path"] = []
            sub_alloc_info["storage_ticket"] = parent_allocation.get_attribute("storage_ticket")
            
            if os.environ.get("ENVIRONMENT") == "qa":
                sub_alloc_info["storage_name"] = entry["project_dir_name"]
            else:
                sub_alloc_info["storage_name"] = f"{entry["project_dir_name"]}_{int(time.time())}"
                
            sub_alloc_info["storage_quota"] = int(parent_allocation.get_attribute("storage_quota"))
            sub_alloc_info["protocols"] = []
            sub_alloc_info["rw_users"] = entry["rw"]
            sub_alloc_info["ro_users"] = entry["ro"]
            sub_alloc_info["cost_center"] = parent_allocation.get_attribute("cost_center")
            sub_alloc_info["department_number"] = parent_allocation.get_attribute("department_number")
            sub_alloc_info["service_rate"] = parent_allocation.get_attribute("service_rate")
            sub_alloc_info["billing_cycle"] = parent_allocation.get_attribute("billing_cycle")
            sub_alloc_info["technical_contact"] = parent_allocation.get_attribute("technical_contact")
            sub_alloc_info["billing_contact"] = parent_allocation.get_attribute("billing_contact")

            # create a sub-allocation
            _ = AllocationService.create_new_allocation(
                sub_alloc_info, parent_pi_user, parent_allocation=parent_allocation
            )
