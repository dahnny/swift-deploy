package swiftdeploy.canary

import rego.v1

default decision := {
  "domain": "canary",
  "question": "pre_promote",
  "allow": false,
  "reason": "canary policy did not evaluate",
  "violations": ["policy evaluation failed"]
}

violation contains message if {
  input.question == "pre_promote"
  input.metrics.error_rate > input.limits.max_error_rate
  message := sprintf(
    "error rate %v%% is above allowed %v%%",
    [input.metrics.error_rate * 100, input.limits.max_error_rate * 100]
  )
}

violation contains message if {
  input.question == "pre_promote"
  input.metrics.p99_latency_seconds > input.limits.max_p99_latency_seconds
  message := sprintf(
    "p99 latency %vms is above allowed %vms",
    [input.metrics.p99_latency_seconds * 1000, input.limits.max_p99_latency_seconds * 1000]
  )
}

decision := output if {
  input.question == "pre_promote"
  count(violation) == 0
  output := {
    "domain": "canary",
    "question": "pre_promote",
    "allow": true,
    "reason": "canary metrics are within promotion limits",
    "violations": []
  }
}

decision := output if {
  input.question == "pre_promote"
  count(violation) > 0
  violations := [v | violation[v]]
  output := {
    "domain": "canary",
    "question": "pre_promote",
    "allow": false,
    "reason": concat("; ", violations),
    "violations": violations
  }
}
