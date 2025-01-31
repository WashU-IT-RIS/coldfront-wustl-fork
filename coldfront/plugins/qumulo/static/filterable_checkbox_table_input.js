class FilterableCheckboxTableInput {
  constructor(widgetName) {
    this.widgetName = widgetName;

    this.options = JSON.parse(
      document.getElementById("checkbox-table-options").textContent
    );
    this.columns = JSON.parse(
      document.getElementById("checkbox-table-columns").textContent
    );

    console.log({ widgetName, options: this.options });
  }
}
