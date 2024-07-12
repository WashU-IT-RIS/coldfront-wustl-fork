const nfsCheckBox = document.getElementById("id_protocols_0");
nfsCheckBox.addEventListener("change", handleExportPathInput);

if (!nfsCheckBox.checked) {
  document.getElementById("div_id_storage_export_path").style.visibility =
    "hidden";
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
