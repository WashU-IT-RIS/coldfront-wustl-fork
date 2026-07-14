import { faker } from "@faker-js/faker";
import StorageChart from "../StorageChart/StorageChart";

function Storage() {
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const data = {
    usage: months.map((_, index) => ({
      x: `2025-${index + 1}-${faker.number.int({ min: 1, max: 28 })}`,
      y: faker.number.int({ min: 0, max: 1000 }),
    })),
    quota: months.map((_, index) => ({
      x: `2025-${index + 1}-01`,
      y: 1000,
    })),
  };

  return (
    <>
      <h3>Storage Usage</h3>
      <StorageChart data={data} />
    </>
  );
}

export default Storage;
