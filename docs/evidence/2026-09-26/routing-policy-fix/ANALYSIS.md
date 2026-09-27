# Failure analysis

Source: unchanged 500-case run in ../english-minimal-500. Counts are observations;
behavioral explanations are deductions, not access to model reasoning.

| Expected        | Actual          | Count | Evidence-backed explanation                                                                                                                                                                               |
| --------------- | --------------- | ----: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| help_desk       | it              |    40 | Individual computers, peripherals, installations and accounts get the broad IT label despite the explicit support/infrastructure split. Case201: one laptop fails while colleagues work normally.         |
| payroll         | human_resources |    32 | Leave, certificates, contracts and employee records get the broad HR label. Here payroll deliberately includes Polish kadry/personnel administration. Case151: employment certificate after contract end. |
| other           | human_resources |    14 | General contact, facilities, vendors and media are overassigned to HR; resolved history can also bias a vague current request.                                                                            |
| other           | help_desk       |    12 | General help, furniture, lost property, cleaning and unclear contact requests treated as technical support.                                                                                               |
| other           | it              |     7 | Non-IT maintenance, unrelated questions or resolved technical history pull selection toward IT. Case465: a cold radiator.                                                                                 |
| other           | payroll         |     2 | Cases489/490: an unexplained reference number is assigned a meaning absent from the current request.                                                                                                      |
| human_resources | payroll         |     1 | Case97 asks for training about pay: subject wins over requested action.                                                                                                                                   |
| help_desk       | payroll         |     1 | Case273 asks to restore login to a leave portal: portal purpose wins over the login problem.                                                                                                              |

Total109. The first two errors account for72/109 (66.1%). These labels reflect
our declared company policy, not universal HR/payroll or help-desk/IT boundaries.
Do not relabel failures to improve the score. History is not the only cause:
54 wrong routes occur in base messages and55 in history variants. There are250
of each in the corpus. Missing-call errors are separate from those109.

## Missing calls: 38, all other

- 14 responses contain only other (one capitalized).
- 2 contain JSON as ordinary assistant text (405,413).
- 17 explicitly say forwarding/action/a tool call is unnecessary.
- 3 decline the task or offer/produce an answer instead (419,437,438).
- 2 ask for clarification (475,487).

All38 are HTTP200 with finish_reason=stop, nonempty content and no native calls.
The experiment bypasses LangChain and delivery; these failures already exist in
the upstream OpenAI-compatible response. There is no evidence here of a
LangChain schema-conversion error, HTTP failure, truncation or malformed native
arguments. Raw generation tokens were not saved, so parser involvement cannot
be categorically excluded for the two JSON-text cases.

The prompt said main unresolved request and only described other as unrelated
or unclear requests. Responses explicitly interpret unrelated/resolved messages
as reasons not to send anything. The old backport preserves this output; it does
not force the tool. The short prompt also removed explicit prohibitions against
text responses, inferred context and generic help-desk routing. The source of
each semantic mistake is not provable from outputs alone, and prompt/schema/
temperature changes were not independently controlled in the 500 comparison.

## Correction and limit

Make forwarding unconditional, define other as an actual catch-all mailbox,
state department responsibilities as company rules, distinguish requested action
from incidental topic, and ignore closed history when current text is vague.
The candidate is prompt.txt. No output conversion, retries, heuristic routing
or provider-specific client code is added. The application prompt is updated;
its existing described schema remains for the Laya contract. The minimal schema
experiment and the application therefore need separate validation.

A prompt is not native-call enforcement. LangChain already supplies tool_choice
through ModelRequest.override and ChatOpenAI. Ollama's ignored tool_choice is a
separate upstream limitation. Guaranteed constrained calls require server support;
setting required/named alone on this server does not implement it.

References inspected:

- https://docs.langchain.com/oss/python/integrations/chat/openai
- https://github.com/ollama/ollama/issues/17921
- [Backport scope](../../../OLLAMA_BACKPORT.md)

Fresh read-only critic independently confirmed counts, the three behavioral
patterns and the enforcement limitation. No additional taxonomy examples were
judged necessary.
