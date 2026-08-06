# grokkable-output — independent qualitative review

Reviewer: independent Opus subagent (did not author the skill, did not run the evals).
Scope: 9 outputs — iteration-1 with_skill and without_skill (v0.1.0), iteration-2 with_skill (v0.2.0).
Method: each reply read once, cold, in the role of the reader named in the eval prompt, then re-read against the fixture notes for fidelity.

Measurements referenced throughout:

| Output | Words | MD headers | Bold markers | Arrows | Sentences >25w | Longest sentence |
|---|---|---|---|---|---|---|
| eval-0 v0.1 with_skill | 307 | 0 | 0 | 0 | 4 | 44 |
| eval-0 baseline | 371 | 0 | 24 | 1 | — | — |
| eval-0 v0.2 with_skill | 315 | 0 | 0 | 0 | 4 | 31 |
| eval-1 v0.1 with_skill | 279 | 0 | 0 | 0 | 1 | 26 |
| eval-1 baseline | 273 | 0 | 6 | 1 | — | — |
| eval-1 v0.2 with_skill | 328 | 0 | 0 | 0 | 4 | 40 |
| eval-2 v0.1 with_skill | 396 | 0 | 6 | 0 | 6 | 41 |
| eval-2 baseline | 464 | 0 | 22 | 0 | — | — |
| eval-2 v0.2 with_skill | 428 | 0 | 0 | 0 | 4 | 41 |

("Headers" counts `^#`; every baseline instead used bold-line pseudo-headers, which is why the bold column matters more.)

---

## (a) Per-output feedback

### iteration-1 / eval-0 debug report / without_skill

As the senior engineer who just walked back to my desk, I get the answer in the first bolded line and that part works. Then the reply turns into a document: four bold section headings on a chat message, and a causality line that is a literal puzzle — `sandbox host → Avalara 429s → each 429 retried 3x with 2s backoff (up to +6s latency) → tax-svc p99 goes 210ms → 8.4s → blows past payment-orchestrator's 5s downstream timeout ... → TaxLookupTimeout → checkout-svc catches it as a generic Exception`. That is seven arrows with a nested arrow inside one of them, and I read it twice. Against that, this is the only output in the whole set that tells me "I didn't audit other services for the same class of bug" — a scope limitation neither with-skill version kept, and one I would actually want. The three-option comparison block is also more decision-ready than the with-skill treatment, which mentions only the option it rejected.

### iteration-1 / eval-0 debug report / with_skill (v0.1)

Fast and honest. First sentence gives fix plus cause, second gives the recovery evidence, and the causal paragraph reads in one pass with verbs where the baseline had arrows. The "Two things I didn't expect, both worth your attention" paragraph is the strongest move in any of the nine outputs — it puts the untyped-500 swallowing and the deploy-checklist gap where a surprised reader will see them, which is exactly what the fixture's line 18 and line 8 deserve. Cost: a 44-word opening sentence in paragraph three, and the ruled-out timeout option is parked in a parenthetical at the very end, after the decision question, which is the one place my eye skips.

### iteration-1 / eval-1 migration status / without_skill

At 273 words with three bold pseudo-headers, this reads like a status doc rather than an answer to "quick status?", but the content is well-ordered and I would not be confused. The single arrow (`multer` → `@fastify/multipart`) is a naming convention, not a causality puzzle, and I would not have flagged it if the assertion did not. Best thing here that both with-skill versions lost: the closing line "Tomorrow: session-touch decision (yours), then the multer routes. The renewal-on-read answer is the thing actually holding me up" — it names the blocker as the blocker. Also "worth knowing if any of those endpoints take large uploads" hands me a question I can answer without opening anything.

### iteration-1 / eval-1 migration status / with_skill (v0.1)

The tightest output in the set. One sentence gives 48/61 and 312 tests, the second sentence tells me one of the two remaining groups needs my call, and the session question arrives with its consequence attached ("a user who only reads stays logged in indefinitely"). Both pre-existing bugs are stated with their real paths and honest confidence ("I suspect it's benign, but I haven't proven there's no bypass when the parse throws first"), and the synthetic benchmark is explicitly discounted. Only friction: 279 words is over the eval's own ~250 proportionality line, which the author's analyst notes already conceded was marginal.

### iteration-1 / eval-2 nonexpert audit / without_skill

As a non-engineer founder this is competently translated but exhausting: six section headings, a "Proposed plan" bullet block that restates the three fixes I just read, and 464 words for a question I asked in nine. The headings are doing the reader's summarizing for them in a way that adds a second pass rather than removing one. Two things here are genuinely better than either with-skill version, though: "Total is roughly a day of engineering time" is the single number a founder actually plans against and no with-skill reply provides it, and "Four of the five 'high severity' items are in development tooling" gives me the severity vocabulary I will encounter if I ever look at the raw scan.

### iteration-1 / eval-2 nonexpert audit / with_skill (v0.1)

Strong on translation — "the code that decides who is logged in" and "can be tricked into fetching a different address than the one it appears to be given, including addresses inside our own network" both land without a single piece of jargon. Bold item lead-ins ("**Session tokens, today.**") give me a scannable spine without turning the reply into a document. Two touches I would keep: "The scan calls this critical, but we only use it in a build script" pre-empts the confusion I would hit if I saw the raw report, and "That's reassuring, not proof — logs only show what got recorded" is exactly the calibration a founder needs on a clean-log finding. One invented number: "we'll be back here in six months" is not in the notes.

### iteration-2 / eval-0 debug report / with_skill (v0.2)

Best of the debug set on structure. The opening is now "Fixed —" and the longest sentence dropped from 44 words to 31. Two additions earn their place: "I confirmed the cause in the logs rather than inferring it" is the confidence statement stated once and plainly, and "I took the rollback without checking in because the runbook pre-approves rollbacks for sev2" tells me why an agent acted unilaterally before I have to wonder. The rejected timeout option moved out of a trailing parenthetical into its own sentence in the body, which is where it belongs. What I lost relative to v0.1: the untyped-500 swallowing is now stated inside the causal chain instead of flagged as a surprise, so a scanning reader will not register it as something to fix. That is a fixture item (notes line 8) the skill's own "anything that surprised you always survives selection" rule argues for elevating.

### iteration-2 / eval-1 migration status / with_skill (v0.2)

Content-complete and readable, but it is the wrong size for "quick status?" — 328 words, up from 279 in v0.1 and 273 in the baseline, making it the longest answer to the shortest question in the set. The session-renewal question is now phrased more answerably ("is renewal-on-read acceptable for the 30-minute idle logout?") and that is a clear improvement. Against it, the explanation of that question is a 40-word sentence carrying three ideas — plugin behavior, Express behavior, and the user-visible consequence — which is precisely what v0.2.0's new one-idea-per-sentence rule exists to prevent. And the Stripe bug now carries an invented reason (see fabrication check). Nothing tells me what happens tomorrow, which the baseline did.

### iteration-2 / eval-2 nonexpert audit / with_skill (v0.2)

The opening is the best in the set — "Less bad than the headline number, but two items need real work this week and one of them touches login" tells a founder the verdict, the workload, and the scary part in one breath. All bold is gone and nothing is lost by it. But this is also the output with the most defects. The counts do not reconcile: I am told 23 total, 20 that don't matter, 3 that do, and then "The remaining sixteen are routine version bumps" — 23 minus 3 is 20, and I stopped to do that subtraction, which is the reread the skill exists to prevent. The v0.1 version said "The remaining 20" and was consistent. The 30-day log check lost its caveat (v0.1: "That's reassuring, not proof"; v0.2: "found nothing"), lodash lost the note that the scan calls it critical, and the Dependabot hour estimate is invented. The two-question close is good and I can answer both without opening anything.

---

## (b) iteration-1 vs iteration-2 with_skill — did v0.2.0 change anything visible?

Yes, and the change is directional in three places, neutral in one, and negative in two.

**Better.** Bold usage went to zero across all three v0.2 outputs (v0.1 still used six bold markers on eval-2 as item lead-ins). Whatever v0.2.0 added, it hardened the "prose over structure" instinct. The eval-0 opener got sharper ("Fixed —" versus "Found it and it's fixed:") and its longest sentence fell 44→31 words. Decision questions got more answerable: eval-1's session question is now a direct yes/no, and eval-2 closes with two scoped asks instead of one compound one.

**Neutral.** Header count was already zero in v0.1; arrows were already zero. Content assertions passed in both iterations. On the outcome the evals actually measure, v0.2.0 bought approximately nothing — 19/19 in iteration 1, 18/19 in iteration 2 under my grading, and the one delta is a regression.

**Worse, and this is the headline.** Every v0.2 output is longer than its v0.1 counterpart: 307→315, 279→328, 396→428. The average grew 8%. The one length-sensitive assertion in the suite (eval-1, "under ~250 words") passed marginally at 279 in v0.1 and fails at 328 in v0.2. If v0.2.0's added prose — the Simplified Technical English paragraph, the altitude-selection section, the one-idea-per-sentence rule — was meant to tighten output, the measurement says it did the opposite: it gave the model more things to say and more license to say them in full sentences. Second regression: the new ~25-word sentence rule did not take. eval-1 went from 1 over-length sentence (max 26 words) to 4 (max 40); eval-2 held at a 41-word maximum. A rule stated in v0.2.0 is violated four times per output in v0.2.0's own results.

**Fidelity moved slightly the wrong way too.** v0.1's eval-2 carried "That's reassuring, not proof" and "The scan calls this critical"; v0.2's dropped both and added an unsupported hour estimate. v0.1's eval-1 said "I suspect it's benign, but I haven't proven there's no bypass"; v0.2's supplied a mechanism it did not have. Both are the same failure — the model filling in with plausible detail — and the sections v0.2.0 added (altitude, selection) are the plausible cause, since both tell the writer to carry judgment rather than raw material.

Net: v0.2.0 is a style win and a proportionality loss. I would not ship it over v0.1.0 without addressing length.

---

## (c) Fabrication check

Every with-skill output was checked claim by claim against its fixture. Findings ordered by severity.

**Unsupported — invented technical justification (most serious).** iteration-2 / eval-1: "My best guess is that it's benign because the parse error path returns early, but I have not confirmed that." The fixture (migration-status-notes.md line 10) says only "validates signature AFTER parsing JSON body (validation bypass if parse throws first? probably benign but sketchy)" — it poses the early-return behavior as an open question and does not answer it. The reply supplies the answer as its reasoning and then hedges the conclusion, which is the wrong way round: the reader is given false grounds to relax about a signature-validation path. v0.1's version got this right ("I suspect it's benign, but I haven't proven there's no bypass when the parse throws first"). This is a v0.2.0 regression on the skill's own "separate what you know from what you infer" rule.

**Unsupported — invented effort estimate.** iteration-2 / eval-2: "Setting it up is about an hour" (Dependabot/Renovate). dependency-audit-notes.md line 15 states the gap and gives no estimate. The founder is being handed a planning number the agent made up. Note the baseline produced the same number independently ("I'd budget an hour to set it up"), so this is a model prior rather than skill-induced — but v0.1's with-skill reply did *not* include it, so v0.2.0 lost the guardrail.

**Unsupported — invented projection.** iteration-1 / eval-2: "Without it, we'll be back here in six months." No basis in the notes.

**Unsupported — added scope.** iteration-2 / eval-2: "It does change authentication code, so I'd want someone to sign in, sign up, and sign out afterward to confirm nothing broke." Good practice, not in the notes. Benign but it is the agent adding work to the plan on its own authority.

**Internally inconsistent arithmetic.** iteration-2 / eval-2: "23 problems ... Twenty of them are [noise] ... Three are worth acting on" followed by "The remaining sixteen are routine version bumps." 23 − 3 = 20. The 16 is real (11 moderate + 5 low from the notes) but the four dev-tooling highs are counted in the "twenty" and then dropped from the "remaining," so no reading of the reply makes the numbers add up. Not a fabricated fact; a fabricated-feeling one, which for a founder is the same problem. v0.1 said "The remaining 20" and was consistent.

**Justified inference, flagged for completeness.** Both eval-1 with-skill outputs assert that renew-on-read means an idle user with a background-polling tab never logs out. That consequence is not stated in the notes but follows deductively from renew-on-read plus a 30-minute idle timer, and the baseline derived it too. I would not call this a fabrication. Same class: iteration-2 / eval-2's gloss "and returning what it finds" for the axios SSRF (the notes say only that user-supplied URLs are fetched), and iteration-2 / eval-0's "That accounts for all 137 500s" (the notes establish the count, the window, the endpoint, and the mechanism separately; the synthesis is sound).

**Clean.** iteration-2 / eval-0 is the only with-skill output with no unsupported claim. Every number in it — 15:19, v2.13.2, 0.02%, 30 minutes, 13:47, 10 req/s, 45, three retries at 2s, 210ms, 8.4s, 5s, timeouts.yaml line 22, 137, 14:02–14:40, TAX-2211, TAX-2212, roughly an hour — traces to a line in debug-investigation-notes.md.

**Verdict:** no output invents a fact wholesale, but four of six with-skill outputs contain at least one number, mechanism, or projection with no support in the source notes, and the skill contains no instruction that would stop any of them. The evals contain no assertion that would catch any of them either.

---

## (d) Cross-cutting patterns

**1. The skill's measured value is entirely formatting discipline, and iteration 2 confirms it.** Every baseline failure across both iterations is structural (arrow chains, bold pseudo-headers, trailing recap). Every content assertion passes with or without the skill. The author's iteration-1 notes said this; iteration 2 gives no reason to revise it. On Opus, this skill is a chat-register formatting corrector, and the description should probably say so.

**2. Selection pressure is deleting real caveats.** The skill says "never silently summarize away a caveat, a failed check, or a limitation," yet with-skill outputs dropped: "I didn't audit other services for the same class of bug" (baseline eval-0, gone from both with-skill versions), "That's reassuring, not proof" (v0.1 eval-2, gone from v0.2), and the flagged-surprise framing of the untyped-500 swallowing (v0.1 eval-0, demoted in v0.2). Meanwhile the *additions* the model makes under the skill are the confident ones (an invented mechanism, an invented estimate). The selection guidance is asymmetric in practice: it cuts hedges and keeps assertions.

**3. Length grew in the direction of the reader's cost.** All three v0.2 outputs are longer than v0.1, and eval-2 at 428 words is answering a founder's nine-word question. The skill is explicit that it is not a brevity prompt, and that stance is right, but there is no counterweight instruction that binds when the *question* is small. "Quick status?" and "how bad is it?" are both requests for a proportionate answer, and the skill has one sentence about this ("a status update is a paragraph or two") that visibly does not fire.

**4. Baselines lose on scanability, not on substance.** Reading the without-skill outputs as the recipient, none of them left me misinformed; they left me doing extra passes. That is a real cost and the skill fixes it. But it means the honest framing of this skill's benefit is "removes a rereading tax," not "produces a better report" — and on two occasions the baseline carried information the skill's version dropped.

**5. Numbers are where one-pass reading actually breaks.** The single hardest stop in all nine outputs was the 23/20/3/16 arithmetic. The skill has extensive guidance on sentences, structure, and claims, and nothing at all on keeping quantities consistent with each other.

---

## (e) Recommendations, ranked

**1. Add a fidelity rule to `write` mode, not just `rewrite` mode.** The skill's strongest anti-fabrication language ("Never add facts, confidence, or stakes the original didn't contain") lives only in the `rewrite` mode description, where it never fires for a default-mode report. Promote it into "Calibrated claims" as its own bullet, phrased for reports: *every number, estimate, timeline, and mechanism in the report traces to something you observed; if you're supplying a reason the evidence doesn't give you, say "I don't know why" instead.* This is the single change that would have caught the invented Stripe rationale, the invented Dependabot hour, and the invented six-month projection. Highest value, lowest cost.

**2. Give proportionality a hard trigger.** Replace the soft "a status update is a paragraph or two" with a rule keyed on the question, not the work: *the reply's length is set by what the reader asked, not by what you did. A one-line question ("quick status?", "how bad is it?", "what did you find?") gets under 250 words unless a decision or a safety issue forces more — and if it does, say why in the first sentence.* v0.2.0 made all three outputs longer; without a binding rule, v0.3 will too.

**3. Add a numeric-consistency check to the grok test.** A fourth check: *do the numbers in your draft add up to each other? If you give a total and then partition it, the parts must reconcile.* One sentence, and it catches the worst reread in the corpus.

**4. Make surprises structurally visible, not merely present.** The skill says surprises always survive selection. v0.2's eval-0 kept the surprise as a clause inside a causal paragraph, where a scanning reader loses it. Tighten to: *a surprise gets its own sentence and its own position — not a subordinate clause inside an explanation of something else.*

**5. Enforce the ~25-word rule or drop it.** It is stated in v0.2.0 and violated four times per output in v0.2.0's own results, including a 40-word sentence carrying three ideas. Either move it into the anti-patterns table with a named failure mode and a fix (which is where the rules that actually fired live — arrows and headers are both in that table), or cut it, because an unenforced rule costs tokens on every load.

**6. Test the eval suite for fabrication.** No assertion in any of the three evals checks output against the fixture. "Effort estimates included so the founder can plan" is exactly the grader spec's example of a weak assertion: it passes on an invented estimate. Add per-eval assertions of the form *every number in the reply appears in or follows arithmetically from the notes*, and *no mechanism is asserted that the notes leave open*. Without these, the suite cannot distinguish a faithful report from a fluent one.

**7. Split the compound assertions.** eval-0 #5 bundles "no headers" with "no trailing summary," and eval-1 #5 bundles "no headers" with "under ~250 words." Both hide which half failed — eval-1's v0.2 failure is length-only, and a reader of the summary would not know that. One check per assertion.

**8. Consider trimming the skill rather than growing it.** v0.2.0 added roughly 20 lines and produced no measured improvement, one assertion regression, and 8% longer outputs. The parts that demonstrably fire are the anti-patterns table and the structure section. Before v0.3 adds more, it is worth running an ablation: does the table alone get 19/19?

**Ship as is?** No. Ship v0.2.0 only after recommendations 1 and 2; they are two paragraph edits and they address the only regression and the only fabrication class in the corpus. Everything below #3 can wait for a later pass.
