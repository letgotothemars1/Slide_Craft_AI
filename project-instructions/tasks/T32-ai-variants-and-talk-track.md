# T32 — Three AI variants and slide/notes agreement

Status: complete for the scoped T32 extension; independent finish disposition: ship.

## Approved change

Content completeness and agreement with speaker notes outrank starter layouts. Exactly three alternatives belong to each accepted slide: selected/recommended, alternative and out-of-the-box. The main slide is one of these three, not an additional fourth option. Read the speech while seeing the artifact.

## Shipped contract

- One structured model call produces three distinct native plans from accepted content and notes. Template mode explicitly provides prepared alternatives.
- Persist `composition_variants`, `selected_variant_id`, status/origin/fingerprint and worker token. GET `/draft/slides/{id}/compositions` is read-only; POST `/compositions/generate` starts guarded background work. PATCH `/composition-choice` selects `variant_id` with expected project revision.
- The response scene/preview plan derives from the selected variant. Content changes invalidate cached alternatives; stale completions are discarded. Restart recovery is retryable without dropping accepted text.
- Final refinement synchronizes the selected persisted plan, retaining exactly three alternatives.
- A dedicated whole-deck content/notes check precedes design. Concrete blocking findings stop styling; accepted content is not rewritten. Cached approval is valid only for the same content. Key-free mode makes no AI consistency claim.
- Notes are a readable inspector tab with a separate editing action. Desktop slide and inspector scroll independently; narrow-screen order puts notes between the slide and variants. Existing unsaved-edit protection remains.
- Native composition remains bounded to four starters plus arrangement, emphasis, focal section and relative poster-title/feature-support widths. No arbitrary canvas or unsupported data generation.

## Source evidence

`app/services/composition_choices.py`, `app/project_schemas.py`, `app/repository.py`, `app/routers/projects.py`, `app/services/coherence_service.py`, `app/services/ai_design.py`, `app/services/modular_recovery.py`; `src/components/CompositionChooser.tsx`, `SpeakerNotesEditor.tsx`, `LiveDraftEditor.tsx`, `src/index.css`.

The targeted backend tests cover exact count/unique geometry, one model call, content preservation, selection-to-canvas parity, read/cache behavior, stale results, provider failure and restart recovery. Final live/browser evidence belongs in `.impeccable/review/T32/`; do not infer provider or browser verification from mocks alone.


## Earlier integration observations (superseded by final evidence below)

The initial real-provider final-quality run rejected two slides. After grounded renderer corrections, all five slides reached ready at 42 logical requests, with returned usage of 131,233 input and 128,362 output tokens. These figures describe the inspected run, not billing or a universal quality threshold.

Subsequent inspection found a real semantic defect: older speaker notes described an existing bar visual although the slide had no accepted visual. The agreement cache is now audit-versioned, and a narrow deterministic guard rejects unambiguous, nonnegated present references to a nonexistent chart/bar visual; broader semantic agreement remains a model judgment. The third slide's notes subsequently received an explicit UI correction. Therefore five visually ready slides are not yet evidence that all speaker notes are semantically verified.

Renderer corrections recognize verbatim percentage transitions when a separate caveat section is retained, and paired duration phrases within accepted semantic content. Exact numbers/words, sample/page captions and original section bindings remain; no new statistics are derived. The final semantic/model recheck below supersedes this earlier checkpoint.


## Scroll correction and current verification

The central desktop canvas now stays stationary above a separately scrolling `.draft-slide-controls` region; retry/update buttons cannot hide underneath an overlapping sticky slide. Rail and inspector retain independent scrolling. Through 900px the controls wrapper uses display-contents and the existing slide → notes → variants order remains.

Earlier checks passed 107 backend and 43 frontend tests plus build/TypeScript; the 50-call in-progress checkpoint is superseded by the final evidence below.


## Final actual-provider and native evidence

`.impeccable/review/T32/model-final.json` records phase ready, workflow complete, five ready designs and approved current semantic-agreement and whole-deck reviews. The development run reached 59 logical requests with returned usage of 205,155 input / 191,395 output tokens, including reasoning where supplied. It includes failures, manual corrections and retries; it is not a typical cost or latency benchmark.

Exact accepted title/body/source blocks, sections and visual data remain unchanged from the original reviewed draft. One inaccurate speaker-note phrase was explicitly corrected through the editor rather than silently rewritten by styling. All five final notes were asserted against the native PowerPoint export. Evidence: `model-final.pptx`, `native/slide-1.png` through `slide-5.png`, `desktop.png`, `mobile.png`, `desktop-notes.png` and `mobile-notes.png` under the same review directory. The parent inspected all five native renders without clipping; independent finish review returned ship with no material fixes (`finish-review.md`).

A rendered-deck review caught a linear process that wrongly implied Scan → Auto-route → Staff-review despite complementary confidence conditions. Shared native rendering now forks only the narrow accepted three-label pattern whose second label explicitly says “if confident” and third “if uncertain”; all labels/content remain exact. This is not arbitrary flowchart generation. Typed starter/proportion tools remain bounded, and selected variants may adapt arrangement during refinement. The selected final card uses a neutral final-design label and current rationale instead of preserving an obsolete geometry label; its preview still matches the main slide.

Final local checks reported by the parent: 108 backend tests, 44 frontend tests, application TypeScript and production build pass. A model-approved semantic gate provides inspected agreement evidence, not factual certification or a guarantee that all future notes are correct.


T32 final verification limits: the browser Download PowerPoint button was enabled/reachable and clicked without a UI error, but its download event did not arrive within the tool timeout; browser download-manager completion remains unverified. The API-generated PPTX, exact native content/notes and all five inspected native renders are verified. A one-unit vertical spacing correction to the native confidence fork followed model review; mechanical tests and native export inspection cover that correction, not a claim that the model reviewed those exact final pixels. Independent finish disposition is ship for this scoped extension, not universal presentation quality or factual certification.
