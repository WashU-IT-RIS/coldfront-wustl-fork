class FilterableCheckboxTableInput {
  constructor(widgetName, options) {
    this.widgetName = widgetName;
    console.log({ widgetName, options });
    this.options = JSON.parse(options);

    console.log({ options, parsed: this.options });
  }
}
