import { useEffect, useState } from "react";

import StorageChart from "../StorageChart/StorageChart";
import Select, { SingleValue } from "react-select";

import axios from "axios";

type usageData = { date: string; usage: number; quota: number }[];

function Storage() {
  const [usage, setUsage] = useState([] as usageData);
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
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (selectedAllocation) {
      setIsLoading(true);
      getAllocationUsage(startDate, endDate, selectedAllocation).then(
        (usageData) => {
          setUsage(usageData);
          setIsLoading(false);
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

  const onSelectChange = (
    newValue: SingleValue<{
      value: number | undefined;
      label: string | undefined;
    }>,
  ) => {
    const allocationId = newValue?.value;
    const allocationOption = allocationOptions.find(
      (option) => option.id === allocationId,
    );

    setSelectedAllocation(allocationOption);
  };

  const getOptions = () => {
    return allocationOptions.map((allocationOption) => {
      return { value: allocationOption.id, label: allocationOption.path };
    });
  };

  return (
    <>
      <h3>Storage Usage</h3>
      <div>
        <label htmlFor="allocationSelector">Allocation</label>
        <Select
          options={getOptions()}
          onChange={(newValue) => onSelectChange(newValue)}
          value={{
            value: selectedAllocation?.id,
            label: selectedAllocation?.path,
          }}
        ></Select>
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
            y: GiBtoTiB(element.usage),
          })),
          quota: usage.map((element) => ({
            x: element.date,
            y: GiBtoTiB(element.quota),
          })),
          path: selectedAllocation?.path || "",
        }}
        isLoading={isLoading}
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

  const { usage_data } = response.data;
  return usage_data as usageData;
}

async function getAllocationOptions() {
  const response = await axios.get("/qumulo/api/usage/allocations");

  const { allocations } = response.data;
  return allocations as AllocationOption[];
}

function GiBtoTiB(GiB: number) {
  return GiB / 1024;
}

export default Storage;
