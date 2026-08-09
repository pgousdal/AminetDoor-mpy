# Security

AminetDoor performs outbound HTTPS read-only requests to Aminet (RSS feed
and `.readme` file downloads). It does not require credentials or an API
key, and it does not provide any Aminet write or upload operations.

Network responses are untrusted input. Requests use a finite timeout,
response size is capped, and expected network/feed failures are reported
without exposing tracebacks to the BBS session.

Please report suspected vulnerabilities privately when possible. This
repository has no dedicated private security contact; use a GitHub Security
Advisory if that mechanism is available. Use regular GitHub issues for
non-sensitive bugs. Include the AminetDoor version, Mystic version, Python
version, reproduction steps, and relevant logs, omitting sensitive BBS or
user information.
