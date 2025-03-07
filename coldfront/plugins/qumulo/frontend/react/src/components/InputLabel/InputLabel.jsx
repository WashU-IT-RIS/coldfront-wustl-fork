import { useActionState, useState } from "react";

function InputLabel({ label, value = "", onChange }) {
  const [isActive, setIsActive] = useState(false);
  const [internalValue, setInternalValue] = useState(value);

  const onKeyDown = (event) => {
    if (event.key === "Enter") {
      onChange(internalValue);
    }
  };

  return (
    <>
      {!isActive ? (
        <span onClick={() => setIsActive(true)}>{label}</span>
      ) : (
        <input
          type="text"
          value={internalValue}
          onChange={(e) => setInternalValue(e.target.value)}
          onKeyDown={onKeyDown}
        />
      )}
    </>
  );
}

export default InputLabel;
