import { useState } from "react";

function InputLabel({ label, value = "", onChange }) {
  const [isActive, setIsActive] = useState(false);
  const [internalValue, setInternalValue] = useState(value);

  const onKeyDown = (event) => {
    if (event.key === "Enter") {
      onChange(internalValue);
      setIsActive(false);
    }
  };

  return (
    <>
      {!isActive && !value ? (
        <span onClick={() => setIsActive(true)}>{label}</span>
      ) : (
        <input
          type="text"
          value={internalValue}
          onChange={(e) => setInternalValue(e.target.value)}
          onKeyDown={onKeyDown}
          autoFocus
        />
      )}
    </>
  );
}

export default InputLabel;
