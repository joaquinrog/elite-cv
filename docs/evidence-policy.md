# Evidence Policy

`source-supported` means that a statement appears in a recorded source. It does
not mean an independent authority proved it true.

## Release treatment

| State | Draft workspace | Release output |
| --- | --- | --- |
| `sourced` | visible | allowed when approved and disclosed |
| `self_attested` | visible | allowed when approved and disclosed |
| `externally_verified` | visible | allowed when approved and disclosed |
| `unsupported` | visible with a question | blocked |
| `conflicted` | visible with a question | blocked |

`pending` and `rejected` review states are blocked. In v0.1, `private` and
`restricted` claims are never rendered by a strict build or copied into a share
bundle. A future private-variant feature requires a separate, audited output
boundary; it is not implemented by changing `allowed_disclosures`.

Open questions are synchronized to `workspace/review/open-questions.md`.
Deleting a question without resolving or rejecting its claim is not a valid
resolution.
