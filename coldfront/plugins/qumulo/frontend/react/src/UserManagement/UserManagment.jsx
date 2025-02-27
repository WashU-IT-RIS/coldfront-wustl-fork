import { useState } from 'react'

import UserSelector from '../UserSelector/UserSelector'
import AllocationSelector from '../AllocationSelector/AllocationSelector'

import './UserManagement.css'

function UserManagement() {
  const [users, setUsers] = useState(['foo', 'bar'])

  return (
    <>
      <UserSelector name="user-selector" users={users} setUsers={setUsers} />
      <AllocationSelector />
      <div className="d-flex justify-content-end">
        <button type="submit" className="btn btn-primary mr-2" id="user_management_form_submit">Submit</button>
      </div>
    </>
  )
}

export default UserManagement
