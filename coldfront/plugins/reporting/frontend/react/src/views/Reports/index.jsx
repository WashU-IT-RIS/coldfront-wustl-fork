import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Reports from "./Reports.jsx";

createRoot(document.getElementById("reports")).render(
  <StrictMode>
    <Reports />
  </StrictMode>,
);
