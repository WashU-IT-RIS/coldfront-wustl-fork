import { useActionState, useEffect, useState } from "react";
import axios from "axios";

const onGetAllocations = async () => {
  const response = await axios.get("/qumulo/api/allocations");

  return response.data.map((allocation) => ({
    id: allocation.id,
    resource_name: allocation.resources[-1],
    allocation_status: allocation.status,
    file_path: allocation.attributes.storage_filesystem_path,
  }));
};

function AllocationSelector({ setSelectedAllocations, selectedAllocations }) {
  const columns = ["id", "resource_name", "allocation_status", "file_path"];
  const [allocations, setAllocations] = useState([]);

  useEffect(() => {
    onGetAllocations().then((allocations) => setAllocations(allocations));
  }, []);

  const renderHeader = () => {
    return columns.map((column) => (
      <th key={column} scope="col" className="text-nowrap">
        {column}
        <a className="sort-asc">
          <i className="fas fa-sort-up" aria-hidden="true"></i>
          <span className="sr-only">Sort {column} asc</span>
        </a>
        <a className="sort-desc">
          <i className="fas fa-sort-down" aria-hidden="true"></i>
          <span className="sr-only">Sort {column} desc</span>
        </a>
      </th>
    ));
  };

  const renderOptions = () => {
    return allocations.map((allocation) => (
      <tr key={allocation.id} className="text-nowrap">
        <td key="checkbox">
          <input
            type="checkbox"
            id={`allocation-${allocation.id}`}
            value={allocation.id}
          />
        </td>
        {columns.map((column) => (
          <td key={column} className="text-nowrap">
            {allocation[column]}
          </td>
        ))}
      </tr>
    ));
  };

  return (
    <div className="table-responsive">
      <table className="table table-sm">
        <thead>
          <tr>
            <th key="checkbox" scope="col" className="text-nowrap">
              {/* <input
                type="checkbox"
                id="select_all"
                name="select_all"
                value="select_all"
              /> */}
            </th>
            {renderHeader()}
          </tr>
        </thead>
        <tbody name="table-values-tbody">
          {/* {% comment %} JS populate this {% endcomment %} */}
        </tbody>
        <tbody name="table-options-tbody">{renderOptions()}</tbody>
      </table>
    </div>
  );
}

export default AllocationSelector;
