# Security

AminetDoor performs outbound HTTPS read-only requests to Aminet (RSS feed
and `.readme` file downloads). It does not require credentials or an API
key, and it does not provide any Aminet write or upload operations.

Network responses are untrusted input. Requests use a finite timeout,
response size is capped, and expected network/feed failures are reported
without exposing tracebacks to the BBS session.

Favorites are local per-user JSON data under the configured user-data
directory. They contain package metadata only, never README bodies or
executable content, are not sent to Aminet, and use hashed user-ID filenames.
Favorites storage failures are handled as an unavailable optional feature and
must not prevent core Browse, Search, Recent, or README functionality.

Please report suspected vulnerabilities privately when possible. This
repository has no dedicated private security contact; use a GitHub Security
Advisory if that mechanism is available. Use regular GitHub issues for
non-sensitive bugs. Include the AminetDoor version, Mystic version, Python
version, reproduction steps, and relevant logs, omitting sensitive BBS or
user information.
