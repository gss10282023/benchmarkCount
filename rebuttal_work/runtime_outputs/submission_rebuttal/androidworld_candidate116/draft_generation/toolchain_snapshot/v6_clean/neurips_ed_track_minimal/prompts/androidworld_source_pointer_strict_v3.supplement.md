## AndroidWorld exact Source Inventory support-pointer gate

Every support entry must use `<relative_path>::<location>`. The path before `::`
must be copied exactly from the supplied canonical packet's `## Source Inventory`.

`case_packet.md` is not a source path and is forbidden. Also forbidden are absolute
paths, URLs, leading `./`, `..` traversal, drafter workspace files, checklists,
reviews, scores, audit records, and invented aliases. Every required native clause
must have a non-empty support list; rationale text never substitutes for support.

