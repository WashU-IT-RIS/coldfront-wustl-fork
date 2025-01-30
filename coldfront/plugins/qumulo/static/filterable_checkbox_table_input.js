class FilterableCheckboxTableInput {
  constructor(widgetName, options, optionsJson) {
    this.widgetName = widgetName;
    console.log({ widgetName, options, optionsJson });
    this.options = JSON.parse(options);
    this.optionsJson = JSON.parse(optionsJson);

    console.log({ options: this.options, optionsJson: this.optionsJson });
  }
}
