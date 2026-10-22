import { useState } from "react";
import axios from "axios";
import Cookies from "universal-cookie";

import AllocationSelector from "../../components/AllocationSelector/AllocationSelector";
import GenericModal from "../../components/GenericModal/GenericModal";

function BulkSuballocationUpdate() {
  const { attributeTypes, updateUrl } = JSON.parse(
    document.getElementById("bulk-attribute-config").textContent
  );
  const [attributeTypeId, setAttributeTypeId] = useState("");
  const [value, setValue] = useState("");
  const [allocations, setAllocations] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [modal, setModal] = useState(null);

  const selectedType = attributeTypes.find(
    (attribute) => String(attribute.id) === attributeTypeId
  );

  const onSubmit = async () => {
    setSubmitting(true);
    try {
      const response = await axios.post(
        updateUrl,
        {
          attributeTypeId,
          value,
          allocationIds: allocations.map((allocation) => allocation.id),
        },
        { headers: { "X-CSRFToken": new Cookies().get("csrftoken") } }
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
        Choose an attribute and enter a value to apply to all selected allocations.
        Existing values will be replaced; missing attributes will be added.
        This updates ColdFront metadata only, not storage configuration or user access.
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
      <div className="form-group">
        <label htmlFor="allocation-attribute-value">
          Value{selectedType ? ` (${selectedType.attribute_type__name})` : ""}
        </label>
        <textarea
          id="allocation-attribute-value"
          className="form-control"
          value={value}
          maxLength={8192}
          disabled={submitting}
          onChange={(event) => setValue(event.target.value)}
        />
      </div>
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
            submitting || !attributeTypeId || !value || allocations.length === 0
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
