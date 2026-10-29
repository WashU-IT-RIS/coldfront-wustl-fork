import { useState } from "react";
import axios from "axios";
import Cookies from "universal-cookie";

import AllocationSelector from "../../components/AllocationSelector/AllocationSelector";
import GenericModal from "../../components/GenericModal/GenericModal";

function getValueValidationError(attribute, value) {
  if (!attribute) return "";

  if (attribute.name === "storage_ticket") {
    return /^(?:ITSD-)?\d+$/i.test(value)
      ? ""
      : "Enter a ticket in ITSD-12345 or 12345 format.";
  }

  switch (attribute.attribute_type__name.trim()) {
    case "Int":
      return /^[+-]?\d+$/.test(value) ? "" : "Enter a whole number.";
    case "Float":
      return value.trim() && Number.isFinite(Number(value))
        ? ""
        : "Enter a number.";
    case "Yes/No":
      return value === "Yes" || value === "No" ? "" : "Choose Yes or No.";
    case "Date": {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        return "Enter a date in YYYY-MM-DD format.";
      }
      const date = new Date(`${value}T00:00:00Z`);
      return !Number.isNaN(date.getTime()) &&
        date.toISOString().slice(0, 10) === value
        ? ""
        : "Enter a valid date in YYYY-MM-DD format.";
    }
    case "JSON":
      try {
        JSON.parse(value);
        return "";
      } catch {
        return "Enter valid JSON.";
      }
    default:
      return "";
  }
}

function BulkSuballocationUpdate() {
  const {
    attributeTypes,
    updateUrl,
    billingCycleOptions,
    protocolOptions,
    serviceRateCategories,
  } = JSON.parse(document.getElementById("bulk-attribute-config").textContent);
  const [attributeTypeId, setAttributeTypeId] = useState("");
  const [value, setValue] = useState("");
  const [protocols, setProtocols] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [modal, setModal] = useState(null);

  const selectedType = attributeTypes.find(
    (attribute) => String(attribute.id) === attributeTypeId,
  );
  const isProtocols = selectedType?.name === "storage_protocols";
  const isContactAttribute = ["billing_contact", "technical_contact"].includes(
    selectedType?.name,
  );
  const valueOptions =
    selectedType?.name === "billing_cycle"
      ? billingCycleOptions
      : selectedType?.name === "service_rate_category"
        ? serviceRateCategories
        : selectedType?.attribute_type__name.trim() === "Yes/No"
          ? [
              ["Yes", "Yes"],
              ["No", "No"],
            ]
          : null;
  const valueError = valueOptions
    ? valueOptions.some(([optionValue]) => optionValue === value)
      ? ""
      : "Choose a valid option."
    : getValueValidationError(selectedType, value);

  const onSubmit = async () => {
    setSubmitting(true);
    try {
      if (isContactAttribute) {
        const response = await axios.get(
          "/qumulo/api/active-directory-members",
          { params: { members: [value] } },
        );
        const validUsers = response.data.validNames;
        if (!validUsers.includes(value)) {
          setModal({
            title: "Invalid User",
            text: `The following user was not found: ${value}`,
          });
          return;
        }
      }

      const response = await axios.post(
        updateUrl,
        {
          attributeTypeId,
          value: isProtocols ? JSON.stringify(protocols) : value,
          allocationIds: allocations.map((allocation) => allocation.id),
        },
        { headers: { "X-CSRFToken": new Cookies().get("csrftoken") } },
      );
      setModal({
        title: "Attributes Updated",
        text: `Updated ${response.data.updatedAllocations} allocation(s).`,
      });
    } catch (error) {
      setModal({
        title: "Update Failed",
        text:
          error.response?.data?.error ||
          "Unable to update allocation attributes. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <h2>Bulk Suballocation Update</h2>
      <p>
        Choose an attribute and enter a value to apply to all selected
        allocations. Existing values will be replaced; missing attributes will
        be added. This updates ColdFront metadata only, not storage
        configuration or user access.
      </p>
      <hr />
      <div className="form-group">
        <label htmlFor="allocation-attribute-type">Allocation Attribute</label>
        <select
          id="allocation-attribute-type"
          className="form-control"
          value={attributeTypeId}
          disabled={submitting}
          onChange={(event) => {
            setAttributeTypeId(event.target.value);
            setValue("");
            setProtocols([]);
          }}
        >
          <option value="">Select an attribute</option>
          {attributeTypes.map((attribute) => (
            <option key={attribute.id} value={attribute.id}>
              {attribute.name}
            </option>
          ))}
        </select>
        {attributeTypes.length === 0 && (
          <p role="alert">No allocation attribute types are configured.</p>
        )}
      </div>
      {isProtocols ? (
        <fieldset className="form-group" disabled={submitting}>
          <legend className="col-form-label pt-0">Protocols</legend>
          {protocolOptions.map(([optionValue, optionLabel]) => (
            <div className="form-check" key={optionValue}>
              <input
                id={`protocol-${optionValue}`}
                className="form-check-input"
                type="checkbox"
                checked={protocols.includes(optionValue)}
                onChange={(event) => {
                  setProtocols((currentProtocols) =>
                    event.target.checked
                      ? [...currentProtocols, optionValue]
                      : currentProtocols.filter(
                          (protocol) => protocol !== optionValue,
                        ),
                  );
                }}
              />
              <label
                className="form-check-label"
                htmlFor={`protocol-${optionValue}`}
              >
                {optionLabel}
              </label>
            </div>
          ))}
        </fieldset>
      ) : (
        <div className="form-group">
          <label htmlFor="allocation-attribute-value">
            Value{selectedType ? ` (${selectedType.attribute_type__name})` : ""}
          </label>
          {valueOptions ? (
            <select
              id="allocation-attribute-value"
              className="form-control"
              value={value}
              disabled={submitting}
              aria-invalid={Boolean(valueError)}
              onChange={(event) => setValue(event.target.value)}
            >
              <option value="">Select a value</option>
              {valueOptions.map(([optionValue, optionLabel]) => (
                <option key={optionValue} value={optionValue}>
                  {optionLabel}
                </option>
              ))}
            </select>
          ) : ["Int", "Float", "Date"].includes(
              selectedType?.attribute_type__name.trim(),
            ) ? (
            <input
              id="allocation-attribute-value"
              className="form-control"
              type={
                selectedType.attribute_type__name.trim() === "Date"
                  ? "date"
                  : "number"
              }
              step={
                selectedType.attribute_type__name.trim() === "Int" ? "1" : "any"
              }
              value={value}
              maxLength={8192}
              placeholder={
                selectedType?.name === "storage_ticket"
                  ? "ITSD-12345 or 12345"
                  : undefined
              }
              disabled={submitting}
              aria-invalid={Boolean(valueError)}
              onChange={(event) => setValue(event.target.value)}
            />
          ) : (
            <textarea
              id="allocation-attribute-value"
              className="form-control"
              value={value}
              maxLength={8192}
              disabled={submitting}
              aria-invalid={Boolean(valueError)}
              onChange={(event) => setValue(event.target.value)}
            />
          )}
          {value && valueError && <p role="alert">{valueError}</p>}
        </div>
      )}
      <AllocationSelector
        setSelectedAllocations={setAllocations}
        selectedAllocations={allocations}
        label="Allocations"
      />
      <div className="d-flex justify-content-end">
        <button
          type="button"
          className="btn btn-primary mr-2"
          disabled={
            submitting ||
            !attributeTypeId ||
            (!isProtocols && !value) ||
            allocations.length === 0 ||
            Boolean(valueError)
          }
          onClick={onSubmit}
        >
          {submitting ? "Updating..." : "Update Attributes"}
        </button>
      </div>
      {modal && (
        <GenericModal
          title={modal.title}
          text={modal.text}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}

export default BulkSuballocationUpdate;
