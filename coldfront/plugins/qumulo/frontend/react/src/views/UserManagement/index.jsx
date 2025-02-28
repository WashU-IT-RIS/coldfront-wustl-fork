import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import UserManagement from "./UserManagment.jsx";

createRoot(document.getElementById("user-management")).render(
  <StrictMode>
    <UserManagement />
  </StrictMode>
);
