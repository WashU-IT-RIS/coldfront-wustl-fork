class FilterableCheckboxTableInput {
  constructor(widgetName) {
    options = document.getElementById(`foo`).textContent;
    this.widgetName = widgetName;
    console.log({ widgetName, options: options });
    this.options = JSON.parse(options);

    console.log({ options: this.options });
  }
}
