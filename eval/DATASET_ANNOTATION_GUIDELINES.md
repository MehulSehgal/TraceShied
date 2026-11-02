# Dataset Annotation Guidelines

## Status of the pilot

`dataset.pilot.jsonl` contains 20 synthetic conversations. Its binary labels and
rationales are provisional, were authored alongside the examples, and have not
been independently reviewed. The examples are not real-world observations and
must not be described as independently annotated, validated, or representative.

All pilot rows belong to the `dev` split. The pilot has no held-out test
examples. It may be used to exercise dataset validation and development-time
evaluation tooling, but its scores are not evidence of detection accuracy and
must not be used to claim real-world performance.

## Provisional label interpretation

The evaluator supports two conversation-level labels:

- `harassment_pattern`: provisional label for a conversation whose sequence
  suggests targeted, unwanted, persistent, intimidating, or escalating
  behavior.
- `benign`: provisional label for a conversation that, in context, does not
  show a harassment pattern, even if it includes disagreement, teasing, or
  isolated negative language.

These are only the pilot authors' rationales, not decisions reached by
independent reviewers. A single negative word should not determine a
conversation-level label by itself. Quoted and joking language should be
interpreted in context.

## Rationale metadata

Each pilot row has an `annotation_rationale` describing why its provisional
label was assigned. These rationales document the synthetic author's intent;
they are not independent annotations or adjudication records. `origin` is
`synthetic`, and `annotation_status` is
`provisional_not_independently_reviewed` on every pilot row.

## Limitations

- The examples are synthetic and do not establish real-world prevalence,
  representativeness, or detection performance.
- The set is small and deliberately balanced, so it does not reflect natural
  class or language distributions.
- The examples have not been independently reviewed; labels may be debatable
  or inconsistent.
- The pilot has no test split and must not be treated as held-out evaluation
  data.
- The current evaluator ignores annotation metadata and reports aggregate
  metrics only.

## Future independent review process

Before creating a reviewed evaluation dataset:

1. Reviewers should use a finalized guideline and independently label each
   complete conversation without seeing the system's prediction or each
   other's label.
2. Record each reviewer's decision and brief rationale in review records kept
   separate from the evaluator's binary label.
3. Send disagreements and uncertain cases to an independent adjudicator.
   Exclude cases that remain genuinely unclear rather than forcing a binary
   label.
4. Include only resolved, reviewed labels in a future evaluation dataset, and
   document the actual review process and counts. Do not mark the current
   pilot as reviewed retroactively.
5. Group duplicate or closely related scenarios before assigning development
   and held-out test splits. Keep the test split untouched during development.

Do not add a third label to the current evaluator without explicitly extending
and testing its binary-label behavior. Unresolved cases should remain outside
the final binary evaluation dataset.
