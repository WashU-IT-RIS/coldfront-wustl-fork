class FilterableCheckboxTableInput {
  constructor(widgetName, options, optionsJson) {
    this.widgetName = widgetName;
    console.log({ widgetName, options, optionsJson });
    this.options = JSON.parse(optionsJson);
    //
    console.log({ options, parsed: this.options });
  }
}
