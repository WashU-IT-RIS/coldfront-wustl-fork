# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Bulk allocation attribute updates

The Bulk Suballocation Update page uses the shared UserAccessManagement bundle.
Django supplies all allocation attribute types and the update URL through the
`bulk-attribute-config` JSON script. Without that configuration, the bundle renders
the existing RW/RO user-management page.

Superusers can select an attribute, enter a value and choose storage allocations.
The value replaces all existing entries of that type on each selected allocation,
or creates an entry when missing. Values are validated using ColdFront's attribute
validators, and the entire batch is rolled back if any value is invalid. This edits
ColdFront metadata only; it does not provision storage changes or modify AD access.

Build from this directory with `node build.js`, then deploy the generated `dist`
assets through the normal static-file deployment process.
