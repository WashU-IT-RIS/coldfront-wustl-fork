class FilterableCheckboxTableInput {
  constructor(widgetName, options, optionsPprint) {
    this.widgetName = widgetName;
    console.log({ widgetName, options, optionsPprint });
    this.options = JSON.parse(optionsPprint);

    console.log({ options, parsed: this.options });
  }
}
