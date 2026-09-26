# LexLens --- Design Plan

> **Status:** Approved / Build-Ready\
> **Required reading before implementation:** `IMPLEMENTATION_PLAN.md`
> **and** `design_plan.md`\
> **Primary visual reference:** `UI_screens/screens.jpeg`\
> **Latest approved UI reference supplied in this conversation:** the
> 3×3 LexLens screen sheet containing Landing, Upload, Document Ready,
> Intent Cards, Analysis, Document Viewer, Potential Inconsistencies,
> Not Determined, and Prepare for a Lawyer.

------------------------------------------------------------------------

# 0. Mandatory Agent Instruction

## READ BEFORE BUILDING

The implementation agent **MUST read both files before writing or
modifying application code**:

``` text
IMPLEMENTATION_PLAN.md
design_plan.md
```

The agent must also inspect:

``` text
UI_screens/screens.jpeg
```

before implementing the frontend.

These files have different responsibilities:

### `IMPLEMENTATION_PLAN.md`

Defines:

-   Product problem
-   Product scope
-   Architecture
-   Backend
-   AI behavior
-   Evidence model
-   Security
-   Accessibility
-   API/data requirements
-   Testing
-   Demo requirements
-   Definition of done

### `design_plan.md`

Defines:

-   Visual system
-   Layout
-   Screen composition
-   Component hierarchy
-   Interaction behavior
-   Responsive behavior
-   Typography
-   Color usage
-   Spacing
-   Visual states
-   Animation
-   Evidence/highlight interaction
-   Frontend fidelity requirements

**Do not start frontend implementation until both documents and the
reference image have been reviewed.**

------------------------------------------------------------------------

# 1. Design Objective

LexLens should feel like a **modern legal-document workspace**, not an
AI chatbot.

The visual experience should communicate:

> **Understand what you're signing.**

The UI should make the user feel that they are:

1.  Looking at their document.
2.  Choosing what they want to understand.
3.  Receiving structured assistance.
4.  Being shown exactly where the information came from.
5.  Able to verify it themselves.
6.  Able to identify what the document does not answer.

The design must prioritize **clarity, trust, evidence, and usability**
over visual complexity.

------------------------------------------------------------------------

# 2. Approved Visual Direction

The supplied 3×3 UI reference is the visual source of truth.

The overall visual language is:

-   Light
-   Minimal
-   Professional
-   Friendly
-   Spacious
-   Rounded
-   Soft
-   Modern SaaS
-   Evidence-oriented
-   Purple/indigo primary accent
-   Subtle green success states
-   Yellow evidence highlighting
-   Soft neutral backgrounds
-   Thin borders
-   Low-intensity shadows

Do not replace this with:

-   Dark mode as the primary design
-   Neon/cyberpunk UI
-   Glassmorphism-heavy UI
-   Enterprise-heavy dashboards
-   Dense legal software styling
-   ChatGPT-clone styling
-   Excessive gradients
-   Excessive animation

------------------------------------------------------------------------

# 3. Brand / Visual Identity

## 3.1 Brand

Product name:

**LexLens**

The logo should be simple and recognizable at small sizes.

Use the logo consistently in:

-   Landing navigation
-   Application navigation
-   Document workspace
-   Authentication surfaces
-   Footer

------------------------------------------------------------------------

# 4. Color System

The reference uses a very light interface with an indigo/purple primary
accent.

Use semantic design tokens rather than hardcoding colors throughout
components.

Suggested tokens:

``` css
:root {
  --background: #f7f8fc;
  --surface: #ffffff;
  --surface-muted: #f5f6fb;

  --text-primary: #101536;
  --text-secondary: #5f6478;
  --text-muted: #8b90a3;

  --primary: #5547e8;
  --primary-dark: #4437cf;
  --primary-soft: #eeecff;

  --border: #e5e7ef;
  --border-strong: #d7dae6;

  --success: #22b573;
  --success-soft: #e8f8f0;

  --warning: #f2a72b;
  --warning-soft: #fff5df;

  --danger: #e45b68;
  --danger-soft: #fff0f2;

  --evidence: #fff1a8;
  --info: #4386e8;
  --info-soft: #edf5ff;
}
```

These values are a starting design token system. The agent should tune
them against the supplied reference rather than treating every hex value
as immutable.

## Color rules

### Primary purple/indigo

Use for:

-   Main CTA
-   Active navigation
-   Selected cards
-   Primary links
-   Key interactive elements

### Green

Use for:

-   Successful processing
-   Explicitly stated
-   Verified evidence
-   Successful upload

### Yellow

Use **specifically and consistently** for:

-   Evidence highlighting inside the document viewer

The yellow highlight is a core product interaction and should remain
visually recognizable.

### Orange/yellow warning

Use for:

-   Potential inconsistencies
-   Attention-needed states
-   Review warnings

### Red

Use sparingly for:

-   Serious attention states
-   Validation errors
-   Destructive actions

Do not use red to imply that a clause is legally wrong.

------------------------------------------------------------------------

# 5. Typography

Use a modern sans-serif typeface.

Recommended:

``` text
Inter
```

or an equivalent highly legible system sans-serif.

Typography hierarchy:

``` text
Hero
48–64px desktop

Page title
28–36px

Section title
20–24px

Card title
14–17px

Body
14–16px

Supporting text
12–14px

Metadata
11–13px
```

The exact sizes should be tuned to the viewport and screenshot.

## Typography rules

-   Strong hierarchy
-   Short paragraphs
-   Comfortable line height
-   Avoid legal-document walls of text in the UI
-   Preserve exact legal wording only inside evidence/source contexts
-   Use bold selectively

------------------------------------------------------------------------

# 6. Layout System

Use a centered application shell.

Desktop:

``` text
┌───────────────────────────────────────────────┐
│ Navigation                                    │
├───────────────────────────────────────────────┤
│                                               │
│ Main content                                  │
│                                               │
│                                               │
└───────────────────────────────────────────────┘
```

Recommended:

``` text
max-width: 1440px
page padding: 24–40px
card radius: 12–18px
```

The reference uses generous whitespace.

Do not make the interface fill every available pixel with content.

------------------------------------------------------------------------

# 7. Border / Radius / Shadow System

Cards should have:

``` text
border: 1px solid var(--border)
border-radius: 12–16px
```

Shadows should be subtle:

``` text
0 4px 20px rgba(...)
```

Avoid dramatic shadows.

Buttons:

``` text
border-radius: 8–10px
```

Larger hero/feature cards:

``` text
border-radius: 16–20px
```

------------------------------------------------------------------------

# 8. Global Navigation

The application navigation in the reference is intentionally minimal.

Desktop structure:

``` text
[LexLens]       Home    My Documents                 [Avatar]
```

Landing page may use:

``` text
[LexLens]       Home    How it works    Features    FAQ
                                      [Sign in] [Get started]
```

Inside the application:

``` text
[LexLens]       Home    My Documents                         [S]
```

The navigation should never dominate the screen.

------------------------------------------------------------------------

# 9. Screen 01 --- Landing Page

Reference: **Panel 1**.

## Composition

Two-column hero:

``` text
LEFT
 ├── small supporting label
 ├── large headline
 ├── explanatory copy
 ├── feature bullets
 ├── primary CTA
 └── secondary link

RIGHT
 └── document visual / floating evidence cards
```

## Hero headline

Use:

> **Understand what you're signing.**

Secondary text:

> AI-powered legal document analysis that shows you what matters, where
> it appears, and what you should verify.

Primary CTA:

> **Analyze a Document →**

Secondary CTA:

> See how it works

## Supporting feature bullets

Use short, scannable statements:

-   Find key terms in seconds
-   See the exact source in your document
-   Identify risks and inconsistencies
-   Prepare questions for a legal professional

## Hero illustration

The reference uses a stylized legal document stack with floating insight
cards.

Keep the concept:

``` text
Document
   +
Notice period card
   +
Restriction / concern card
   +
Evidence indicator
```

The illustration should reinforce the product concept rather than look
like generic AI artwork.

------------------------------------------------------------------------

# 10. Landing Page Trust Footer

Near the bottom of the hero, show subtle trust messaging:

``` text
Secure & private
Evidence-backed answers
Not a substitute for professional legal advice
```

These should be visually secondary.

Do not make unsupported security claims.

------------------------------------------------------------------------

# 11. Screen 02 --- Upload Document

Reference: **Panel 2**.

The screen should feel extremely simple.

Structure:

``` text
Back

┌─────────────────────────────────────┐
│                                     │
│              Upload icon            │
│                                     │
│       Upload your legal document    │
│                                     │
│ Drop your file here, or click       │
│ to browse                           │
│                                     │
│         [ Choose File ]             │
│                                     │
└─────────────────────────────────────┘

Secure processing     Supported files     Privacy
```

Supported file types:

-   PDF
-   DOCX
-   TXT

Do not clutter this screen with options.

------------------------------------------------------------------------

# 12. Upload States

The upload component must have:

### Empty

``` text
Upload your legal document
```

### Dragging

Use a visible purple/indigo border and soft background.

### Uploading

Show progress.

### Processing

Show:

``` text
Processing your document...
```

### Success

Transition to Document Ready.

### Error

Show a concise human-readable error.

------------------------------------------------------------------------

# 13. Screen 03 --- Document Ready

Reference: **Panel 3**.

Top:

``` text
✓ Your document is ready!
```

Then two primary cards:

### Document Card

Contains:

-   PDF/file icon
-   Filename
-   Page count
-   File size
-   Detected document type
-   Replace file action

Example:

``` text
Employment Agreement.pdf
36 pages · 1.2 MB

Detected as: Employment Agreement

Replace file
```

### Intent Prompt

``` text
What would you like to understand?

Choose an option to get started.
```

Do not automatically show a large AI summary here.

------------------------------------------------------------------------

# 14. Screen 04 --- Intent Selection

Reference: **Panel 4**.

Heading:

> **What do you want to know?**

Supporting copy:

> Choose an option to get a focused, AI-powered analysis.

Use a 4×2 card grid on desktop.

Cards:

``` text
Compensation & Benefits
Notice & Exit Terms
Restrictions
Potential Concerns

Your Obligations
Important Terms
Ask About the Document
Prepare for a Lawyer
```

Below:

``` text
＋ Compare another document
```

------------------------------------------------------------------------

# 15. Intent Card Design

Each card contains:

``` text
[Icon]

Title

One or two lines explaining
what the operation does.
```

Example:

``` text
🔒
Restrictions

Find bonds, non-compete,
confidentiality and other
restrictions.
```

Cards should have:

-   White surface
-   Thin border
-   Rounded corners
-   Small icon container
-   Clear title
-   Small supporting text

Hover:

-   Slight border emphasis
-   Very subtle elevation
-   Slight icon movement optional

Selected:

-   Purple border
-   Light purple background
-   Clear selected indicator

------------------------------------------------------------------------

# 16. Document-Agnostic Intent Design

Do not make the intent cards employment-specific.

The same cards must work with:

``` text
Rental Agreement
NDA
Freelance Contract
Vendor Agreement
Internship Agreement
SaaS Terms
Startup Agreement
Partnership Agreement
Service Agreement
Employment Agreement
```

The analysis output should adapt.

Example:

### Rental

`Compensation & Benefits` may become:

> Rent, deposit, fees and payment obligations.

### Freelance

> Rates, invoices, payment schedule and expenses.

### SaaS

> Subscription fees, renewal charges and payment conditions.

The visual card remains consistent.

------------------------------------------------------------------------

# 17. Screen 05 --- Analysis View

Reference: **Panel 5**.

This is the main structured analysis interface.

Desktop layout:

``` text
┌────────────────┬──────────────────────────────────────┐
│ Operation nav  │ Analysis content                    │
│                │                                      │
│ Notice Period  │ Notice Period                        │
│ Termination    │ 60 days                              │
│ Resignation    │ [Explicitly stated]                  │
│ Severance      │                                      │
│ Post-employment│ Explanation                          │
│                │                                      │
│                │ Source                               │
│                │ Page 14 · §8.2                       │
│                │ [Evidence preview]                  │
│                │ [View in document →]                │
└────────────────┴──────────────────────────────────────┘
```

The left operation navigation should remain quiet and compact.

The right side contains the main result.

------------------------------------------------------------------------

# 18. Analysis Result Card

Example:

``` text
Notice Period

✓ 60 days

[Explicitly stated]

Your agreement states that either party must
provide 60 days written notice...
```

The status badge should be semantic, not decorative.

For explicit evidence:

``` text
✓ Explicitly stated
```

For partial:

``` text
i Partially determined
```

For missing:

``` text
○ Not found
```

For conflict:

``` text
⚠ Potential inconsistency
```

------------------------------------------------------------------------

# 19. Evidence Card

This is a key design component.

``` text
Source

Page 14 · §8.2 Termination

"...sixty (60) days written notice
before termination..."

View in document →
```

The evidence card should be visually distinct but not overwhelming.

Use:

-   Slight blue/purple tint
-   Thin border
-   Quote text
-   Metadata
-   Action link

------------------------------------------------------------------------

# 20. Evidence Chip

Evidence chips are reusable throughout the application.

Examples:

``` text
[Page 14 · §8.2]
[Page 8 · §4.1]
```

Or:

``` text
📄 Page 14 · §8.2
```

Behavior:

### On click

1.  Open document viewer.
2.  Navigate to the page.
3.  Find the evidence text.
4.  Highlight it in yellow.
5.  Scroll it into view.
6.  Keep the corresponding analysis context visible where possible.

This interaction is mandatory.

------------------------------------------------------------------------

# 21. Yellow Evidence Highlight

The selected reference explicitly uses yellow.

Use:

``` css
background: #fff1a8;
```

or a tuned equivalent.

Rules:

-   Highlight only supporting text.
-   Do not highlight an entire page.
-   Keep text readable.
-   Highlight all relevant matching fragments if there are multiple.
-   Provide a non-color indicator for accessibility.

Example:

``` text
8.2 Termination

Either party may terminate this Agreement by providing
[ SIXTY (60) DAYS WRITTEN NOTICE ]
to the other party.
```

The highlighted region should feel like a document annotation, not a UI
selection.

------------------------------------------------------------------------

# 22. Screen 06 --- Document Viewer

Reference: **Panel 6**.

Structure:

``` text
Top toolbar
 ├── filename
 ├── page controls
 ├── zoom
 ├── search
 └── actions

Left analysis panel
 ├── selected evidence
 ├── page/section
 └── related questions

Right document
 └── PDF page with yellow highlight
```

Desktop should use a split view.

The document itself must remain the visual focus.

------------------------------------------------------------------------

# 23. Related Questions in Viewer

Below the evidence card:

``` text
Related questions

[What happens if I resign?]
[Are there penalties for early exit?]
[Is there a probation period?]
[Are there post-employment restrictions?]
```

These are clickable.

Clicking one should open the document-grounded question flow.

------------------------------------------------------------------------

# 24. Screen 07 --- Potential Inconsistencies

Reference: **Panel 7**.

Header:

> **Potential Inconsistencies**

Supporting copy:

> We found clauses that may contain conflicting information. Please
> review and consider clarification.

Use a warning card.

Example:

``` text
Different notice periods mentioned

Location      Clause                 Notice period

Page 4        §4.1                   30 days
Page 14       §8.2                   60 days
```

Actions:

``` text
[View §4.1]
[View §8.2]
[Add to lawyer questions]
```

Do not visually imply that the later clause is automatically correct.

------------------------------------------------------------------------

# 25. Screen 08 --- Ask a Question / Not Determined

Reference: **Panel 8**.

The chat interface appears here, but it remains document-grounded.

User question appears as a compact message bubble.

System result:

``` text
Cannot be determined from this document

I couldn't identify a clause in the supplied document
that explains what happens to your stock options after
resignation.
```

Then:

### What I found

``` text
No relevant stock-option or equity clause
was identified in this document.
```

Then:

### You may want to ask your legal professional

``` text
• What happens to vested options after resignation?
• What happens to unvested options?
• Is there an exercise period after leaving?
• Is there a separate equity agreement?
```

------------------------------------------------------------------------

# 26. Suggested Question Chips

At the bottom of an answer:

``` text
[Is there a separate equity agreement?]
[What happens to vested options?]
[Are there post-employment restrictions?]
```

These should look like lightweight interactive chips.

They should not overpower the main answer.

------------------------------------------------------------------------

# 27. Screen 09 --- Prepare for a Lawyer

Reference: **Panel 9**.

Title:

> **Questions to Clarify with a Legal Professional**

Supporting copy:

> Based on your document, here are some important questions you may want
> to discuss.

Use numbered rows.

Example:

``` text
01  Does the bond apply if I resign during probation?

02  Which notice period applies if two clauses specify
    different durations?

03  What happens to benefits after termination?

04  Are there any non-compete restrictions after leaving?
```

Bottom actions:

``` text
+ Add your own question
[Copy all questions]
[Export to PDF]
```

This screen should feel actionable rather than conversational.

------------------------------------------------------------------------

# 28. Compare Documents

Although not shown as a separate numbered panel in the approved 3×3
reference, the comparison experience must use the same design system.

Structure:

``` text
Compare Documents

Original.pdf                  Updated.pdf

Notice Period
30 days                       60 days
                              ↑ Changed

Probation
6 months                      3 months
                              ↑ Changed

Remote Work
Not mentioned                 Permitted
                              New
```

Each difference must have evidence links.

------------------------------------------------------------------------

# 29. Operation-Specific UI Rule

Never render every operation using one generic result component.

Required visual patterns:

``` text
Key Terms
→ Data cards / grid

Compensation
→ Financial / payment cards

Notice & Exit
→ Structured clause analysis

Restrictions
→ Attention / restriction cards

Potential Concerns
→ Review dashboard

Obligations
→ Checklist

Important Terms
→ Key-value extraction grid

Ask Document
→ Grounded conversation

Prepare for Lawyer
→ Numbered question list

Compare
→ Comparison table
```

Shared components are encouraged.

Shared **presentation** is not.

------------------------------------------------------------------------

# 30. Responsive Design

Desktop is the primary reference.

At desktop widths:

-   3-column visual sheet corresponds to the design reference only;
    actual application screens should use full-width app layouts.
-   Analysis uses split layout.
-   Document viewer uses document + analysis panel.
-   Intent cards use multi-column grid.

Tablet:

-   Reduce grid columns.
-   Preserve hierarchy.
-   Keep evidence accessible.

Mobile:

``` text
Navigation
↓
Main content
↓
Analysis
↓
Evidence
↓
Document viewer
```

The document viewer should become a dedicated full-width section or
modal/sheet.

Intent cards become a single-column or two-column grid depending on
width.

------------------------------------------------------------------------

# 31. Mobile Evidence Interaction

On mobile, clicking an evidence chip should:

1.  Open the document viewer.
2.  Navigate to the page.
3.  Highlight the evidence.
4.  Show a small source toolbar:
    -   Page
    -   Section
    -   Back to analysis

Do not force a desktop split-view into a narrow mobile viewport.

------------------------------------------------------------------------

# 32. Interaction Design

The product should feel responsive but restrained.

Use animations for:

-   Page transitions
-   Upload processing
-   Card selection
-   Evidence navigation
-   Highlight appearance
-   Success states
-   Loading states

Animation timing:

``` text
Fast interaction: 120–180ms
Standard transition: 180–260ms
Panel transition: 250–350ms
```

Avoid:

-   Bouncy cards
-   Constant floating animations
-   Excessive parallax
-   Large entrance animations
-   Animated legal text

The UI should feel trustworthy.

------------------------------------------------------------------------

# 33. Loading States

Never show an empty screen while AI is working.

Example:

``` text
Analyzing your document

✓ Reading document
✓ Identifying relevant clauses
● Verifying evidence
○ Preparing your analysis
```

For longer processing:

``` text
This may take a moment.
Your document is being processed securely.
```

Use skeleton loaders where useful.

------------------------------------------------------------------------

# 34. Error States

Error UI should preserve the same visual language.

Example:

``` text
We couldn't analyze this document.

The document was uploaded successfully,
but we couldn't reliably extract its contents.

[Try again]
[Upload another document]
```

Avoid technical errors such as:

``` text
500 INTERNAL SERVER ERROR
```

in the user-facing interface.

------------------------------------------------------------------------

# 35. Accessibility

All visual decisions must have non-visual equivalents.

For example:

Instead of:

``` text
green badge
```

use:

``` text
✓ Explicitly stated
```

Instead of:

``` text
yellow highlight only
```

also provide:

``` text
Source: Page 14 · §8.2
```

Keyboard:

-   Tab through intent cards
-   Enter/Space to activate
-   Escape closes overlays
-   Arrow keys where appropriate for document navigation

Focus should always be visible.

------------------------------------------------------------------------

# 36. Microcopy Rules

Use plain, human language.

Prefer:

> What do you want to know?

over:

> Select an analytical operation.

Prefer:

> We couldn't find this in your document.

over:

> Retrieval returned zero relevant chunks.

Prefer:

> View in document

over:

> Navigate to source location.

Prefer:

> Prepare questions for a legal professional

over:

> Generate legal consultation prompt.

------------------------------------------------------------------------

# 37. AI Trust Language

Use consistent status vocabulary.

### Supported

> Explicitly stated

### Partial

> Partially determined

### Missing

> Cannot be determined from this document

### Conflict

> Potential inconsistency

Never use:

> 99.8% confidence

as the primary trust indicator.

The product's trust comes from **evidence**, not a model confidence
number.

------------------------------------------------------------------------

# 38. Privacy UI

The upload page may show privacy messaging such as:

``` text
Your files are securely processed.
```

Only display stronger claims such as:

> Automatically deleted after analysis

if the backend actually enforces the corresponding lifecycle policy.

The design must not overpromise security.

------------------------------------------------------------------------

# 39. Empty States

## No document

``` text
No document selected

Upload a legal document to get started.

[Upload document]
```

## No evidence

``` text
No supporting evidence found

This information could not be verified
from the supplied document.
```

## No inconsistencies

``` text
No potential inconsistencies identified

We did not identify conflicting clauses
for this analysis.
```

Avoid saying:

> The document has no legal risks.

The analysis is not exhaustive legal advice.

------------------------------------------------------------------------

# 40. Component Design System

Create reusable primitives.

``` text
Button
Card
Badge
Chip
IconButton
Input
Textarea
UploadZone
IntentCard
EvidenceChip
EvidenceCard
StatusBadge
SectionHeader
QuestionChip
DocumentMeta
DocumentViewer
ChecklistItem
ComparisonRow
AlertCard
Modal
Tooltip
```

All should use centralized design tokens.

------------------------------------------------------------------------

# 41. Component Variants

Example:

``` text
Button:
- primary
- secondary
- ghost
- danger

Badge:
- success
- info
- warning
- danger
- neutral

Card:
- default
- interactive
- selected
- warning
- evidence
```

Do not create one-off CSS for every screen if a reusable variant can
express the design.

------------------------------------------------------------------------

# 42. Design Consistency Rules

The same visual concept should always look the same.

For example:

### Evidence

Always:

``` text
Page X · §Y
```

### Suggested question

Always:

``` text
[Question?]
```

### Primary action

Always use the primary purple/indigo button.

### Warning

Always use the same warning icon and semantic treatment.

### Document metadata

Always use the same typography hierarchy.

------------------------------------------------------------------------

# 43. Do Not Over-Design

The reference image is intentionally restrained.

The agent must not add:

-   AI sparkles everywhere
-   Floating chat buttons
-   Excessive gradients
-   3D illustrations
-   Huge icons
-   Animated backgrounds
-   Decorative charts unrelated to the document
-   Complex sidebars that aren't in the reference

Every visual element should answer:

> Does this help the user understand or verify the document?

If not, remove it.

------------------------------------------------------------------------

# 44. Landing-to-App Transition

The landing CTA should feel like a clear entry point:

``` text
Analyze a Document →
```

Flow:

``` text
Landing
 ↓
Upload
 ↓
Document Ready
 ↓
Intent Selection
```

Avoid intermediate marketing screens.

The user should reach the core product quickly.

------------------------------------------------------------------------

# 45. Prototype Navigation

Minimum navigation:

``` text
Landing
  ↓
Upload
  ↓
Document Ready
  ↓
Analysis
  ↘
   Document Viewer
  ↘
   Ask Question
  ↘
   Lawyer Questions
  ↘
   Compare
```

A persistent "Back to analysis" action should exist where appropriate.

------------------------------------------------------------------------

# 46. Frontend Fidelity Checklist

Before considering the frontend complete, compare implementation against
`UI_screens/screens.jpeg`.

Check:

-   [ ] Landing layout matches
-   [ ] Hero hierarchy matches
-   [ ] CTA placement matches
-   [ ] Upload box proportions match
-   [ ] Document Ready card layout matches
-   [ ] Intent card grid matches
-   [ ] Analysis split layout matches
-   [ ] Evidence card matches
-   [ ] Yellow evidence highlight exists
-   [ ] Viewer layout matches
-   [ ] Inconsistency table matches
-   [ ] Not-determined screen matches
-   [ ] Lawyer question list matches
-   [ ] Spacing feels similar
-   [ ] Typography hierarchy feels similar
-   [ ] Border/radius language matches
-   [ ] Color system matches
-   [ ] Navigation is similarly restrained

Do not judge only by whether components exist. Judge by **visual
hierarchy and composition**.

------------------------------------------------------------------------

# 47. Frontend QA at Each Milestone

After each major screen is implemented:

1.  Run the application.
2.  Capture the screen.
3.  Compare against `UI_screens/screens.jpeg`.
4.  Fix spacing and hierarchy.
5.  Check desktop.
6.  Check mobile.
7.  Check keyboard navigation.

Do not wait until the end to compare the UI.

------------------------------------------------------------------------

# 48. Design-to-Code Priority

When implementing the visual design, prioritize in this order:

``` text
1. Layout
2. Typography hierarchy
3. Spacing
4. Card composition
5. Colors
6. Interaction states
7. Icons
8. Animation
```

Do not spend time perfecting icons while the layout is still wrong.

------------------------------------------------------------------------

# 49. Important Reference-Image Interpretation

The approved screenshot is a **visual design reference**, not literal
production copy.

Some text in generated/reference imagery may contain placeholder or
rendering artifacts.

The implementation agent must:

-   Preserve the intended wording from `IMPLEMENTATION_PLAN.md`
-   Preserve the visual hierarchy from the screenshot
-   Correct obvious image-generation text artifacts
-   Never copy misspelled or corrupted text from the image

For example, use:

> **Explicitly stated**

rather than reproducing any malformed rendering of that phrase from the
screenshot.

------------------------------------------------------------------------

# 50. Design QA Definition of Done

The frontend is design-complete when:

### Landing

-   [ ] Matches approved hero composition.
-   [ ] CTA is prominent.
-   [ ] Trust message is visible but secondary.

### Upload

-   [ ] Upload area is centered and spacious.
-   [ ] Drag/drop state exists.
-   [ ] Processing state exists.
-   [ ] Error state exists.

### Document Ready

-   [ ] File metadata is clear.
-   [ ] Document type is visible.
-   [ ] Intent entry point is obvious.

### Intent Selection

-   [ ] Cards are visually distinct.
-   [ ] Cards are easy to scan.
-   [ ] All eight operations exist.
-   [ ] Compare action is separated from the main grid.

### Analysis

-   [ ] Operation navigation exists.
-   [ ] Result is structured.
-   [ ] Evidence is visually distinct.
-   [ ] Status is semantic.

### Evidence

-   [ ] Source chip is clickable.
-   [ ] Viewer navigates to the source.
-   [ ] Supporting text is highlighted yellow.
-   [ ] Source metadata remains visible.

### Inconsistency

-   [ ] Conflicting clauses are side-by-side.
-   [ ] Evidence is accessible.
-   [ ] UI does not claim which clause is legally correct.

### Not Determined

-   [ ] Missing evidence is clearly communicated.
-   [ ] No hallucinated answer is shown.
-   [ ] Relevant professional questions are suggested.

### Lawyer Preparation

-   [ ] Questions are numbered.
-   [ ] Questions are editable/addable.
-   [ ] Copy/export actions exist.

### Responsive

-   [ ] Desktop matches reference.
-   [ ] Tablet remains usable.
-   [ ] Mobile does not collapse into an unusable desktop layout.

### Accessibility

-   [ ] Keyboard navigation works.
-   [ ] Focus states are visible.
-   [ ] Status does not rely on color alone.
-   [ ] Interactive controls have accessible names.

------------------------------------------------------------------------

# 51. Final Design Principle

LexLens should visually communicate one idea above everything else:

> **The AI is helping you navigate the document --- it is not asking you
> to blindly trust the AI.**

The visual hierarchy should therefore repeatedly reinforce:

``` text
WHAT THE DOCUMENT SAYS
        ↓
WHAT LEXLENS UNDERSTANDS
        ↓
WHERE IT SAYS IT
        ↓
WHAT IS UNCLEAR / MISSING
        ↓
WHAT YOU CAN ASK NEXT
```

That is the design identity of LexLens.

------------------------------------------------------------------------

# 52. Final Agent Instruction

Before implementing or changing any UI:

``` text
READ:
1. IMPLEMENTATION_PLAN.md
2. design_plan.md
3. UI_screens/screens.jpeg
```

Then verify:

``` text
Does this change preserve the product?
Does this change preserve the approved visual language?
Does this change preserve evidence-first interaction?
Does this change preserve accessibility?
Does this change preserve the document-grounded boundary?
```

If the answer to any of these is no, revise the implementation before
proceeding.

**Do not invent a new UI direction. Build the approved LexLens direction
faithfully, then improve implementation quality without changing the
product's core interaction model.**
