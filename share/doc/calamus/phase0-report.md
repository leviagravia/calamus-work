# Calamus phase 0 stabilization

Applied conservative package/code hygiene changes:

- aligned runtime About dialog version with the `VERSION` constant;
- bumped Debian package version to `1.7.0~rc2+phase0`;
- replaced obsolete About text claiming direct Leafpad basis with a more accurate “inspired by Leafpad/Mousepad-style” wording;
- removed the older duplicate `highlight_all_search()` implementation that was shadowed later in the file;
- narrowed top-level JSON/integer helper exception handlers from broad `Exception` to expected exception classes;
- verified no `__pycache__` files are installed by this package.

No feature behavior was intentionally changed in this phase.
