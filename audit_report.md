# SwiftDeploy Audit Report

Generated: 2026-05-06T21:16:45Z

## Timeline

| Time | Event | Detail |
| --- | --- | --- |
| 2026-05-06T21:05:41Z | mode changed | canary |
| 2026-05-06T21:05:41Z | chaos changed | none |
| 2026-05-06T21:16:27Z | chaos changed | slow |

## Policy Violations

| Time | Domain | Reason |
| --- | --- | --- |
| 2026-05-06T21:05:41Z | infrastructure | CPU load 9.86 is above allowed 2.00 |
| 2026-05-06T21:16:27Z | infrastructure | CPU load 9.25 is above allowed 2.00 |
| 2026-05-06T21:16:27Z | canary | p99 latency 2500ms is above allowed 500ms |
