package swiftdeploy.infra

import rego.v1

default decision := {
  "domain": "infrastructure",
  "question": "pre_deploy",
  "allow": false,
  "reason": "infrastructure policy did not evaluate",
  "violations": ["policy evaluation failed"]
}

violation contains message if {
  input.question == "pre_deploy"
  input.host.disk_free_gb < input.limits.min_disk_free_gb
  message := sprintf(
    "disk free %.2fGB is below required %.2fGB",
    [input.host.disk_free_gb, input.limits.min_disk_free_gb]
  )
}

violation contains message if {
  input.question == "pre_deploy"
  input.host.cpu_load_1m > input.limits.max_cpu_load_1m
  message := sprintf(
    "CPU load %.2f is above allowed %.2f",
    [input.host.cpu_load_1m, input.limits.max_cpu_load_1m]
  )
}

decision := output if {
  input.question == "pre_deploy"
  count(violation) == 0
  output := {
    "domain": "infrastructure",
    "question": "pre_deploy",
    "allow": true,
    "reason": "host satisfies infrastructure deployment limits",
    "violations": []
  }
}

decision := output if {
  input.question == "pre_deploy"
  count(violation) > 0
  violations := [v | violation[v]]
  output := {
    "domain": "infrastructure",
    "question": "pre_deploy",
    "allow": false,
    "reason": concat("; ", violations),
    "violations": violations
  }
}
