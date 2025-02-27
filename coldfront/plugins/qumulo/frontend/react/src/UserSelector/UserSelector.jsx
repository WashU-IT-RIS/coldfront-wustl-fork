import { useState } from 'react'

import "./UserSelector.css"

function UserSelector({name, users, setUsers}) {
  const [inputText, setInputText] = useState("")
  const [selectedUsers, setSelectedUsers] = useState([])

  const handleAddButtonClick = (event) => {
    const values = inputText
      .split(",")
      .map((value) => value.trim())
      .filter((value) => value.length);

    setUsers([...users, ...values]);
    setInputText("");
  };

  const handleRemoveButtonClick = (event) => {
    setSelectedUsers([]);
    setUsers(users.filter((user) => !selectedUsers.includes(user)));

  };

  const onListItemClick = (event) => {
    const listItemElement = event.target;

    if (selectedUsers.includes(listItemElement.textContent)) {
      setSelectedUsers(selectedUsers.filter((user) => user !== listItemElement.textContent));
    }
    else {
      setSelectedUsers([...selectedUsers, listItemElement.textContent]);
    }
  };

  const isSelected = (user) => selectedUsers.includes(user) ? "selected" : ""

  return (
    <>
      <p id={`${name}-error-message`} className="invalid-feedback"><strong></strong></p>
      <div className="d-flex flex-row justify-content-between">
        <textarea
          id={`${name}-textarea`}
          className="align-self-start"
          rows="4"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        ></textarea>
        <div>
        <button 
          id={`${name}-add-button`}
          type="button"
          className="btn btn-outline-primary btn-sm align-self-start"
          onClick={handleAddButtonClick}
        >
          {'>'}{'>'}
        </button>
        <button 
          id={`${name}-remove-button`}
          type="button"
          className="btn btn-outline-primary btn-sm align-self-start"
          onClick={handleRemoveButtonClick}
        >
          {'<'}{'<'}
        </button>
      </div>
        <ul id={`${name}-output-list`} class="list-group multi-select-lookup">
          {users.map((user) => (
            <li className={`multi-select-lookup list-group-item d-flex flex-row justify-content-between ${isSelected(user)}`} onClick={onListItemClick}>
              {user}
            </li>
          ))}
        </ul>
      </div>
      </>
  )
}

export default UserSelector