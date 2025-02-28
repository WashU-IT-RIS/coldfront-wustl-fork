import SelectableTable from "../SelectableTable/SelectableTable";

function AllocationSelector() {
  const columns = ["id", "resource_name", "allocation_status", "file_path"];

  return <SelectableTable columns={columns} />;
}

export default AllocationSelector;
