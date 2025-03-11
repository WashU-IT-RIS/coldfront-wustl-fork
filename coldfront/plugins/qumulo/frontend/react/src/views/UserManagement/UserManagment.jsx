import { useState } from "react";

import UserSelector from "../../components/UserSelector/UserSelector";
import AllocationSelector from "../../components/AllocationSelector/AllocationSelector";

import "./UserManagement.css";

import axios from "axios";
import Cookies from "universal-cookie";

function UserManagement() {
  const [rwUsers, setRwUsers] = useState([]);
  const [roUsers, setRoUsers] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const cookies = new Cookies();
  const csrfToken = cookies.get("csrftoken");

  const onSubmit = () => {
    const allocationIds = allocations.map((allocation) => allocation.id);

    axios
      .post(
        "user-management",
        {
          rwUsers,
          roUsers,
          allocationIds: allocationIds,
        },
        {
          headers: {
            "X-CSRFToken": csrfToken,
          },
        }
      )
      .then((response) => {
        console.log(response);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  return (
    <>
      <UserSelector
        name="rw-user-selector"
        users={rwUsers}
        setUsers={setRwUsers}
        label={"Read/Write Users"}
      />
      <UserSelector
        name="ro-user-selector"
        users={roUsers}
        setUsers={setRoUsers}
        label={"Read-Only Users"}
      />
      <AllocationSelector
        setSelectedAllocations={setAllocations}
        selectedAllocations={allocations}
        label={"Allocations"}
      />
      <div className="d-flex justify-content-end">
        <button
          type="submit"
          className="btn btn-primary mr-2"
          id="user_management_form_submit"
          onClick={onSubmit}
        >
          Submit
        </button>
      </div>
    </>
  );
}

export default UserManagement;
