# PriorityClass

## Approach
`kubectl create priorityclass {{pc}} --value={{val}} --description="..."` (globalDefault is false unless requested), then
set `priorityClassName: {{pc}}` in the pod template (`kubectl patch deployment ...`) and wait for the rollout. At pod creation the Priority admission plugin resolves the name and writes the numeric `spec.priority` into each pod.

## What the verifier checks
The class exists with value {{val}}, the running pods have `spec.priority == {{val}}`, the rollout is complete, and the class is not a global default.

## Why shortcuts fail
A class that is not referenced changes nothing; a system class yields a different priority number.
