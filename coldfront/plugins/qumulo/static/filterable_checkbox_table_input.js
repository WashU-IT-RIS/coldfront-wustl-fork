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

    console.log({ widgetName, options: this.options });
  }

  populateOptions() {
    const tbody = document.getElementById(`${this.widgetName}-options-tbody`);

    for (const option of this.options) {
      const tr = this.getOptionsRowElement(option);
      tbody.appendChild(tr);
    }
  }

  getOptionsRowElement = (option) => {
    const tr = document.createElement("tr");
    tr.setAttribute("class", "text-nowrap");

    const checkbox_td = document.createElement("td");
    const checkboxInput = document.createElement("input");
    checkboxInput.setAttribute("type", "checkbox");
    checkboxInput.setAttribute("id", `${this.widgetName}-${option["value"]}`);
    checkboxInput.setAttribute("value", option["value"]);
    checkbox_td.appendChild(checkboxInput);

    for (const value of Object.values(Object.label)) {
      const td = this.getOptionsColumnElement(value);
      tr.appendChild(td);
    }

    return tr;
  };

  getOptionsColumnElement = (value) => {
    const td = document.createElement("td");
    td.setAttribute("class", "text-nowrap");
    td.appendChild(document.createTextNode(value));

    return td;
  };
}
