# Privacy

Elite CV Builder by joaq defaults to local processing and no telemetry. The
software does not operate an account service, collect CV content, or upload
artifacts to joaq.mx. The public sample uses fictional data and must not be
populated with personal material before it is copied into a private workspace.

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

Build and local release output directories also use owner-only permissions on
POSIX systems. A share bundle is still local until its owner deliberately copies
or publishes it elsewhere.

## Hosted agents

The default agent workflow is local/manual. Before a hosted coding agent reads
any raw source document, it must tell the profile owner that the provider may
process the material and obtain explicit permission. Do not send confidential
sources unless the profile owner explicitly accepts that risk. Read the
provider's retention, training, access, and deletion terms separately.

Installing the skill or plugin does not create a second data recipient. If a
user pastes or uploads material into ChatGPT, Claude, or another hosted agent,
that material is governed by that provider's policy.

## Share boundary

`share/` contains files eligible for human review as shareable artifacts. It is
not an automatic publication action. Private evidence reports, manifests, raw
sources, and generated build internals stay outside the share bundle by
default. In v0.1, `private` and `restricted` claims cannot enter `share/` or a
release bundle.

The safety scan is a guardrail. It cannot detect every personal or confidential
value and does not replace a complete history and artifact review.
