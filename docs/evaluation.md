# Verification and evaluation

## Release checks

The application release at [`cd615c2`](https://github.com/MS3B09/Games-Recommendation-System/commit/cd615c2fa49cfe811ee20ecf04aa1bb85867cc26) passed [backend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42409600236): 302 tests, one skipped, plus lint, type, and API-contract checks. [Frontend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42409600180) passed 81 tests and the production build. Hosted no-mock checks covered discovery, saved games, dashboard interactions, and responsive Chromium layouts.

The catalog-name fix was checked against all 2,000 then-active titles and 4,602 name variants, with no misses in that finite set. Scripted-provider checks verified handling of a false catalog denial. These are recognition and validation checks, **not** 2,000 generated answers or proof that an LLM cannot make mistakes. The final release verification did not make live AI calls.

## Experimental relevance findings

An earlier retrieval-only comparison used a 40-game catalog, oracle-provided intent, and a semantic-only baseline. On named-target held-out cases, Hit@5 was 9/9 for the proposed method and 8/9 for the baseline; both found 4/5 nonexhaustive semantic anchor seeds. This small conditional comparison is **not** evidence of end-to-end recommendation-quality improvement.

The live development pilot also exposed rejected or unsupported responses. A November 5 hosted assistant smoke returned an answer-validation error; it was not retried or relabeled a pass. The owner later reported the live app working, but full human relevance judgments, comprehensive generated-answer evaluation, and representative performance acceptance remain incomplete.

The [historical evaluation report](https://github.com/MS3B09/Games-Recommendation-System/blob/cd615c2fa49cfe811ee20ecf04aa1bb85867cc26/docs/reports/conversational-rag-evaluation.md) preserves the original measurements and failures. Frozen evaluation inputs remain in [`data/evaluation/`](../data/evaluation/); historical live journals must not be replayed against changed source or treated as new results.
