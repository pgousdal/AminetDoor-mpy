# Installation

## 1. Verify Mystic Python 3

Mystic BBS must be configured with Python 3 support.

A Mystic Python script normally imports:

```python
import mystic_bbs as bbs
```

## 2. Install AminetDoor

Copy `aminetdoor.mpy` into either:

- the active theme's script directory, or
- Mystic's default script directory.

## 3. Add the menu entry

In the Mystic menu editor add a command using:

```text
Command: GZ
Data:    aminetdoor
```

Mystic's `GZ` menu command executes a Python 3 script. When no extension is
given Mystic resolves the script as `aminetdoor.mpy`.

## 4. Test

Call the BBS with an ANSI-capable client at 80x25 or larger and launch
AminetDoor.

Try:

```text
[R] Recent uploads
```

Then use Recent, Browse, or Search to select a package with Up/Down and Enter,
and page through its README.
The default result selector is the lightbar. For numbered compatibility mode,
set `RESULT_SELECTOR = "numbered"` near the top of `aminetdoor.mpy`. Both modes
retain the 80x25 baseline layout; lightbar arrows use Mystic-native extended
key handling.

Browse follows the public Aminet category tree. Search sends a bounded query to
Aminet's public search form; neither mode requires credentials or writes to
Aminet.

## Troubleshooting

### `mystic_bbs` cannot be imported

Confirm Mystic's embedded Python 3 configuration and that the Python bitness
matches Mystic.

### Could not reach Aminet

Check DNS, HTTPS connectivity, firewall policy and outbound TCP/443 from the
Mystic host.

### Aminet request timed out

M0 uses a 10-second timeout so a remote caller is not left hanging
indefinitely.

### Aminet returned an unreadable feed

Aminet's RSS feed occasionally has brief downtime windows (see Aminet's own
status notices). Retry after a few minutes; this is reported as a friendly
error rather than a traceback.

Automated/offline validation: complete. Live Mystic validation: pending.
