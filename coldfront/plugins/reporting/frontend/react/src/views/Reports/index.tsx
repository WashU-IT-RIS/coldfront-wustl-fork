import { StrictMode } from "react";
import { Container, createRoot } from "react-dom/client";
import Reports from "./Reports.js";

createRoot(document.getElementById("reports") as Container).render(
  <StrictMode>
    <Reports />
  </StrictMode>,
);
