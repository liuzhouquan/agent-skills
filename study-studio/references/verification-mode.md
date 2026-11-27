# Interview-style learning verification

Use this mode for an actual request to start questioning or verification, such as “开始验证”, “进行提问”, “面试问答”, or “开始追问”. Mentioning these phrases while discussing or editing the skill does not start a round. Ordinary learning stays conversational until the learner requests verification.

## Start with a bounded scope

Read `goal.md`, `plan.md`, `state.md`, the relevant draft topics and note index; consult only the supporting resources needed. The scope is the learner's current/past studied units and target mastery, not everything the assistant has read, everything in resources, or an unaccepted draft proposal. A learner-reported reading range may be used, but do not assume it proves mastery. If progress is ambiguous, state a narrow assumed diagnostic scope and let the learner adjust; do not block with an intake questionnaire.

Briefly announce the unit/goal, subject boundary and a short round (normally 3–5 core questions with bounded follow-ups, adjustable by the learner). Say that “提示”, “跳过”, “暂停验证” and “结束验证” are available. Preserve the ordinary learning position and begin with one core question. Do not output the answer, rubric, whole question bank or all follow-ups before the learner attempts it.

Prepare each question against a resource locator and expected key points. Recheck contested facts before correcting the learner. Course answer sheets, assistant notes and draft hypotheses are material to inspect, not unquestionable ground truth. When evidence is incomplete, mark the uncertainty rather than grade the learner against an invented answer.

## Ask, assess, correct, and follow up

Ask one focused question per turn and wait for the learner's answer. Follow-ups should respond to what they actually said; do not run a fixed interrogation irrespective of their answers.

- First check purpose and the main path, then implementation/data flow, design tradeoffs, failure cases or evidence, as relevant to the current goal.
- Use the learner's own claims as hooks: “which component does that?”, “what is its input/output?”, “what happens if it fails?”, “what evidence supports the improvement?” Ask one of these at a time.
- Distinguish a wrong concept, a missing detail, poor expression, and missing implementation evidence. Valid alternative designs can be accepted with their assumptions; don't require a canned wording or punish a truthful statement that a result has not been measured.
- After the answer, briefly identify what is correct and the most important gap. For an unclear answer ask a targeted clarification. For an error, offer a small hint or a concise correction and an appropriate source locator, then ask a rephrased/application question to check understanding. If the learner says they do not know or wants the explanation, teach it directly before retrying.
- For a strong answer, deepen within the scoped topic with a design or failure scenario. For repeated difficulty, stop escalating, explain the prerequisite and use an easier check. Usually limit a branch to 1–2 follow-ups; avoid looping on the same failure or drifting to unrelated algorithms, projects or future units.
- Keep an evidence record per question: asked question, concise learner answer, assessment and why, hint/correction given, follow-up response and source locator. Use `independent`, `partial`, `with_help`, `not_yet`, or `not_assessed` to distinguish performance. A repaired answer after instruction is useful progress but is not independent proof of mastery; check later with a different question.

For interview goals, probe ownership and measured outcomes only where the learner actually makes such claims. Help express real learning, design or implementation clearly; do not coach fabricated employment, deployments or metrics. STAR questions should match actual work and current study scope. Level 3 still requires the meaningful application/reproduction evidence defined in SKILL.md, not a polished verbal answer.

## End, pause, or resume

Honor “结束验证”, “先到这里”, “停止提问” and equivalent requests immediately; do not add another question. End naturally after the announced short scope is covered or fatigue/repeated prerequisite gaps make further probing unhelpful. Pausing saves the current question and gaps; switching to explanation or another task suspends the round rather than forcing more questions. Resume a paused round only when requested; do not treat ordinary “继续学习” as automatic continuation of an interrogation.

At exit, begin the response with one actionable recommendation:

- **继续往下学** — name the next unit and any minor point to revisit.
- **先复习再继续** — name the specific blocking concepts, exact reading pages/symbols and a small recheck activity.
- **暂不足以判断** — say which key area was not assessed, especially if the round ended early, and what check would resolve it.

Then give a short, evidence-backed debrief: independent strengths, corrected/assisted answers, remaining gaps, scope not covered and concrete next steps. Weight core prerequisite gaps more than raw correct-answer counts. Do not infer whole-project readiness from a few answers. Avoid numerical precision unless the learner requested and understood a rubric.

## Persist compactly and retain the learning position

Use a stable topic in `draft.md` for verification results under the current unit, with subheadings for rounds; do not create a note or topic for each question. Save a concise record rather than a transcript:

```markdown
### Verification round <ID> — <unit/topic>
- Scope / goals / date / outcome:
- Recommendation first: <continue/review/insufficient evidence + specific focus>
| Question / follow-up | Learner answer summary | Assessment / help | Evidence / remaining gap |
| --- | --- | --- | --- |
- Useful learner explanations worth keeping:
- Suggestions / new ideas and triggers:
- Next reading and recheck:
```

Store follow-ups with their parent question. Put good explanations in QA, and new suggestions in the topic's suggestion section with maturity, plan impact and triggers from `draft-workflow.md`. Propose consolidation only when a theme becomes sufficiently useful and supported. An ordinary review recommendation is not authority to rebuild the whole plan; apply only already authorized plan changes.

While a round is active, keep a compact `state.md` checkpoint after each evaluated answer: round ID/status, scope, original learning position, questions covered, current pending question, relevant draft link and main gaps. A different agent can resume from that checkpoint and the draft without previous chat history. Reuse the current session handoff; do not generate a session file after every answer. With simultaneous agents use the shared-write coordination rules.

At completion or pause, update the checkpoint and next action; update `goal.md` mastery only where learner evidence genuinely supports it, linking the round and preserving prior evidence. An isolated failure does not erase demonstrated mastery; record the gap for review. On interruption before any answer, record no performance judgment. Do not fabricate a verification record while merely configuring this mode.
