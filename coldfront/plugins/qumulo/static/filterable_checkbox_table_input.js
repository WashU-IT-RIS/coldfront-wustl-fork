class FilterableCheckboxTableInput {
  constructor(widgetName) {
    this.widgetName = widgetName;

    this.options = JSON.parse(
      document.getElementById("checkbox-table-options").textContent
    );
    this.columns = JSON.parse(
      document.getElementById("checkbox-table-columns").textContent
    );

    this.populateOptions();
  }

  populateOptions() {
    const tbody = document.getElementById(`${this.widgetName}-options-tbody`);

    for (const option of this.options) {
      const tr = this.getOptionsRowElement(option);
      tbody.appendChild(tr);
    }
  }

  getOptionsRowElement(option) {
    const tr = document.createElement("tr");
    tr.setAttribute("class", "text-nowrap");

    const checkbox_td = document.createElement("td");

    const checkboxInput = document.createElement("input");
    checkboxInput.setAttribute("type", "checkbox");
    checkboxInput.setAttribute("id", `${this.widgetName}-${option["value"]}`);
    checkboxInput.setAttribute("value", option["value"]);
    checkboxInput.addEventListener("change", this.onOptionChanged);
    checkbox_td.appendChild(checkboxInput);

    tr.appendChild(checkbox_td);

    for (const column of this.columns) {
      const td = this.getOptionsColumnElement(option.label[column]);
      tr.appendChild(td);
    }

    return tr;
  }

  getOptionsColumnElement(value) {
    const td = document.createElement("td");
    td.setAttribute("class", "text-nowrap");
    td.appendChild(document.createTextNode(value));

    return td;
  }

  onOptionChanged(event) {
    const checkboxInput = event.target;
    const isChecked = checkboxInput.checked;

    const optionRow = checkboxInput.parentElement.parentElement;
    const parentTable = optionRow.parentElement;

    console.log({ isChecked, optionRow, parentTable, checkboxInput, event });

    parentTable.removeChild(optionRow);

    const newTable = document.getElementById(
      `${this.widgetName}-${isChecked ? "values" : "options"}-tbody`
    );
    newTable.appendChild(optionRow);
  }
}
