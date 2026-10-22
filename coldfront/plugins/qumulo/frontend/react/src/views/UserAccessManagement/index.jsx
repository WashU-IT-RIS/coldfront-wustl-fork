import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import UserAccessManagement from "./UserAccessManagement.jsx";
import BulkSuballocationUpdate from "./BulkSuballocationUpdate.jsx";

const bulkConfig = document.getElementById("bulk-attribute-config");

createRoot(document.getElementById("user-access-management")).render(
  <StrictMode>
    {bulkConfig ? (
      <BulkSuballocationUpdate />
    ) : (
      <UserAccessManagement />
    )}
  </StrictMode>
);
