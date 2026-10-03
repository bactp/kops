# Topology spread constraints

## Approach
Remove `nodeSelector` and add `topologySpreadConstraints: [{maxSkew: 1, topologyKey: rack, whenUnsatisfiable: DoNotSchedule, labelSelector: {matchLabels: {app: {{app}}}}}]` in one JSON patch, then wait for the rollout.

## What the verifier checks
The constraint (key `rack`, maxSkew 1, DoNotSchedule, selector on the app label), no `rack` pin, and the resulting placement: 4 running pods on both workers with at most 2 per node.

## Why shortcuts fail
Removing the pin alone often yields a good placement but enforces nothing; `ScheduleAnyway` does not satisfy "must stay unscheduled rather than break the rule".
