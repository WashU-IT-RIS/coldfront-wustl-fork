class FilterableCheckboxTableInput {
  constructor(widgetName, optionsName) {
    const options = document.getElementById(optionsName);
    this.widgetName = widgetName;
    console.log({ widgetName, options: options });
    this.options = JSON.parse(options.textContent);

    console.log({ options: this.options });
  }
}
