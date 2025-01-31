class FilterableCheckboxTableInput {
  constructor(widgetName, optionsName) {
    const options = document.getElementById(optionsName).textContent;
    this.widgetName = widgetName;
    console.log({ widgetName, options: options });
    this.options = JSON.parse(options);

    console.log({ options: this.options });
  }
}
