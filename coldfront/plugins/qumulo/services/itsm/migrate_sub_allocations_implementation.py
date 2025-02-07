from coldfront.plugins.qumulo.services.allocation_service import AllocationService

from coldfront.core.allocation.models import (
    Allocation,
    AllocationLinkage,
)


class MigrateSubAllocationsImplementation:

    def create_sub_allocations(self, parent_allocation_id: str, sub_allocs_to_create: dict, dry_run: bool=True):
        import pdb
        pdb.set_trace()
        if not Allocation.objects.filter(pk=parent_allocation_id).exists():
            raise Exception(f"Parent allocation with id {parent_allocation_id} does not exist.")
        
        # confirm that the parent allocation is active
        parent_allocation = Allocation.objects.get(pk=parent_allocation_id)

        if parent_allocation.status.name != "Active":
            raise Exception(f"Parent allocation with id {parent_allocation_id} is not active.")

        try:
            linkage = AllocationLinkage.objects.filter(parent=parent_allocation)
        except:
            raise Exception(f"Parent allocation {parent_allocation_id} has no linkage")

        existing_child_allocs = linkage.children.all()
        if len(existing_child_allocs) > 0:
            raise Exception(f"Parent allocation {parent_allocation_id} already has child sub-allocations.")

        parent_pi_user = parent_allocation.project.pi
        pdb.set_trace()
        if dry_run:
            print("Not creating sub-allocations due to dry-run mode.")
            return

        num_sub_allocs_expected = len(sub_allocs_to_create)

        pdb.set_trace()
        for entry in sub_allocs_to_create:
             
            sub_alloc_info = dict()
            sub_alloc_info["project_pk"] = parent_allocation.project.id
            sub_alloc_info["parent_allocation_name"] = parent_allocation.name
            sub_alloc_info["storage_filesystem_path"] =  entry["project_dir_name"]
            sub_alloc_info["storage_export_path"] = []
            sub_alloc_info["storage_ticket"] = parent_allocation.get_attribute("storage_ticket")
            sub_alloc_info["storage_name"] = entry["project_dir_name"]
            sub_alloc_info["storage_quota"] = int(parent_allocation.get_attribute("storage_quota"))
            sub_alloc_info["protocols"] = []
            sub_alloc_info["rw_users"] = entry["rw"]
            sub_alloc_info["ro_users"] = entry["ro"]
            sub_alloc_info["cost_center"] = parent_allocation.get_attribute("cost_center")
            sub_alloc_info["department_number"] = parent_allocation.get_attribute("department_number")
            sub_alloc_info["service_rate"] = parent_allocation.get_attribute("service_rate")

            # create a sub-allocation
            _ = AllocationService.create_new_allocation(
                sub_alloc_info, parent_pi_user, parent_allocation=parent_allocation
            )
        
        pdb.set_trace()
        linkage.refresh_from_db()
        if num_sub_allocs_expected != linkage.children.count():
            raise Exception(f"Expected {num_sub_allocs_expected} sub-allocations, but found {linkage.children.count()}")

    
