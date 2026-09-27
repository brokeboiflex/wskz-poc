# Independent review

Fresh agent tool_choice_critic inspected the local OpenAI -> API -> native transport and generic validation code. It found one blocker in candidate .1: rendered Qwen parsers can emit tool_calls even after offered tools are removed for explicit none. Candidate .2 rejects explicit none on rendered execution paths before inference, with regression coverage for native and rendered branches. The critic re-read the correction and found no remaining local blocker.

Omitted/auto behavior, named declaration membership plus narrowing, invalid choices and required-without-tools rejection, request copying through truncation, and local native forwarding were reviewed. Cloud/remote downstream enforcement is explicitly outside this verification. This is source review; build and runtime results are recorded separately.
