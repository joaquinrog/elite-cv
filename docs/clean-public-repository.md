# Clean Public Repository Procedure

Do not publish the private CV repository by deleting personal files from its
history. Create the public repository from this extraction with a new history.

1. Create the candidate directory outside the private workspace; never publish
   this parent repository or initialize the public history inside it.
2. Copy only the allowlisted extraction, excluding caches, build products, and
   any root-level local workspace paths.
3. Run `python -m elitecv check-public`, the test suite, both synthetic builds,
   PDF text extraction, and visual review.
4. Inspect generated reports, manifests, PDF metadata, workflows, dependencies,
   license notices, and the exact artifact-upload path for private values.
5. Initialize a new Git repository, inspect every file in its first commit, and
   run a full-history secret scan before adding a remote.
6. Configure the public remote only after the history audit passes, then rerun
   the same checks from a fresh clone.
7. Keep the personal workspace private and separate from the public repository.

The public workflow uploads synthetic artifacts only. A user's personal
workflow must not upload artifacts unless the user explicitly configures and
reviews that behavior.
