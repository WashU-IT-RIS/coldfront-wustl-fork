class FilterableCheckboxTableInput {
  constructor(widgetName) {
    const options = document.getElementById(
      `${widgetName}-options`
    ).textContent;
    this.widgetName = widgetName;
    console.log({ widgetName, options: options });
    this.options = JSON.parse(options);

    console.log({ options: this.options });
  }
}
