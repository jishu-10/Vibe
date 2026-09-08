# Campus Chemistry Vibe Engine V1 - Internal Requirement Matrix

This is the post-remediation implementation audit of the attached `CAMPUS CHEMISTRY | VIBE ENGINE V1.0 | ZERO-GAP CODEX BUILD SPECIFICATION` and Final Zero-Gap Completion Amendment. The amendment supersedes only the five previously unresolved paths recorded below; the final release-gap directive resolves only the explicitly recorded remediation paths and all other passing behavior is preserved.
The PDFs are the sole authority. This file is an engineering traceability artifact, not a product contract.

Status values: `PASS`, `IMPLEMENTATION_GAP`, `TEST_GAP`, `SPECIFICATION_GAP`. The current audit is authoritative for this delivery.

## Canonical versions, enums, and boundaries

| Spec requirement | Implementation target | Test target | Status |
| --- | --- | --- | --- |
| Questionnaire version `1.0` | `app/vibe/config/v1_1_0.py` / `config` | version contract tests | PASS |
| Signal model version `1.0` | versioned config | version contract tests | PASS |
| Dimension model version `1.0` | versioned config | version contract tests | PASS |
| Scoring model version `1.2.0` | versioned config | version contract tests | PASS |
| Narrative prompt version `1.0` | narrative contract/config | narrative boundary tests | PASS |
| Completion amendment version `1.0` and scoring-version increment | `config/v1_1_0.py`, `modes.py`, cache/profile version identity | amendment version/cache invalidation tests | PASS |
| Amendment A: D5 computed-negative/friction fields, hard threshold, and high-salience predicate | `pair/dimensions.py` | `test_amendment.py` GA-D5-01..07 | PASS |
| Amendment B: six Wildcard perturbation maps, clamp/recompute/ephemeral pipeline, eligibility/ranking | `wildcard.py`, versioned config | `test_amendment.py` GA-WC-01..08 | PASS |
| Amendment C: contrast weights, normalized contributions, score, omission boundary, evidence tie order | `contrast.py`, versioned config | `test_amendment.py` GA-CT-01..05 | PASS |
| Amendment D: profile evidence units, confidence factors/labels/strong-claim boundary | `confidence.py`, `profile.py` | `test_amendment.py` GA-CF-01..12 | PASS |
| Amendment cross-cutting: clamp/no-rounding/order/error/version/cache rules | config validators, pure functions, typed errors, migrations | boundary, replay, typed-error, and cache tests | PASS |
| Valid relationship modes: `DATE`, `FRIEND`, `HANGOUT` | `contracts.py`, `modes.py` | invalid-mode and mode-weight tests | PASS |
| Public pair chemistry labels: `NATURAL_CLICK`, `INTERESTING_CHEMISTRY`, `POTENTIAL_FRICTION` | `classify.py`, API schemas | classification/API tests | PASS |
| Confidence labels: `WEAK`, `MODERATE`, `STRONG`, `VERY_STRONG` | `confidence.py` / contracts | confidence threshold tests | PASS |
| Dimension relationships: `ALIGNMENT`, `COMPLEMENTARITY`, `NEUTRAL`, `SOFT_FRICTION`, `HARD_FRICTION` | pair contracts | relationship boundary tests | PASS |
| Pair result internal final score only; never public percentage | API serializer | public boundary test | PASS |
| Pair engine is request-time only after explicit trigger | API/application layer | trigger/background tests | PASS |
| No recommendation feed/ranking/all-user scoring | application boundary | no-go/side-effect tests | PASS |
| Deterministic engine has no randomness or timestamps in scoring | pure engine functions | replay/determinism tests | PASS |
| Retired similarity engine removed from active code, routes, models, services, and runtime configuration | `app/api/router.py`, `app/models.py`, `app/services/`, `app/api/routes/`, `0005_remove_similarity_engine.py` | full suite, route-removal test, migration upgrade test, production-source search | PASS |
| Dedicated Wildcard scoring context is versioned, D1-D9 complete, D10-excluded, and independent of DATE/FRIEND/HANGOUT | `config/v1_1_0.py`, `pair/modes.py`, `wildcard.py` | `test_release_gap_remediation.py::test_valid_wildcard_configuration_is_dedicated_and_normalized` | PASS |
| Required Wildcard signals fail closed with `SPEC_CONTRACT_ERROR` and an exact signal path | `wildcard.py`, `dimensions.py`, `pair/dimensions.py` | `test_release_gap_remediation.py::test_missing_wildcard_signals_fail_closed`, `::test_missing_wildcard_signal_object_fails_closed` | PASS |
| Configuration validation executes before affected calculations and rejects malformed deltas, weights, multipliers, thresholds, matrices, prototypes, and blocks | `pair/modes.py::validate_configuration` | remediation malformed-configuration tests | PASS |
| Narrative claims are semantically bounded by deterministic claim terms in addition to evidence IDs | `config/v1_1_0.py`, `narrative.py` | `test_release_gap_remediation.py::test_llm_claim_envelope_rejects_valid_evidence_with_unsupported_prose`, T28/T29 | PASS |
| Profile optimistic concurrency returns 409 `PROFILE_VERSION_CONFLICT` and preserves current data | `schemas.py`, `routes/vibe.py`, `services/vibe_service.py` | `tests/test_api.py::test_profile_version_conflict_is_optimistic_and_preserves_current_data` | PASS |
| Production profile path executes validation -> mapping -> dimensions -> evidence/confidence -> contrast -> Wildcard -> narrative | `profile.py`, `contrast.py`, `wildcard.py`, `narrative.py` | profile pipeline, amendment, and remediation profile tests | PASS |
| Protected Vibe operations fail before data access without required authorization | `api/deps.py`, `api/routes/vibe.py` | `tests/test_api.py::test_unauthorized_profile_and_pair_operations_fail_before_data_access` | PASS |
| Pair observability persists the deterministic trace and request/cache metadata needed for replay without LLM rerun | `pair/engine.py`, `services/vibe_service.py`, `models.py` | `tests/vibe/test_acceptance_ids.py::test_observability_replay_has_versions_trace_cache_hit_and_request_metadata` | PASS |
| Remediation threshold boundaries cover Wildcard, contrast, classification, productive difference, hard counts, and confidence at X-epsilon/X/X+epsilon | threshold classifiers and config | `tests/vibe/test_release_gap_remediation.py` boundary tests | PASS |

## Section-by-section matrix

| Spec section / requirement | Implementation target | Test target | Status |
| --- | --- | --- | --- |
| 0: exactly one valid answer to each Q1-Q10 produces versioned signals/profile | questionnaire, signal map, profile pipeline | T01, incomplete tests | PASS |
| 0.1: question bank is Section 4; mappings Section 5; dimensions Section 8; pair rules Section 14; weights Sections 13/16; score Section 17; class Section 20; UX Sections 1.3/24; narrative Section 23 | module ownership and contract tests | traceability/replay tests | PASS |
| 0.2: question weights use arithmetic total 10.05; no hidden divisor | config question weights | weight arithmetic test | PASS |
| 0.2: mode weights are base x multiplier; normalize D1-D9 only | `modes.py` | Z11, mode tests | PASS |
| 0.2: D10 is context-only and has zero component contribution | `phase.py`, aggregation | T14/T15, Z10 | PASS |
| 0.2: phase adjustment max absolute value is 0.05 | D10 phase matrix | phase boundary test | PASS |
| 0.2: alignment `>=0.50`, high-confidence alignment `>=0.65` | relationship classifier | threshold boundary tests | PASS |
| 0.2: hard friction interaction `<=-0.50` | relationship classifier | hard-friction boundary tests | PASS |
| 0.2: productive difference requires difference `>=0.30`, interaction `>=0.25`, no hard friction | aggregate/classification | productive-difference boundary tests | PASS |
| 0.2: fallback honors friction safeguards and stores `fallback_used=true` | `classify.py` | T21/T22, Z09 | PASS |
| 0.2/0.3: missing config or undefined enum fails `ENGINE_CONFIG_INVALID`; uncovered path fails `SPEC_CONTRACT_ERROR` | config validation / fail-closed error types | Z13 and error tests | PASS |
| 0.4: same answers/versions/config/mode produce byte-equivalent deterministic facts | canonical serialization/hash | replay tests | PASS |
| 1.1: 10-question assessment, static mapping, derived profile, all named profile sections, on-demand pair, evidence, confidence, versions/cache/logging/tests | complete engine boundary | T01-T30, Z01-Z15 | PASS |
| 1.2: no recommendations, background scoring, all-user matrices, automatic narratives, percentages, ML, ranking, outcome prediction | application/API scope | no-go tests | PASS |
| 1.3: locked journey from 10 questions through Vibe sections, browse, explicit Why You Two, optional Approach | API/service trigger model | API trigger tests | PASS |
| 2: questionnaire owns IDs/display/validation/version, not scoring/inference | questionnaire module | schema/ownership tests | PASS |
| 2: signal engine owns answer->raw signals/categories/clamps, not natural-language inference | `signal_map.py`, `signals.py` | mapping/normalization tests | PASS |
| 2: individual model owns dimensions/profile/evidence/confidence/contrast/wildcard, not pair candidates | profile modules | profile scope tests | PASS |
| 2: pair engine owns D1-D10 comparison, weights, components, final score, class, evidence, not prose | `pair/` modules | pair trace tests | PASS |
| 2: narrative renderer owns wording/order/tone/compression only | `narrative.py` | LLM boundary tests | PASS |
| 2: persistence/cache owns versioned results, not inference | persistence/cache | version/cache tests | PASS |
| 3: raw signals are continuous [0,1] or controlled categorical values | contracts/validation | signal invariant tests | PASS |
| 3: component scores and final internal score are [0,1] | aggregate/score | range tests | PASS |
| 3: interaction scores [-1,1] and dimension difference scores [0,1] | pair contracts | range tests | PASS |
| 3: current phase is Q5 and context-only in pair numerics | phase module | D10 exclusion tests | PASS |
| 3: confidence is evidence interpretation, not relationship-success probability | narrative/API language | confidence boundary tests | PASS |
| 4: exact 10-question bank and exactly four options each | questionnaire config | canonical question tests | PASS |
| 4: IDs are Q1_A..Q1_D through Q10_A..Q10_D | questionnaire schema | option enum tests | PASS |
| 4: display text for all 40 options is preserved exactly | questionnaire config | display-text fixture tests | PASS |
| 4.1: weights Q1=1.15, Q2=1.15, Q3=0.90, Q4=0.90, Q5=0.60, Q6=1.10, Q7=1.15, Q8=1.15, Q9=1.00, Q10=0.95; total 10.05 | config | arithmetic and metadata tests | PASS |
| 5: immutable mapping keyed by questionnaire+signal model versions | `signal_map.py`, versioned config | mapping version tests | PASS |
| 5: Q1 options map exact six signals and category: A high stimulation, B small group, C one-to-one, D low stimulation | signal map config | T04 and mapping matrix tests | PASS |
| 5: Q2 options map exact four signals and category: intellectual/emotional/playful/ambient comfort | signal map config | mapping matrix tests | PASS |
| 5: Q3 options map exact five signals and category: immediate/selective/observational/slow start | signal map config | mapping matrix tests | PASS |
| 5: Q4 options map exact five signals and category: energizer/regulator/playmaker/tuned-in | signal map config | T05 and mapping matrix tests | PASS |
| 5: Q5 options map exact categorical/context signals: exploring/building/present/pressured | signal map config | T06 and phase tests | PASS |
| 5: Q6 options map exact four signals and category: direct/process-then-talk/action-response/contextual | signal map config | T07 and prohibition tests | PASS |
| 5: Q7 options map exact signals/category: direct/presence/playful/attentive | signal map config | T08 and mapping tests | PASS |
| 5: Q8 options map exact planning signals/category: structured/flexible/spontaneous/variable | signal map config | mapping tests | PASS |
| 5: Q9 options map exact recharge signals/category: social/solitary/people-dependent/mixed | signal map config | mapping tests | PASS |
| 5: Q10 options map exact processing signals/category: deep/moderate/action/variable | signal map config | mapping tests | PASS |
| 5.11: prohibited inferences for Q1, Q2, Q3, Q4, Q5, Q6_B/Q6_C, Q10 | controlled labels and claim validator | forbidden-claim tests | PASS |
| 6: `clamp01(x)=max(0,min(1,x))` | `signals.py` | normalization tests | PASS |
| 6: weighted average is `sum(value*weight)/sum(weight)` | `signals.py` | weighted-average tests | PASS |
| 6: continuous invariant 0..1 and interaction invariant -1..1 | validators | invariant tests | PASS |
| 6: exactly one valid option per Q1-Q10; unknown/duplicate/missing/malformed/invalid category fails closed | questionnaire validation | T02/T03 and invalid-input tests | PASS |
| 6: no profile from incomplete assessment | profile boundary | T02/API 422 test | PASS |
| 6: no intermediate rounding; Decimal where practical or fixed IEEE-754 serialization | numeric engine / serializer | Z15 precision test | PASS |
| 6: categorical values remain categorical and use explicit matrices/rules only | dimension/pair contracts | categorical comparison tests | PASS |
| 7: D1 Conversation Orientation inputs Q2/Q4/Q7/Q10; labels intellectual/emotional/playful/ambient | dimension engine | D1 fixtures | PASS |
| 7: D2 Connection Style inputs Q2/Q6/Q7/Q10; labels depth/humor/attention/presence/direct/ease/emotion | dimension engine | D2 fixtures | PASS |
| 7: D3 Affection Style inputs Q7/Q2/Q6; labels direct/presence/playful/attentive | dimension engine | D3 fixtures | PASS |
| 7: D4 Social Rhythm inputs Q1/Q3/Q4/Q9; opening/warming/peak/recovery | dimension engine | D4/profile tests | PASS |
| 7: D5 Emotional Processing inputs Q6/Q10/Q3; four categories | dimension engine | D5 fixtures | PASS |
| 7: D6 Lifestyle Rhythm inputs Q8/Q5; planning style + phase pattern | dimension engine | D6 and D10 exclusion tests | PASS |
| 7: D7 Social Recharge inputs Q9/Q1/Q4; four categories | dimension engine | D7 fixtures | PASS |
| 7: D8 Interaction Pace inputs Q3/Q6/Q10; immediate/gradual/observational/process-first/action-first/variable | dimension engine | D8 fixtures | PASS |
| 7: D9 Energy Signature inputs Q1/Q4/Q9/Q10; seven labels | dimension engine | D9 fixtures | PASS |
| 7: D10 Current Phase input Q5; four labels | phase module | phase fixtures | PASS |
| 7: Social Friction Profile is derived internal feature set, not pair dimension 11/12 | profile module | dimension inventory test | PASS |
| 7.1: Social Energy formula `0.50 Q1.social_energy + 0.25 Q4.energy_contribution + 0.25 Q9.social_replenishment`; thresholds `<.25 LOW`, `.25-.44 LOW_MODERATE`, `.45-.64 MODERATE`, `.65-.79 HIGH`, `>=.80 VERY_HIGH` | dimensions.py | formula and threshold tests | PASS |
| 7.1: Social Density `0.60 Q1.social_density + 0.40 Q9.social_replenishment`; `<.30 LOW`, `.30-.59 MODERATE`, `>=.60 HIGH` | dimensions.py | boundary tests | PASS |
| 7.1: Social Selectivity `0.40*(1-max(Q1.group_orientation,Q1.one_to_one_preference))+0.60 Q3.social_selectivity`; `<.35 OPEN`, `.35-.64 MODERATE`, `>=.65 SELECTIVE` | dimensions.py | boundary/tie tests | PASS |
| 7.1: Connection Depth `max(Q2.intellectual_depth,Q2.emotional_depth)`; tie is INTELLECTUAL | dimensions.py | tie/formula tests | PASS |
| 7.1: Humor Connection `0.50 Q2.humor_connection + 0.25 Q4.humor_presence + 0.25 Q7.playful_affection`; `<.35 LOW`, `.35-.64 MODERATE`, `.65-.79 HIGH`, `>=.80 VERY_HIGH` | dimensions.py | boundary tests | PASS |
| 7.1: Introspection `0.75 Q10.introspection + 0.25 Q6.processing_delay`; `<.30 ACTION_ORIENTED`, `.30-.59 MODERATE`, `>=.60 HIGHLY_INTERNAL` | dimensions.py | boundary tests | PASS |
| 7.1: Social Recovery equals Q9 category | dimensions.py | category-preservation tests | PASS |
| 7.2: Conversation Orientation is exactly Q2.primary_category; support signals never replace Q2 | dimensions.py | category precedence tests | PASS |
| 7.3: Affection Style is exactly Q7.category; no receiving preference inference | dimensions.py | category/prohibition tests | PASS |
| 7.4: exact D2 mode scores for DEPTH_LED, EMOTION_LED, HUMOR_LED, ATTENTION_LED, PRESENCE_LED, DIRECT, EASE_LED | dimensions.py | score fixtures | PASS |
| 7.4: D2 keeps every mode >=.65; top two descending; if none top one; exact tie order ATTENTION > HUMOR > PRESENCE > DEPTH > DIRECT > EASE > EMOTION | dimensions.py | Z01 and tie tests | PASS |
| 7.5: D8 precedence: variability >=.70; action-first; process-first; observational; immediate; else gradual | dimensions.py | precedence/boundary tests | PASS |
| 7.6: exact seven D9 label formulas; primary max; secondary only score >=.65 and within .10; tie order PLAYFUL > ENERGIZER > SOCIAL_CATALYST > TUNED_IN > RELAXED > INTENSE > UNDERSTATED | dimensions.py | D9 formula/tie tests | PASS |
| 7.7: planning_style=Q8 category, current_phase=Q5 category; exact 16 display-tag combinations | dimensions.py | display-tag matrix tests | PASS |
| 8: profile generated only after all answers and reused until answer/model invalidation | profile service/cache | profile lifecycle tests | PASS |
| 8.1: profile fields user_id/profile_version/answers/signals/derived/evidence/confidence/narrative/generated_at/engine_versions | profile contracts/persistence | profile shape tests | PASS |
| 8.2: exact profile section limits for Vibe, Rhythm, Connection, Energy, Pulls, Drains, Phase, Different People, Wildcard | profile/narrative contracts | profile-limit tests | PASS |
| 8.3: rhythm opening, warming thresholds, peak predicates/tie order, Q9 recovery | profile.py | rhythm threshold/tie tests | PASS |
| 8.4: eight Pull codes and exact eligibility predicates | profile.py config | pull eligibility/ranking tests | PASS |
| 8.4: Pull rank by primary signal, secondary signal, fixed code order; up to four/all eligible/empty no fabrication and low confidence | profile.py | Z08 and pull tests | PASS |
| 8.5: seven Drain codes and exact eligibility predicates; describe behaviors not bad people | profile.py config | drain tests/claim tests | PASS |
| 9: four contrast prototypes use exact 10-answer vectors | contrast.py | prototype fixture tests | PASS |
| 9: prototype goes through same pipeline; compare D1-D9; no chemistry classification; highest relevance + support; tie D4>D1>D6>D7>D8>D9>D5>D2>D3 | contrast.py | contrast ranking/tie tests | PASS |
| 10.1: Wildcard candidates fixed set HIGHER_ENERGY, MORE_DIRECT, MORE_SPONTANEOUS, MORE_STRUCTURED, MORE_SOCIAL, MORE_TUNED_IN; controlled perturbations of own profile | wildcard.py | candidate-generation tests | PASS |
| 10.2: eligibility difference>=.30, complementarity>=.35, friction<.35, hard count=0 | wildcard.py | threshold/safety tests | PASS |
| 10.3: score=difference*complementarity*(1-friction); tie score, comp, difference, fixed archetype order | wildcard.py | Z07/T30-style tie tests | PASS |
| 10: no qualifying wildcard means no wildcard; never opposite/user/recommendation/hard-friction candidate | wildcard.py | T30/Wildcard safety tests | PASS |
| 11: pair engine only explicit action with one mode | pair service/API | trigger tests | PASS |
| 11: DATE emphasis conversation/connection/affection/emotional processing; FRIEND rhythm/conversation/recharge/energy; HANGOUT rhythm/lifestyle/recharge/energy | modes config | mode emphasis tests | PASS |
| 11.1: A/B symmetry for all D1-D10 scores, components, final, phase, counts, classification | pair engine canonical ordering | T23/Z12/property symmetry | PASS |
| 12: exact DATE effective and normalized weights; D10 context-only; D1-D9 denominator 9.8350 | modes.py config | mode weight fixture | PASS |
| 12: exact FRIEND effective and normalized weights; D10 context-only; D1-D9 denominator 9.4700 | modes.py config | mode weight fixture | PASS |
| 12: exact HANGOUT effective and normalized weights; D10 context-only; D1-D9 denominator 8.7725 | modes.py config | mode weight fixture | PASS |
| 12.4: raw=base*multiplier; normalized=raw/sum(D1..D9); D10 CONTEXT_ONLY | modes.py | Z11 | PASS |
| 13.1: dimension result fields dimension, relationship, interaction_score, difference_score, confidence, evidence, narrative_permission | pair contracts | record shape tests | PASS |
| 13.2: generic continuous evaluator exact gap bands/formulas and policy scope D4/D5/D8/D9 only | continuous.py | evaluator formula/boundary tests | PASS |
| 13.3: exact D1 4x4 matrix | matrices.py | all matrix entries/symmetry tests | PASS |
| 13.4: D2 shared/label_gap, productive pairs, direct interference, thresholds, D5 friction guard, tie top modes | connection.py | D2 fixtures/T12 | PASS |
| 13.5: exact D3 4x4 matrix | matrices.py | all matrix entries/symmetry tests | PASS |
| 13.6: D4 feature weights, productive guard, interference policy, precedence, generic evaluator use | pair/d4.py | T13/Z02/Z03 | PASS |
| 13.7: D5 feature weights, high-salience predicate, productive pairs, gap/friction rules | pair/d5.py | T14/Z04/Z05 | PASS |
| 13.8: exact D6 4x4 matrix; Q8 only, Q5 excluded | matrices.py | T09 and D10 exclusion tests | PASS |
| 13.9: exact D7 4x4 matrix | matrices.py | T10 and matrix tests | PASS |
| 13.10: D8 feature weights, productive/hard pairs and exact gap rules | pair/d8.py | T14/Z05 | PASS |
| 13.11: D9 feature weights, productive pairs, D7-conditioned interference, exact rules | pair/d9.py | T13/Z06 | PASS |
| 13.12: exact symmetric D10 phase matrix; phase adjustment only | phase.py | T15/Z10 | PASS |
| 13.13: exact difference scores for continuous, D2, categorical, D10 relationships | pair contracts | difference convention tests | PASS |
| 14: interaction classification exact thresholds and hard-friction <=-.50 | classify/dimension relation | boundary tests | PASS |
| 15: conditional-capacity alignment/complementarity/friction aggregation and clamp | aggregate.py | component formula/capacity tests | PASS |
| 15.1: exact friction/complementarity multipliers by D1-D9 | config | multiplier fixture tests | PASS |
| 16: hard count, four friction groups, reinforced group count | aggregate.py | group-count tests | PASS |
| 16: productive difference count exact predicates and hard-friction guard | aggregate.py | T17/Z09 | PASS |
| 17: exact RAW_FINAL, normalized, pre-phase, final formulas and internal-only boundary | aggregate.py | final-score fixtures/boundaries | PASS |
| 17.2: D10 phase adjustment only, max .05, no second Q5 adjustment | phase/aggregate | T15/Z10 | PASS |
| 17.3: canonical numerical examples: Natural 0.7781, Interesting fixture 0.6467, Potential 0.3117 | aggregate/classify | golden score fixtures | PASS |
| 18.1: Potential override if friction>=.50 OR hard>=2 OR hard>=1+reinforced>=1+final<.55 | classify.py | T18-T20/boundaries | PASS |
| 18.2: Natural requires final>=.65, alignment>=.55, friction<.35, hard=0 | classify.py | gate boundary tests | PASS |
| 18.3: Interesting requires final>=.45, complementarity>=.35, friction<.50, productive>=1, hard=0 | classify.py | T16/T17/boundaries | PASS |
| 18.4: exact evaluation order and friction-safe fallback; `fallback_used=true`; downgrade certainty | classify.py/narrative | T21/T22/Z09 | PASS |
| 19: evidence count factor .50/.75/1.00; signal strength .25/.50/.75/1.00; consistency .25/.50/.75/1.00; mean formula | confidence.py | confidence boundary tests | PASS |
| 19: labels <.50 WEAK, .50-.69 MODERATE, .70-.84 STRONG, >=.85 VERY_STRONG | confidence.py | threshold boundary tests | PASS |
| 19: pair confidence weighted mean by insight_priority; no evidence=0 | confidence.py | evidence confidence tests | PASS |
| 20: mode relevance, effective dimension weight, insight priority exact formulas | evidence.py | evidence priority tests | PASS |
| 20: positive eligibility >=+.65; complementary >=+.25 + difference>=.30 + complementarity; friction <=-.35 | evidence.py | evidence eligibility tests | PASS |
| 20: max 3 positive/interesting, max 1 friction/difference, max 4 total | evidence.py | evidence limit tests | PASS |
| 20: tie-break priority, confidence, absolute interaction, D1>D2>...>D9 | evidence.py | deterministic tie tests | PASS |
| 21.1: exact LLM input fields including scores, counts, evidence, allowed/forbidden claims, confidence, fallback | narrative.py | payload schema tests | PASS |
| 21.2: LLM can phrase/order/tone/compress only; cannot score/classify/change relationship/invent evidence/traits; strong claims require >=.70 | narrative.py/validator | T28/T29 and boundary tests | PASS |
| 21.3: forbidden claims include attachment, trauma, diagnosis, clinical personality, avoidant/anxious, soulmate/destiny, guarantees, outcome prediction, IQ, social anxiety | narrative validator | forbidden-language tests | PASS |
| 21.4: approved qualified language set | narrative contract | claim-language tests | PASS |
| 22: Why You Two has 2-3 positive observations, 0/1 evidence-backed difference, 1 qualified meaning, exactly one label, max 4 internal evidence, strongest first | pair narrative/API | API output tests | PASS |
| 22: Why You Two only explicit trigger; profile open never triggers | API route/service | trigger/background tests | PASS |
| 23: How To Approach is second explicit trigger, inputs signal reps+pair+mode, output tone/opener_type/works/avoid/better_opener | approach.py/API | approach trigger/schema tests | PASS |
| 23: approach uses only existing evidence, short/concrete, no guarantees, softer below .70 | approach.py/validator | evidence/claim tests | PASS |
| 24.1: profile version derives from canonical answers + questionnaire/signal/dimension/config | versioning.py | profile hash/version tests | PASS |
| 24.2: pair cache SHA256 canonical JSON of sorted IDs, mode, A/B versions, questionnaire/signal/dimension/scoring/narrative versions | cache.py | Z12/cache-key tests | PASS |
| 24.2: preserve request order separately for display metadata | cache/persistence | request-order test | PASS |
| 24.3: answer/questionnaire/signal/dimension/scoring/narrative/Q5 invalidation rules exact | cache/invalidation | T25/T26/version tests | PASS |
| 25: exact six API endpoint behaviors | API routes/services | API contract tests | PASS |
| 25.1: exact profile compute/pair analyze/approach request JSON shapes | schemas.py | schema tests | PASS |
| 25.2: exact public pair response and internal-score stripping | API serializers | T27/public boundary tests | PASS |
| 26: 400 INVALID_ANSWER_CODE | API error mapper | invalid option API test | PASS |
| 26: 409 PROFILE_VERSION_CONFLICT | profile update boundary | stale update test | PASS |
| 26: 422 INCOMPLETE_ASSESSMENT | profile compute | T02/API test | PASS |
| 26: 422 INVALID_MODE | pair API | invalid mode test | PASS |
| 26: 404 PROFILE_NOT_FOUND | pair API | missing profile test | PASS |
| 26: 409 VERSION_MISMATCH and re-computation rule | pair service | version mismatch test | PASS |
| 26: 500 ENGINE_CONFIG_INVALID | config validation | Z13 | PASS |
| 26: 500 SPEC_CONTRACT_ERROR with exact path | fail-closed policy dispatch | uncovered path test | PASS |
| 26: 502 NARRATIVE_RENDER_ERROR with deterministic facts/status and no invented narrative | narrative API | LLM outage test | PASS |
| 27: no randomness/timestamps/unordered tie behavior; canonical JSON; LLM never influences facts; A/B symmetry; cache cannot change correctness; no defaults | engine/cache/narrative | Z12/Z14/Z15/property tests | PASS |
| 28: recommended logical module boundaries and versioned config shape | `app/vibe/` package | import/module boundary tests | PASS |
| 29: exact versions, question weights, component weights, thresholds, chemistry thresholds, phase adjustments, narrative limits | `config/v1_1_0.py` | config snapshot test | PASS |
| 29: deployed config must additionally contain complete option maps, matrices, multipliers, tie-breaks, libraries, prototypes, prompt contract; no ellipses | config validation | Z13/config completeness test | PASS |
| 30: reference `build_profile` pipeline exact stages | profile orchestrator | pipeline trace test | PASS |
| 30: reference `analyze_pair` pipeline exact stages | pair orchestrator | pair trace test | PASS |
| 31: T01 complete assessment | tests/golden | T01 | PASS |
| 31: T02 missing answer -> INCOMPLETE/no profile | tests/golden | T02 | PASS |
| 31: T03 unknown option -> INVALID_ANSWER_CODE | tests/golden | T03 | PASS |
| 31: T04 Q1_A exact six raw values | tests/golden | T04 | PASS |
| 31: T05 Q4_D exact five raw values | tests/golden | T05 | PASS |
| 31: T06 Q5_D PRESSURED/context | tests/golden | T06 | PASS |
| 31: T07 Q6_C ACTION_RESPONSE/no avoidant | tests/golden | T07 | PASS |
| 31: T08 Q7_D ATTENTIVE/no receiving preference | tests/golden | T08 | PASS |
| 31: T09 Q8_A x Q8_C D6=-.80 hard | tests/golden | T09 | PASS |
| 31: T10 Q9_A x Q9_B D7=-.60 hard | tests/golden | T10 | PASS |
| 31: T11 Q2_C x Q2_C D1=+.95 alignment | tests/golden | T11 | PASS |
| 31: T12 Q2_A x Q2_D D1=-.55 hard | tests/golden | T12 | PASS |
| 31: T13 ENERGIZER x RELAXED D9 complementarity | tests/golden | T13 | PASS |
| 31: T14 IMMEDIATE x PROCESS_FIRST D8 hard at high gap | tests/golden | T14 | PASS |
| 31: T15 same phase +.05 and no D10 component contribution | tests/golden | T15 | PASS |
| 31: T16 Natural Click requires all gates | tests/golden | T16 | PASS |
| 31: T17 Interesting requires productive difference | tests/golden | T17 | PASS |
| 31: T18 friction>=.50 overrides positive score | tests/golden | T18 | PASS |
| 31: T19 two hard frictions -> Potential | tests/golden | T19 | PASS |
| 31: T20 hard+reinforced+final<.55 -> Potential | tests/golden | T20 | PASS |
| 31: T21 fallback productive difference -> Interesting/fallback | tests/golden | T21 | PASS |
| 31: T22 fallback alignment dominant -> Natural/fallback | tests/golden | T22 | PASS |
| 31: T23 A/B symmetry | tests/golden | T23 | PASS |
| 31: T24 same pair, modes differ | tests/golden | T24 | PASS |
| 31: T25 answer change only affected user and pair caches | tests/golden | T25 | PASS |
| 31: T26 scoring version invalidates pair caches | tests/golden | T26 | PASS |
| 31: T27 no public internal score | tests/golden | T27 | PASS |
| 31: T28 unsupported LLM evidence blocked | tests/golden | T28 | PASS |
| 31: T29 forbidden LLM claim blocked | tests/golden | T29 | PASS |
| 31: T30 severe-friction wildcard rejected | tests/golden | T30 | PASS |
| 31.1: Z01 D2 top-mode tie fixed order | tests/zero_gap | Z01 | PASS |
| 31.1: Z02 D4 productive category predicates explicit | tests/zero_gap | Z02 | PASS |
| 31.1: Z03 D4 high-energy/social vs low/solitary interference | tests/zero_gap | Z03 | PASS |
| 31.1: Z04 D5 all high-salience predicates required | tests/zero_gap | Z04 | PASS |
| 31.1: Z05 D8 hard pairs exact threshold | tests/zero_gap | Z05 | PASS |
| 31.1: Z06 D9 D7 friction + energy gap >.50 interference | tests/zero_gap | Z06 | PASS |
| 31.1: Z07 wildcard fixed archetype tie | tests/zero_gap | Z07 | PASS |
| 31.1: Z08 pull/drain shortage no fabrication | tests/zero_gap | Z08 | PASS |
| 31.1: Z09 fallback cannot bypass friction | tests/zero_gap | Z09 | PASS |
| 31.1: Z10 D10 only phase/context evidence | tests/zero_gap | Z10 | PASS |
| 31.1: Z11 D1-D9 normalized weights sum 1 | tests/zero_gap | Z11 | PASS |
| 31.1: Z12 symmetric cache key/result | tests/zero_gap | Z12 | PASS |
| 31.1: Z13 missing config -> ENGINE_CONFIG_INVALID | tests/zero_gap | Z13 | PASS |
| 31.1: Z14 LLM outage leaves deterministic facts | tests/zero_gap | Z14 | PASS |
| 31.1: Z15 unrounded intermediate/persistence-boundary rounding | tests/zero_gap | Z15 | PASS |
| 32: all observability fields including request/profile versions, mode, versions, config hash, D1-D10, components, final, phase, class, fallback, evidence, confidence, cache hit, spec path | result/debug object and persistence | observability/replay tests | PASS |
| 32: pair auditable without rerunning LLM | stored deterministic trace | audit reconstruction test | PASS |
| 33: authorization boundaries, public stripping, controlled labels, minimum evidence prompts, no ranking side effect | API/service boundary | security/scope tests | PASS |
| 34: implementation checklist 01-32 | module/test checklist | matrix review | PASS |
| 35: explicit prohibited behaviors | architecture/API/validator | no-go tests | PASS |
| 36: all acceptance criteria including fresh clone, static mapping, executable dimensions, no undefined guards, stored replay, trigger-only pair, no ranking, symmetry, public boundary | full suite | acceptance tests | PASS |
| 37: final input->validation->mapping->profile->explicit pair->components->score->override/class->evidence->LLM flow | orchestrators | end-to-end trace | PASS |
| 38: source traceability for UX/questions/mapping/normalization/dimensions/matrices/weights/score/class/confidence/evidence/LLM/approach/cache/API/testing/checklist | this matrix + code trace fields | traceability audit | PASS |
| 39: zero-gap fail-closed rule for any uncovered runtime case | error boundary | uncovered path test | PASS |

## Amendment-resolved gap register

| Gap | Exact location | Affected path | Required behavior | Status |
| --- | --- | --- | --- | --- |
| D5 friction guard field/formula | Base Sections 13.4/13.7/13.10; Amendment Completion A | `app/vibe/pair/dimensions.py` | `computed_negative_score=max(0,-interaction_score)` and `friction_score=computed_negative_score`; D2/D8 guards consume the per-dimension value | PASS |
| D5 high-salience formula | Base Section 13.7; Amendment Completion A | `d5_high_salience()` and `compare_d5()` | Inclusive direct-gap, delay-gap, and negative-score thresholds; no intermediate rounding | PASS |
| Wildcard construction | Base Sections 10.1-10.3; Amendment Completion B | `app/vibe/wildcard.py` | Six exact archetype deltas, clamp, categorical preservation, recomputation, eligibility, ranking, no-user persistence | PASS |
| Contrast relevance/support | Base Section 9; Amendment Completion C | `app/vibe/contrast.py` | Exact D1-D9 weights, normalized contributions, score formula, omission boundary, evidence ranking, no chemistry classification | PASS |
| Profile confidence derivation | Base Sections 8/19/30; Amendment Completion D | `app/vibe/confidence.py`, `profile.py` | Unique evidence units, strength/consistency factors, D1-D10 weighted mean, labels, strong-claim guard | PASS |

## Final release-gap remediation register

| Gap | Canonical/directive location | Implementation | Test evidence | Status |
| --- | --- | --- | --- | --- |
| SG-01 Wildcard scoring context | Final Release-Gap Remediation Directive §4; Amendment Wildcard contract | `config/v1_1_0.py::WILDCARD_*`, `pair/modes.py::wildcard_effective_weights`, `wildcard.py` | dedicated-config, version, denominator, and six-archetype tests | PASS |
| IG-01 Missing signal fail-closed | Final Release-Gap Remediation Directive §5; Amendment fail-closed rule | `wildcard.py::perturb_signals` | one missing, multiple missing, and missing signal-object tests | PASS |
| IG-02 Executable configuration validation | Final Release-Gap Remediation Directive §6 | `pair/modes.py::validate_configuration` called by profile/pair paths | malformed delta/weight/multiplier/enum/matrix/threshold/prototype/block tests | PASS |
| IG-03 Semantic LLM claim envelope | Final Release-Gap Remediation Directive §7; Build Spec §21 | `config/v1_1_0.py::NARRATIVE_*`, `narrative.py` | valid-evidence unsupported-prose, invented claim, forbidden-claim, and confidence tests | PASS |
| IG-04 Profile version conflict | Final Release-Gap Remediation Directive §8; Build Spec §26 | `schemas.py`, `routes/vibe.py`, `services/vibe_service.py` | matching, stale 409, no-overwrite, increment, and deterministic stale-update tests | PASS |
| IG-05 Profile/auth/observability completion | Final Release-Gap Remediation Directive §9 | profile orchestrator, auth dependency, pair persistence/trace | profile pipeline, authorization, observability, and API tests | PASS |
| TG-01 Boundary coverage | Final Release-Gap Remediation Directive §10 | canonical threshold classifiers and config | Wildcard, contrast, classification, confidence, productive-difference, hard-count boundaries | PASS |
| Mandatory negative probes | Final Release-Gap Remediation Directive §15 | fail-closed validators and API scope guards | remediation, API, T28/T29, trigger, public-boundary, and Vibe-only route tests | PASS |
| Static V1 audit | Final Release-Gap Remediation Directive §16 | V1 import graph and production paths | repository search plus route/import isolation tests | PASS |

## Threshold and boundary test inventory

For every threshold below, tests must cover `X-epsilon`, `X`, and `X+epsilon` using the precision of the affected value, without intermediate rounding.

| Threshold family | Exact values |
| --- | --- |
| Individual profile labels | Social Energy .25/.45/.65/.80; Social Density .30/.60; Selectivity .35/.65; Humor .35/.65/.80; Introspection .30/.60; D2 mode .65; D8 .70/.75/.60; D9 secondary .65 and delta .10; pulls/drains predicates |
| Generic/dimension relationships | gaps .15/.30/.50/.60/.70; interaction +.50/+ .25/0/-.01/-.35/-.50; high-confidence +.65 |
| D2/D4/D5/D8/D9 policy guards | label gap .30/.60/.80; D5 direct gap .55, delay gap .50; D8 gap .30/.60/.70; D9 energy gap .50/.60 |
| Mode/final classification | alignment .50/.55/.65; complementarity .25/.35; friction .35/.50; final .45/.55/.65; productive diff .30/.25; hard count 0/1/2 |
| Wildcard | difference .30; complementarity .35; friction exclusive .35; hard count 0 |
| Confidence | signal strength .40/.60/.80; labels .50/.70/.85; strong-claim boundary .70 |
| Phase | exact matrix values +.05, +.025, 0, -.025; max absolute .05 |

## Final audit ledger

This ledger is updated after implementation and test execution. No `PASS` is valid without an implementation target and passing test target.

| Audit result | Meaning |
| --- | --- |
| `PASS` | Implemented and tested against the canonical rule. |
| `IMPLEMENTATION_GAP` | Canonical behavior is known but missing or divergent in code. |
| `TEST_GAP` | Code exists but a required canonical/boundary/golden test is missing or failing. |
| `SPECIFICATION_GAP` | Runtime path is not defined by the PDF; fail closed and report exact path. |

## Final grouped zero-gap audit

| Spec requirement group | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Sections 0-6: authority, locked UX boundary, versions, exact Q1-Q10 schema, static mappings, validation, normalization, no intermediate rounding | `app/vibe/config/v1_1_0.py`, `questionnaire.py`, `signal_map.py`, `signals.py` | `tests/vibe/test_questionnaire_and_cache.py`, `tests/vibe/test_canonical_core.py`, API invalid-input tests | PASS |
| Section 7: individual dimensions, formulas, labels, tie-breaks, D10 representation | `app/vibe/dimensions.py` | matrix, mapping, mode, and boundary tests | PASS |
| Section 8: complete profile generation including all profile sections and narrative | `app/vibe/profile.py`, `confidence.py`, `narrative.py` | profile/amendment/API section-limit tests | PASS |
| Section 9: contrast prototypes and relevance selection | `app/vibe/contrast.py` | GA-CT-01..05 and prototype/ranking tests | PASS |
| Section 10: Wildcard candidate generation/eligibility/ranking | `app/vibe/wildcard.py` | GA-WC-01..08, T30, Z07 | PASS |
| Sections 11-14: explicit pair modes, symmetry, matrices, continuous policies, interaction thresholds | `app/vibe/pair/`, `contracts.py`, amendment D5 guard | T09-T15, T23-T24, Z01-Z06, GA-D5-01..07 | PASS |
| Sections 15-18: conditional aggregation, multipliers, friction groups, final score, classification, fallback | `pair/aggregate.py` | score/classification threshold and override tests | PASS |
| Sections 19-20: confidence and evidence ranking | `app/vibe/confidence.py`, `app/vibe/pair/evidence.py` | confidence boundaries, evidence contract, GA-CF tests | PASS |
| Sections 21-23: LLM boundary, Why You Two, Approach | `app/vibe/narrative.py`, explicit pair/approach routes | T27-T29, API trigger/schema tests | PASS |
| Section 24: profile/pair versioning, symmetric cache identity, invalidation | `versioning.py`, `cache.py`, `vibe_service.py`, migrations `0003`/`0004` | T25-T26, Z12, replay/cache observability tests | PASS |
| Sections 25-27: API/error contracts, determinism, public data boundary | `app/api/routes/vibe.py`, schemas, fail-closed `VibeError` | API status/serialization/trigger tests | PASS |
| Sections 28-30: module boundaries, complete config shape, reference orchestration | `app/vibe/` modules, centralized amendment-aware config, profile/pair pipelines | config/mode/pipeline tests | PASS |
| Sections 31/31.1: T01-T30 and Z01-Z15 | `tests/vibe/test_acceptance_ids.py`, `test_amendment.py`, `test_threshold_boundaries.py`, `test_release_gap_remediation.py`, canonical/API modules | 129-test suite, all IDs present and passing | PASS |
| Sections 32-33: observability reconstruction and security/authorization boundary | pair trace, version/cache metadata, migration `0004`, `require_vibe_service_authorization`, public serializers | replay/observability/auth/public-boundary tests | PASS |
| Sections 34-39: checklist, prohibited behavior, acceptance, final flow, traceability, fail-closed declaration | README, matrix, code trace fields, Vibe-only route boundary | full suite, route-isolation, typed-error tests | PASS |
| Zero-gap acceptance condition | Amendment-aware implementation with no unresolved runtime gaps | Full acceptance suite passing | PASS |

## Final release gate snapshot

| Gate | Actual result |
| --- | --- |
| `SPECIFICATION_GAP` | `0` |
| `IMPLEMENTATION_GAP` | `0` |
| `TEST_GAP` | `0` |
| `NEGATIVE_PROBE_FAILURES` | `0` |
| `THRESHOLD_COVERAGE_GAPS` | `0` |
| Full repository suite | `129 passed` |
| T01-T30 / Z01-Z15 / amendment / remediation / boundary suites | `PASS` |
| Pair A/B symmetry and deterministic replay | `PASS` |
| LLM evidence/claim boundary | `PASS` |
| Cache/version invalidation and public score stripping | `PASS` |
| Authorization and retired-route removal | `PASS` |

## Final remediation traceability table

| Requirement | PDF/directive section | Code location | Test | Actual result |
| --- | --- | --- | --- | --- |
| Dedicated Wildcard mode/configuration | Amendment Wildcard; remediation §4 | `app/vibe/config/v1_1_0.py`, `app/vibe/pair/modes.py` | `test_valid_wildcard_configuration_is_dedicated_and_normalized` | PASS |
| Wildcard missing signals fail closed | Amendment fail-closed; remediation §5 | `app/vibe/wildcard.py` | `test_missing_wildcard_signals_fail_closed`, `test_missing_wildcard_signal_object_fails_closed` | PASS |
| Config validation is reachable | Build Spec error contract; remediation §6 | `app/vibe/pair/modes.py::validate_configuration` | malformed configuration tests | PASS |
| Semantic narrative evidence/claim boundary | Build Spec §21; remediation §7 | `app/vibe/narrative.py`, `app/vibe/config/v1_1_0.py` | T28/T29 and remediation LLM tests | PASS |
| Optimistic profile update/version conflict | Build Spec §26; remediation §8 | `app/schemas.py`, `app/api/routes/vibe.py`, `app/services/vibe_service.py` | `test_profile_version_conflict_is_optimistic_and_preserves_current_data` | PASS |
| Complete profile pipeline | Build Spec §§8-10, 19, 23; remediation §9 | `app/vibe/profile.py`, `contrast.py`, `wildcard.py`, `narrative.py` | profile/amendment/remediation suite | PASS |
| Authorization boundary | Build Spec §33; remediation §9 | `app/api/deps.py`, `app/api/routes/vibe.py` | unauthorized profile/pair test | PASS |
| Deterministic pair trace/observability | Build Spec §32; remediation §9 | `app/vibe/pair/engine.py`, `app/services/vibe_service.py`, `app/models.py` | observability replay test | PASS |
| Wildcard/contrast/classification boundaries | Amendment boundaries; remediation §10 | `app/vibe/wildcard.py`, `contrast.py`, `pair/aggregate.py` | remediation threshold tests | PASS |
| Six Wildcard archetypes, clamping, safety, tie/no-candidate | Amendment Wildcard; remediation §11 | `app/vibe/wildcard.py` | deterministic archetype/clamp/safety tests | PASS |
| Contrast prototypes/relevance/omission | Amendment Contrast; remediation §12 | `app/vibe/contrast.py` | contrast prototype/boundary tests | PASS |
| Confidence formulas/labels/replay | Amendment Confidence; remediation §13 | `app/vibe/confidence.py`, `app/vibe/pair/evidence.py` | confidence boundary/determinism tests | PASS |
| Negative probes and retired-engine isolation | Build Spec §§26-27, 35; remediation §§15-16 | API scope, route graph, validators | full negative-probe and Vibe-only route tests | PASS |
| Zero-gap release gate | remediation §§18-20 | this matrix and full repository | full suite + second read-only audit | PASS |

## Delivery blockers

No delivery blockers remain after the final remediation and audit. Current counts are `SPECIFICATION_GAP=0`, `IMPLEMENTATION_GAP=0`, and `TEST_GAP=0`; negative-probe failures and threshold-coverage gaps are both zero.

