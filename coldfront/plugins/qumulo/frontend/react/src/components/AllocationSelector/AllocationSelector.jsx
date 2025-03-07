import { useActionState, useEffect, useState } from "react";
import axios from "axios";

import InputLabel from "../InputLabel/InputLabel";

function AllocationSelector({ setSelectedAllocations, selectedAllocations }) {
  const columns = [
    { key: "id", label: "ID" },
    { key: "resources__name", label: "Resource" },
    { key: "status__name", label: "Status" },
    { key: "attributes__storage_filesystem_path", label: "File Path" },
  ];

  const onQueryChange = (state, { action, key, value }) => {
    switch (action) {
      case "filter":
        return {
          ...state,
          filters: { ...state.filters, [key]: value },
        };
      case "sort":
        return {
          ...state,
          sort: value,
        };
      default:
        return state;
    }
  };

  const [allocations, setAllocations] = useState([]);
  const [allChecked, setAllChecked] = useState(false);
  const [queryState, queryDispatch] = useActionState(onQueryChange, {
    filters: {},
  });

  useEffect(() => {
    const params = { search: [], sort: queryState.sort };

    for (const [key, value] of Object.entries(queryState.filters)) {
      params.search.push(`${key}:${value}`);
    }

    getAllocations(params).then((allocations) => setAllocations(allocations));
  }, [queryState]);

  const renderHeader = () => {
    return columns.map(({ key, label }) => (
      <th key={key} scope="col" className="text-nowrap">
        <InputLabel
          label={label}
          value={queryState.filters[key]}
          onChange={(value) => queryDispatch({ action: "filter", key, value })}
        />
        <a
          className="sort-asc"
          onClick={() =>
            queryDispatch({ action: "sort", key, value: `-${key}` })
          }
        >
          <i className="fas fa-sort-up" aria-hidden="true"></i>
          <span className="sr-only">Sort {label} asc</span>
        </a>
        <a
          className="sort-desc"
          onClick={() => queryDispatch({ action: "sort", key, value: key })}
        >
          <i className="fas fa-sort-down" aria-hidden="true"></i>
          <span className="sr-only">Sort {label} desc</span>
        </a>
      </th>
    ));
  };

  const onAllocationCheck = (event) => {
    const allocationId = event.target.value;

    if (event.target.checked) {
      const allocation = allocations.find(
        (allocation) => allocation.id === Number(allocationId)
      );
      setSelectedAllocations([...selectedAllocations, allocation]);
    } else {
      setSelectedAllocations(
        selectedAllocations.filter(
          (allocation) => allocation.id !== Number(allocationId)
        )
      );
      setAllChecked(false);
    }
  };

  const onCheckAll = (event) => {
    if (event.target.checked) {
      setSelectedAllocations([
        ...new Set([...selectedAllocations, ...allocations]),
      ]);
      setAllChecked(true);
    } else {
      setSelectedAllocations([]);
      setAllChecked(false);
    }
  };

  const isChecked = (allocation) => {
    return selectedAllocations
      .map((allocation) => allocation.id)
      .includes(allocation.id);
  };

  const renderRows = (allocations) => {
    return allocations.map((allocation) => (
      <tr key={allocation.id} className="text-nowrap">
        <td key="checkbox">
          <input
            type="checkbox"
            id={`allocation-${allocation.id}`}
            value={allocation.id}
            checked={isChecked(allocation)}
            onChange={onAllocationCheck}
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

  const renderOptions = () => {
    const unCheckedAllocations = allocations.filter(
      (allocation) =>
        !selectedAllocations
          .map((selecatedAllocation) => selecatedAllocation.id)
          .includes(allocation.id)
    );

    return renderRows(unCheckedAllocations);
  };

  return (
    <div className="table-responsive">
      <table className="table table-sm">
        <thead>
          <tr>
            <th key="checkbox" scope="col" className="text-nowrap">
              <input
                type="checkbox"
                name="select_all"
                onChange={onCheckAll}
                value="select_all"
                checked={allChecked}
              />
            </th>
            {renderHeader()}
          </tr>
        </thead>
        <tbody name="table-values-tbody">
          {renderRows(selectedAllocations)}
        </tbody>
        <tbody name="table-options-tbody">{renderOptions()}</tbody>
      </table>
    </div>
  );
}

async function getAllocations(params) {
  const response = await axios.get("/qumulo/api/allocations", { params });

  return response.data.map((allocation) => ({
    id: allocation.id,
    resources__name: allocation.resources[allocation.resources.length - 1],
    status__name: allocation.status,
    attributes__storage_filesystem_path:
      allocation.attributes.storage_filesystem_path,
  }));
}

export default AllocationSelector;
