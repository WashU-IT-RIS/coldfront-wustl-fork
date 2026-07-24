import { SyntheticEvent, useEffect, useState } from "react";

import StorageChart from "../StorageChart/StorageChart";

import axios from "axios";

type usageData = { date: string; usage: number }[];

function Storage() {
  const [usage, setUsage] = useState([] as usageData);
  const [quota, setQuota] = useState(0);
  const [endDate, setEndDate] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [startDate, setStartDate] = useState(undefined as undefined | string);
  const [selectedAllocation, setSelectedAllocation] = useState(
    undefined as undefined | AllocationOption,
  );
  const [allocationOptions, setAllocationOptions] = useState(
    [] as AllocationOption[],
  );

  useEffect(() => {
    if (selectedAllocation) {
      getAllocationUsage(startDate, endDate, selectedAllocation).then(
        ({ quota, usage }) => {
          setQuota(quota);
          setUsage(usage);
        },
      );
    }
  }, [startDate, endDate, selectedAllocation]);

  useEffect(() => {
    getAllocationOptions().then((returnedOptions) => {
      setAllocationOptions(returnedOptions);
      if (returnedOptions.length) {
        setSelectedAllocation(returnedOptions[0]);
      }
    });
  }, []);

  const onSelectChange = (event: SyntheticEvent) => {
    const allocationId: number = parseInt(event.target.value);
    const allocationOption = allocationOptions.find(
      (option) => option.id === allocationId,
    );

    setSelectedAllocation(allocationOption);
  };

  const renderOptions = () => {
    return allocationOptions.map((allocationOption) => {
      return (
        <option value={allocationOption.id}>{allocationOption.path}</option>
      );
    });
  };

  return (
    <>
      <h3>Storage Usage</h3>
      <div>
        <label htmlFor="allocationSelector">Allocation</label>
        <select
          id="allocationSelector"
          onChange={onSelectChange}
          value={selectedAllocation?.id}
        >
          {renderOptions()}
        </select>
      </div>
      <div>
        <DateInput
          id="startDate"
          label="Start Date"
          value={startDate}
          setDate={setStartDate}
        />
        <DateInput
          id="endDate"
          label="End Date"
          value={endDate}
          setDate={setEndDate}
        />
      </div>
      <StorageChart
        data={{
          usage: usage.map((element) => ({
            x: element.date,
            y: element.usage,
          })),
          quota,
        }}
      />
    </>
  );
}

interface DateInputProps {
  id: string;
  label: string;
  value: string | undefined;
  setDate: Function;
}

interface AllocationOption {
  id: number;
  path: string;
}

function DateInput({ id, label, value, setDate }: DateInputProps) {
  return (
    <>
      <label htmlFor={id}>{label}</label>
      <input
        className="form-control"
        type="date"
        value={value}
        onChange={(event) => setDate(event.target.value)}
      />
    </>
  );
}

async function getAllocationUsage(
  startDate: string | undefined,
  endDate: string,
  allocation: AllocationOption,
) {
  const response = await axios.get("/qumulo/api/usages", {
    params: {
      allocation_id: allocation.id,
      start_date: startDate,
      end_date: endDate,
    },
  });

  const { quota, usage } = response.data;
  return { quota, usage } as {
    quota: number;
    usage: usageData;
  };
}

async function getAllocationOptions() {
  const response = await axios.get("/qumulo/api/usage/allocations");

  const { allocations } = response.data;
  return allocations as AllocationOption[];
}

export default Storage;
