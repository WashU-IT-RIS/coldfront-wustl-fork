import { useState } from "react";

import UserSelector from "../../components/UserSelector/UserSelector";
import AllocationSelector from "../../components/AllocationSelector/AllocationSelector";

import "./UserManagement.css";

function UserManagement() {
  const [users, setUsers] = useState(["foo", "bar"]);
  const [allocations, setAllocations] = useState([]);

  return (
    <>
      <UserSelector name="user-selector" users={users} setUsers={setUsers} />
      <AllocationSelector
        setAllocations={setAllocations}
        allocations={allocations}
      />
      <div className="d-flex justify-content-end">
        <button
          type="submit"
          className="btn btn-primary mr-2"
          id="user_management_form_submit"
        >
          Submit
        </button>
      </div>
    </>
  );
}

export default UserManagement;
