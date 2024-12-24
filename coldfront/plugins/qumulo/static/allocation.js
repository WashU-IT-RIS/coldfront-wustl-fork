document.addEventListener("DOMContentLoaded", prepaidDisplayOptions);
const protocols = Array.from(
  document.querySelectorAll(
    "#div_id_protocols div div.form-check input.form-check-input",
  ),
);

const nfsCheckBox = protocols.find((protocol) => protocol.value === "nfs");
const allocationName = document.getElementById("id_storage_name");

nfsCheckBox.addEventListener("change", handleExportPathInput);
allocationName.addEventListener("change", (evt) => {
  document.getElementById("id_storage_filesystem_path").value =
    evt.target.value;
});

if (!nfsCheckBox.checked) {
  document.getElementById("div_id_storage_export_path").style.visibility =
    "hidden";
}

const billOptions = document.getElementById("id_billing_cycle");
if (billOptions.value !== "prepaid") {
  document.getElementById("div_id_prepaid_time").style.visibility = "hidden";
  document.getElementById("div_id_prepaid_billing_date").style.visibility = "hidden";
}
billOptions.addEventListener("change", handlePrepaidCycleSelection);


let confirmed = false;

const submitButton = document.getElementById("allocation_form_submit");
submitButton.addEventListener("click", (event) => {
  const smb = protocols.find((protocol) => protocol.value === "smb"),
    modalShouldDisplay = () => {
      /*
       * bmulligan (20241114): we are now using the document title to
       * determine whether we are on the "Create Allocation" form.
       *
       * NOTE: we're using id_project_pk to determine whether we are
       * on a parent or sub-allocation creation page
       */
      if (document.title.trim() !== "Create Allocation") return false;
      else if (document.getElementById("div_id_project_pk") === null)
        return false;

      return !smb.checked && !confirmed;
    };

  if (modalShouldDisplay()) {
    const modal = $("#smb_warning_modal");
    modal.modal("show");

    event.preventDefault();
  }
});

const dialogSubmitButton = document.getElementById("smb_warning_button_submit");
if (dialogSubmitButton !== null) {
  dialogSubmitButton.addEventListener("click", (event) => {
    confirmed = true;

    const modal = $("#smb_warning_modal");
    modal.modal("hide");

    submitButton.click();
    confirmed = false;
  });
}

function handleExportPathInput(event) {
  const isChecked = event.target.checked;

  if (isChecked) {
    document.getElementById("id_storage_export_path").value = "";
    document.getElementById("div_id_storage_export_path").style.visibility =
      "visible";
  } else {
    document.getElementById("div_id_storage_export_path").style.visibility =
      "hidden";
    document.getElementById("id_storage_export_path").value = "";
  }
}

function handlePrepaidCycleSelection(event) {
  const bill_cycle_value = event.target.value;
  const prepaid_time = document.getElementById("div_id_prepaid_time");
  const prepaid_time_value = document.getElementById("id_prepaid_time").value;

  if (bill_cycle_value !== "prepaid" && prepaid_time_value === "") {
    prepaid_time.style.visibility = "hidden";
    prepaid_time.value = "";
  } else {
    prepaid_time.style.visibility = "visible";
    prepaid_time.value = "";
  }
  handlePrepaidBillingDateDisplay();
}

function handlePrepaidBillingDateDisplay(){
  const bill_cycle_value = document.getElementById("id_billing_cycle").value;
  const prepaid_billing_date = document.getElementById("div_id_prepaid_billing_date");
  const prepaid_billing_date_value = document.getElementById("id_prepaid_billing_date").value;
  const prepaid_billing_date_invalid = document.getElementById("error_1_id_prepaid_billing_date");

  if (bill_cycle_value !== "prepaid" && prepaid_billing_date_value === "") {
    prepaid_billing_date.style.visibility = "hidden";
    prepaid_billing_date.value = "";
    prepaid_billing_date_invalid.style.visibility = "visible";
  } else {
    prepaid_billing_date.style.visibility = "visible";
    prepaid_billing_date.value = "";
  }
}

function prepaidDisplayOptions(){
  const prepaid_billing_date = document.getElementById("div_id_prepaid_billing_date");
  const prepaid_time = document.getElementById("div_id_prepaid_time");

  const bill_cycle_value = document.getElementById("id_billing_cycle").value;
  const prepaid_time_value = document.getElementById("id_prepaid_time").value;
  const prepaid_billing_date_value = document.getElementById("id_prepaid_billing_date").value;

  if (prepaid_time_value !== "" && prepaid_billing_date_value !== "" && bill_cycle_value !== "prepaid") {
    prepaid_billing_date.style.visibility = "visible";
    prepaid_time.style.visibility = "visible";
  } else {
    prepaid_billing_date.style.visibility = "hidden";
    prepaid_time.style.visibility = "hidden";
  }
}
