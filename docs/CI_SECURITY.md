# CI security controls

Execution errors are fatal. Bandit preserves JSON; findings are reported separately
from tool failures. Scorecard resolves result and rule-default levels and gates on
SARIF errors. TruffleHog scans history without verifying keys against providers;
findings require review/rotation, not an ignored exit code.

CodeQL runs on public repos, or on private repos only when ENABLE_PRIVATE_CODEQL=true
and the account has the required code scanning entitlement. A skipped private job
is documented in the run summary; Bandit and regression tests still run.

Source archive provenance signs/verifies a real source.tar.gz on public manual/release
runs. It does not certify compiled binaries. Private source is not sent to a public
transparency log. The exact SLSA v2.1.0 tag exception is recorded in .pinact.yaml;
other Actions remain pinned to immutable SHAs.

Raw scanner results remain in runner temporary storage and are not uploaded.
A removed literal can still trigger history scanning; revocation/rotation and
historical remediation require separate evidence. A red scan is not ignored.
