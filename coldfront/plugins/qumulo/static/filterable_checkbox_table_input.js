class FilterableCheckboxTableInput {
  constructor(widgetName, options) {
    this.widgetName = widgetName;
    this.options = JSON.parse(options);

    console.log({ options, parsed: this.options });
  }
}
