class FilterableCheckboxTableInput {
  constructor(widgetName, options) {
    this.widgetName = widgetName;
    console.log({ widgetName, options: options.replace(/'/g, '"') });
    this.options = JSON.parse(options.replace(/'/g, '"'));

    console.log({ options: this.options });
  }
}
