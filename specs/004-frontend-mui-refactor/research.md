# Research: Frontend MUI Refactor

**Research Date**: 2026-04-17  
**Feature**: Frontend MUI Migration  
**Researcher**: Claude

---

## Research Areas

### RA-1: MUI v6 Migration Best Practices

**Context**: Need to migrate from vanilla CSS to MUI v6 with minimal disruption

**Findings**:

| Aspect | Best Practice | Rationale |
|--------|---------------|-----------|
| Bundle Size | Use path imports (`@mui/material/Button`) not barrel imports | Tree-shaking works better, reduces bundle by ~40% |
| Theme Setup | Create theme.ts with design tokens, useTheme hook | Centralized design system, consistent overrides |
| CSS Interop | Keep old CSS during migration, wrap components | Incremental migration without breaking changes |
| Performance | Lazy load heavy components (DataGrid) | Improves initial load time |
| TypeScript | Use `satisfies` operator for theme extensions | Better type inference for custom properties |

**Decision**: Use incremental migration with ThemeProvider at root, path imports for tree-shaking.

---

### RA-2: Responsive Breakpoint Strategy

**Context**: Current vanilla CSS uses custom media queries; need MUI equivalent

**Decision**: Map existing breakpoints to MUI defaults (xs:0, sm:600, md:900, lg:1200, xl:1536)

**Migration**:
```css
/* Old */
@media (max-width: 768px) { }

/* New MUI */
const theme = createTheme({
  breakpoints: {
    values: { xs: 0, sm: 600, md: 900, lg: 1200, xl: 1536 }
  }
})
// use: sx={{ display: { xs: 'none', md: 'block' } }}
```

---

### RA-3: Component Migration Priority

**Priority Order** (based on dependency graph):

1. **Layout First** (blocks everything else)
   - App shell (AppBar, Drawer)
   - Page containers
   - Grid layouts

2. **Forms Second** (highest user interaction)
   - LoginForm (simplest, good test case)
   - RoleEditor, CompositionEditor
   - Settings forms

3. **Data Display Third**
   - Tables → DataGrid (highest complexity)
   - Cards, Lists
   - Status indicators

4. **Feedback Last**
   - Loading states
   - Alerts, Snackbars
   - Dialogs

---

### RA-4: DataGrid Configuration

**MUI X DataGrid** replaces custom tables with built-in features:

| Feature | Configuration |
|---------|-----------------|
| Sorting | `disableColumnFilter={false}` (default on) |
| Filtering | Built-in with `slots={{ toolbar: GridToolbar }}` |
| Pagination | `paginationModel` with server-side or client-side |
| Selection | `checkboxSelection` for bulk actions |
| Editing | `editMode="row"` or `"cell"` for inline editing |

**Decision**: Use DataGrid Pro patterns (even with free version) for future upgrade path.

---

### RA-5: Theme Customization for Syntexa Brand

**Color Palette** (assuming brand colors - to be confirmed):

| Token | Suggested Value | Usage |
|-------|---------------|-------|
| primary.main | `#1976d2` | Actions, links |
| primary.dark | `#115293` | Hover states |
| secondary.main | `#dc004e` | Accent, CTAs |
| background.default | `#f5f5f5` | Page background |
| background.paper | `#ffffff` | Cards, sheets |

**Typography**: Use MUI defaults (Roboto) or system font stack.

---

### RA-6: Accessibility (WCAG 2.1 AA)

**MUI Built-in**:
- Focus management on Dialogs, Menus
- ARIA labels on IconButton
- Keyboard navigation in DataGrid
- High contrast mode support

**Manual Checks Needed**:
- Color contrast verification (use Polished or a11y addon)
- Focus indicators visible
- Form labels associated

---

## Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Migration Strategy | Incremental per-page | Lower risk, maintain functionality |
| Import Pattern | Path imports | Tree-shaking, smaller bundles |
| Theme Approach | Single theme file + CssBaseline | Centralized, easy to modify |
| Dark Mode | localStorage + system preference | User expectation, simple to add |
| Table Replacement | DataGrid | Rich features, less custom code |
| CSS Coexistence | Yes during migration | Allows gradual transition |

---

## Open Questions Addressed

1. **Bundle size concern?** → Tree-shaking with path imports, <50KB increase target
2. **Theme flash on load?** → Set theme class before render, localStorage sync
3. **Custom CSS needed?** → Use `sx` prop or `styled()` for overrides
4. **Responsive behavior?** → MUI Grid with breakpoints, mobile-first

---

## References

- MUI v6 Migration Guide: https://mui.com/material-ui/migration/migration-v5/
- DataGrid Documentation: https://mui.com/x/react-data-grid/
- Theme Customization: https://mui.com/material-ui/customization/theming/
