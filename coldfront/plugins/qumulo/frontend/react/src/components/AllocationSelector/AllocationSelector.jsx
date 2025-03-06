import { lazy, useActionState, useEffect, useState } from "react";
import axios from "axios";

const onGetAllocations = async (params) => {
  const response = await axios.get("/qumulo/api/allocations", { params });

  return response.data.map((allocation) => ({
    id: allocation.id,
    resource__name: allocation.resources[allocation.resources.length - 1],
    status__name: allocation.status,
    attributes__storage_filesystem_path:
      allocation.attributes.storage_filesystem_path,
  }));
};

function AllocationSelector({ setSelectedAllocations, selectedAllocations }) {
  const columns = [
    { key: "id", label: "ID" },
    { key: "resource__name", label: "Resource" },
    { key: "status__name", label: "Status" },
    { key: "attributes__storage_filesystem_path", label: "File Path" },
  ];
  const [allocations, setAllocations] = useState([]);

  useEffect(() => {
    onGetAllocations().then((allocations) => setAllocations(allocations));
  }, []);

  const getAllocations = async (params) => {
    const allocations = await onGetAllocations(params);

    setAllocations(allocations);
  };

  const renderHeader = () => {
    return columns.map(({ key, label }) => (
      <th key={key} scope="col" className="text-nowrap">
        {label}
        <a className="sort-asc" onClick={() => getAllocations({ sort: key })}>
          <i className="fas fa-sort-up" aria-hidden="true"></i>
          <span className="sr-only">Sort {label} asc</span>
        </a>
        <a
          className="sort-desc"
          onClick={() => getAllocations({ sort: `-${key}` })}
        >
          <i className="fas fa-sort-down" aria-hidden="true"></i>
          <span className="sr-only">Sort {label} desc</span>
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
        {columns.map(({ key, label }) => (
          <td key={key} className="text-nowrap">
            {allocation[key]}
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
