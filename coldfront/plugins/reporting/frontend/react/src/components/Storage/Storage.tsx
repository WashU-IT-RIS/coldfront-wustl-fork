import { useEffect, useState } from "react";

import StorageChart from "../StorageChart/StorageChart";
import AllocationDropdown from "../AllocationDropdown/AllocationDropdown";

import axios from "axios";

type usageData = { date: string; usage: number }[];

function Storage() {
  const [usage, setUsage] = useState([] as usageData);
  const [quota, setQuota] = useState(0);

  useEffect(() => {
    getAllocationUsage().then(({ quota, usage }) => {
      setQuota(quota);
      setUsage(usage);
    });
  }, []);

  return (
    <>
      <h3>Storage Usage</h3>
      <AllocationDropdown />
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

async function getAllocationUsage() {
  const response = await axios.get("/qumulo/api/usage", {
    params: { allocation_id: 1 },
  });

  const { quota, usage } = response.data;
  return { quota, usage } as {
    quota: number;
    usage: usageData;
  };
}

export default Storage;
