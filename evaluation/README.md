# Evaluation preparation

`cases-skeleton.json` contains ten initial development scenarios covering seeds, text, combined discovery, hard constraints, missing facts, feedback, conflict and refinement. Only Hades and Portal 2 seed IDs are used here; both were verified during source probes.

This is a design skeleton, not the final API request schema, a runnable evaluation, or human judgments. Expand to 30–50 curated cases and separate development from release cases before tuning. Freeze catalog/model/ranking versions, implement one reproducible TF-IDF cosine baseline with the same hard filters, and have the owner judge the hidden-system union of top-five outputs on the 0/1/2 scale. Report violations, unsupported claims and measured latency separately. No quality improvement has been measured.
