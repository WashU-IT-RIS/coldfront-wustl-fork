import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  ChartOptions,
  LineOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";

import * as chartjsAdapter from "chartjs-adapter-dayjs-4";
import "./StorageChart.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
);

interface StorageChartProps {
  data: {
    usage: { x: string; y: number }[];
    quota: { x: string; y: number }[];
    path: string;
  };
  isLoading: Boolean;
}

function StorageChart({ data, isLoading }: StorageChartProps) {
  const getMaxQuota = () => {
    let maxQuota = 0;
    for (const element of data.quota) {
      maxQuota = element.y > maxQuota ? element.y : maxQuota;
    }

    return maxQuota;
  };

  const options: ChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: data.path,
      },
      tooltip: {
        filter: (toolTipItem) => toolTipItem.dataset.label === "Usage",
        callbacks: {
          title: (tooltipItems) => {
            return tooltipItems.map((tooltipItem) => {
              const rawData = tooltipItem.raw as { x: string; y: number };
              return new Date(rawData.x).toDateString();
            });
          },
          afterBody: (tooltipItems) => {
            return tooltipItems.map((tooltipItem) => {
              const rawData = tooltipItem.raw as { x: string; y: number };
              return formatBytes(rawData.y * 2 ** 40);
            });
          },
        },
      },
    },
    scales: {
      x: {
        type: "time",
        time: { unit: "month" },
        adapters: {
          date: chartjsAdapter,
        },
      },
      y: {
        title: {
          display: true,
          text: "Size (TiB)",
        },
        min: 0,
        max: Math.floor((getMaxQuota() + 0.25) / 0.25) * 0.25,
      },
    },
  };

  if (data.usage.length && data.quota.length) {
    if (data.usage[0].x > data.quota[0].x) {
      data.quota = [{ x: data.usage[0].x, y: data.quota[0].y }, ...data.quota];
    }
    if (data.quota[0].x > data.usage[0].x) {
      data.usage = [{ x: data.quota[0].x, y: data.usage[0].y }, ...data.usage];
    }

    const lastUsage = data.usage[data.usage.length - 1];
    const lastQuota = data.quota[data.quota.length - 1];
    if (lastUsage.x < lastQuota.x) {
      data.quota = [{ x: lastUsage.x, y: lastQuota.y }, ...data.quota];
    }
    if (lastQuota.x < lastUsage.x) {
      data.usage = [{ x: lastQuota.x, y: lastUsage.y }, ...data.usage];
    }
  }

  const chartData = {
    datasets: [
      {
        label: "Usage",
        data: data.usage,
        borderColor: "rgb(88, 88, 255)",
        backgroundColor: "rgba(0, 0, 255, 0.5)",
      },
      {
        label: "Quota",
        data: data.quota,
        borderColor: "rgb(255, 99, 132)",
        backgroundColor: "rgba(255, 99, 132, 0.5)",
        plugins: {
          tooltip: {
            enabled: false,
          },
        },
      },
    ],
  };

  return (
    <div className="storage-chart">
      {/* 
// @ts-ignore */}
      <Line
        className="storage-chart-child"
        options={options as LineOptions}
        data={chartData}
      />
      {isLoading && (
        <div className="storage-chart-child storage-chart-spinner d-flex justify-content-center align-items-center">
          <div className="spinner-border" role="status" />
        </div>
      )}
    </div>
  );
}

function formatBytes(bytes: number, decimals = 2) {
  if (!+bytes) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = [
    "Bytes",
    "KiB",
    "MiB",
    "GiB",
    "TiB",
    "PiB",
    "EiB",
    "ZiB",
    "YiB",
  ];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export default StorageChart;
