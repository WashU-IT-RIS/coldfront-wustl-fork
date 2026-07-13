import { useState } from "react";

import axios from "axios";
import Cookies from "universal-cookie";

import Storage from "../../components/Storage/Storage";

function Reports() {
  return (
    <>
      <h2>Reports</h2>

      <Storage />
    </>
  );
}

export default Reports;
