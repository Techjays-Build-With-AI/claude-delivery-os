# UI consistency — writing a screen that belongs in this app

**Purpose.** `pattern-inference.md` makes new code structurally match the repo. This makes it *look*
like the repo. Both halves matter: a section that imports correctly and names things correctly, then
renders its own fonts, its own spacing and its own colours, reads as bolted on — because it is.

**Budget.** ≤ 4 targeted reads, on top of pattern-inference's. Stack-agnostic: web, mobile and
desktop all have a component library, a token source and a set of primitives, whatever they are
called.

---

## 1. Detect the system before writing anything

| Look for | Where | What you get |
|---|---|---|
| **Component library** | the dependency manifest | Bootstrap, Tailwind, MUI, Chakra, Ant, SwiftUI, Compose, Flutter widgets |
| **Token source** | `:root` CSS vars, a theme file, `tailwind.config`, a design-tokens module | the real colours, type scale and spacing steps |
| **Layout primitives** | one existing page | the container/row/column or stack/grid wrappers every screen uses |
| **Shared components** | the shared/common folder | the table, form field, button, modal, empty state you are expected to reuse |

If the repo has no library and no tokens, say so in the build summary and pick **one** approach for
the whole feature. Inventing a second system beside an existing one is the failure this prevents.

---

## 2. Five rules, and they are hard

**Reuse before you create.** Search the shared folder for a component that does the job. Write a new
one only when nothing fits, and compose it from the primitives already there. A second table
implementation in a repo that has one is a defect, not a style choice.

**Never add a second UI library.** Whatever the manifest already has is the library. Adding another
to get one component is how an app ends up with three button styles.

**No hardcoded visual values where a token exists.** No hex colours, no `px` font sizes, no magic
spacing. Use the variable, the theme key or the library's scale. Where no token exists, use the
library's own default scale rather than a number you chose.

**Match the neighbour, not your taste.** Open the section that will sit next to yours and copy its
shape: same container, same heading level, same spacing rhythm, same table and form components, same
empty and loading states. Consistency with one real neighbour beats any general principle.

**No new stylesheet when the repo has a system.** A per-component `.css` file alongside a
Bootstrap or Tailwind app means the system was ignored. Extend the existing stylesheet or use the
library's utilities.

---

## 3. What the build summary must say

One line, so a reviewer can check it rather than take it on trust. The shape is
`UI: <library> · tokens from <source> · reused <components> · new <components>`; the example below
happens to be a web stack, and reads the same for a mobile or desktop one:

```
UI: react-bootstrap · tokens from src/styles/_variables.scss · reused DataTable, FormField, EmptyState
    new: AssetFilters (composes Row/Col/Form.Control) · no new stylesheet
```

If you had to break a rule, name which and why. An unexplained break reads as an oversight.

---

## 4. Not in scope here

Visual design *decisions* — what a new screen should look like when the repo gives no precedent — are
a `PB-###` for the human, not something to invent at build time. This file is about following what
already exists, not about designing what does not.
