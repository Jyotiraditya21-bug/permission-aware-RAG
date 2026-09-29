Task 1 complete: declared Python >=3.12 and approved pydantic>=2,<3; added typed request, access, source, chunk, version, retrieval, answer, and settings contracts.
Validation: all 15 unittest tests pass on Python 3.12.5 with Pydantic 2.13.4; tuning values remain explicit, with no provider or release-threshold defaults.
Next: Task 2, trusted identity and query-time ACL scope; contract validation alone does not authorize retrieval or verify evidence support.
Task 1 verified: contracts retained; environment-backed settings and Python 3.12 pytest tooling added; 15 tests pass.
ASSUMPTION: isolated uv workspace avoids unrelated parent projects; runtime providers will offer a deterministic offline baseline and optional HTTP models.
Next: trusted identity and ACL scope.
Task 2 complete: trusted credentials, epoch replacement/revocation, tenant/grant/attribute predicates; 17 tests pass.
ASSUMPTION: explicit empty policy maps impose no attributes; a declared attribute without matching trusted values denies access. Credentials are provisioned out of band.
Next: source normalization.
Task 3 complete: validated docs/tickets/wikis batches, source boundaries, change tokens, deletion and snapshot signals; 19 tests pass.
ASSUMPTION: connectors supply normalized JSON exports; content hashes are recomputed rather than trusting modification timestamps.
Next: incremental state and chunking.
Task 4 complete: stable chunk IDs, recomputed hashes, no-op retries, ACL-only embedding reuse, deletion and vector validation; 22 tests pass.
ASSUMPTION: word-bounded deterministic chunks and content hashes are the conservative baseline; modification tokens never bypass hashing.
Next: filtered indexes and atomic durable publication.
