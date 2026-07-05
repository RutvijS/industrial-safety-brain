/**
 * DataTable — Reusable table component for plant data.
 *
 * Props:
 *   columns  - Array of { key, label } objects defining columns
 *   data     - Array of row objects
 *   loading  - Boolean for loading state
 *   error    - Error message string (or null)
 *   title    - Section title
 *   icon     - Emoji icon for the title
 */

import { useState } from "react";

function DataTable({ columns, data, loading, error, title, icon }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <section className="data-section">
      <button
        className="data-section__header"
        onClick={() => setCollapsed(!collapsed)}
        aria-expanded={!collapsed}
      >
        <span className="data-section__icon">{icon}</span>
        <h2 className="data-section__title">{title}</h2>
        <span className="data-section__count">
          {!loading && !error && `${data.length} records`}
        </span>
        <span className={`data-section__chevron ${collapsed ? "" : "data-section__chevron--open"}`}>
          &#9660;
        </span>
      </button>

      {!collapsed && (
        <div className="data-section__body">
          {loading && (
            <div className="data-section__state">
              <div className="data-section__spinner" />
              <p>Loading data...</p>
            </div>
          )}

          {error && (
            <div className="data-section__state data-section__state--error">
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && data.length === 0 && (
            <div className="data-section__state">
              <p>No records available</p>
            </div>
          )}

          {!loading && !error && data.length > 0 && (
            <div className="data-table__wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col.key}>{col.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, idx) => (
                    <tr key={idx}>
                      {columns.map((col) => (
                        <td key={col.key}>
                          {col.render
                            ? col.render(row[col.key], row)
                            : row[col.key] ?? "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default DataTable;
