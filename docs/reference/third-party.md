# Reference sources and licensing

The frontend is a Databrix implementation informed by Compass navigation, lesson layout, and table-of-contents behavior.
It imports no Compass course/interview media or unrelated demo teaching content.
The original reference at `/Users/tinvotan/Projects/compass-ts` is left unchanged.
Compass's Tailwind Plus license is retained verbatim in [COMPASS-LICENSE.md](../../licenses/COMPASS-LICENSE.md).

The shared primitives are vendored from the official shadcn new-york-v4 registry and adapted to workspace imports/tokens.
Upstream license: [SHADCN-LICENSE.txt](../../licenses/SHADCN-LICENSE.txt).
The package layout follows next-forge's design-system pattern; unrelated next-forge services are not copied.
The scoped-documentation pattern is inspired by Streamify; Databrix's canonical file is AGENTS.md.

`legacy/homepage` retains original marketing/legal sources for traceability.
`legacy/data` preserves old tracked and ignored working files; it is not included in application image contexts.
Obsolete tests are archived as historical evidence and replaced by discoverable policy/storage/migration tests.
Retained archives and third-party license files are excluded from the owned Markdown length rule.
