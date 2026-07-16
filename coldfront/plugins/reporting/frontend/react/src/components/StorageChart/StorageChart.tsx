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
    quota: number;
  };
}

function StorageChart({ data }: StorageChartProps) {
  const options: ChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Storage Usage",
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
              return formatBytes((rawData.y * 2) ^ 30);
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
          text: "Size (GiB)",
        },
        min: 0,
        max: Math.floor((data.quota + 512) / 500) * 500,
      },
    },
  };

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
        data: data.usage.map(({ x }) => ({ x, y: data.quota })),
        borderColor: "rgb(255, 99, 132)",
        backgroundColor: "rgba(255, 99, 132, 0.5)",
        pointStyle: false,
        plugins: {
          tooltip: {
            enabled: false,
          },
        },
      },
    ],
  };

  return (
    <>
      {/* 
// @ts-ignore */}
      <Line options={options as LineOptions} data={chartData} />
    </>
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
