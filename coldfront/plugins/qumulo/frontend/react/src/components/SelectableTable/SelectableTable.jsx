function SelectableTable({ columns }) {
  const renderHeader = () => {
    return columns.map((column) => (
      <th key={column} scope="col" className="text-nowrap">
        {column}
        <a className="sort-asc">
          <i className="fas fa-sort-up" aria-hidden="true"></i>
          <span className="sr-only">Sort {column} asc</span>
        </a>
        <a className="sort-desc">
          <i className="fas fa-sort-down" aria-hidden="true"></i>
          <span className="sr-only">Sort {column} desc</span>
        </a>
      </th>
    ));
  };

  return (
    <div className="table-responsive">
      <table className="table table-sm">
        <thead>
          <tr>
            <th key="checkbox" scope="col" className="text-nowrap">
              {/* <input
                type="checkbox"
                id="select_all"
                name="select_all"
                value="select_all"
              /> */}
            </th>
            {renderHeader()}
          </tr>
        </thead>
        <tbody name="table-values-tbody">
          {/* {% comment %} JS populate this {% endcomment %} */}
        </tbody>
        <tbody name="table-options-tbody">
          {/* {% comment %} JS populate this {% endcomment %} */}
        </tbody>
      </table>
    </div>
  );
}

export default SelectableTable;
