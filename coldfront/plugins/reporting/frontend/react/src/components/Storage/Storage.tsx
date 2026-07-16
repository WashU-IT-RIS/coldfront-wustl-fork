import { useEffect, useState } from "react";

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

  useEffect(() => {
    getAllocationUsage(startDate, endDate).then(({ quota, usage }) => {
      setQuota(quota);
      setUsage(usage);
    });
  }, [startDate, endDate]);

  return (
    <>
      <h3>Storage Usage</h3>
      <div>
        <label htmlFor="allocationSelector">Allocation</label>
        <select id="allocationSelector">
          <option value={245}>/storage1/fs1/foo</option>
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
) {
  const response = await axios.get("/qumulo/api/usage", {
    params: { allocation_id: 245, start_date: startDate, end_date: endDate },
  });

  const { quota, usage } = response.data;
  return { quota, usage } as {
    quota: number;
    usage: usageData;
  };
}

export default Storage;
