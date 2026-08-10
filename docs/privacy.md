# Privacy

Elite CV defaults to local processing and no telemetry. The public sample uses
fictional data and must not be populated with personal material before it is
copied into a private workspace.

## Local-only paths

These paths are ignored by default:

```text
sources/private/**
workspace/**
dist/**
```

`elitecv init` records `track_structured_profile: false` and
`remote_artifacts: false` in `workspace/policy.yml`. Enabling either behavior
requires an explicit command-line opt-in.

Ignored does not mean encrypted or inaccessible. Protect the machine, backups,
remote repository, and agent environment separately.

On POSIX systems, `init` creates its local workspace directories with owner-only
permissions and applies the same restriction to generated structured files. It
cannot change permissions of source files supplied independently by the user,
and platform-specific backup or sync tools may still copy local data.

## Hosted agents

If a coding agent is hosted, source documents may be transmitted to that
provider. Read its retention, training, access, and deletion terms. Do not send
confidential sources unless the profile owner explicitly accepts that risk.

## Share boundary

`share/` contains files eligible for human review as shareable artifacts. It is
not an automatic publication action. Private evidence reports, manifests, raw
sources, and generated build internals stay outside the share bundle by
default. In v0.1, `private` and `restricted` claims cannot enter `share/` or a
release bundle.

The safety scan is a guardrail. It cannot detect every personal or confidential
value and does not replace a complete history and artifact review.
