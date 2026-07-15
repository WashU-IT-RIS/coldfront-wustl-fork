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
        min: 0,
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
      // {
      //   label: "Quota",
      //   data: data.quota,
      //   borderColor: "rgb(255, 99, 132)",
      //   backgroundColor: "rgba(255, 99, 132, 0.5)",
      // },
    ],
  };

  return (
    <>
      <Line options={options as LineOptions} data={chartData} />
    </>
  );
}

export default StorageChart;
