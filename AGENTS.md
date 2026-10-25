# AGENTS.md

Instructions for an AI agent helping to extend this server.

- Read `docs/protocol.md` first, then `docs/code-map.md`. The research method is in `docs/research.md`.
- Work in small loops. The human plays the game against `server/server.py`; you read `server/requests.jsonl` for
  `unhandled` endpoints and decrypted FLS messages, find the reply parser in the EBOOT (Ghidra via GhidraMCP; search the
  service name or attribute names), implement the reply in `ROUTES`, test it with curl or a simulated client, and ask the
  human to retest.
- Reply rules that will bite you: Content-Type exactly `application/xml;charset=utf-8`; the `<result><status><id>0…`
  envelope; data as XML attributes.
- Scope is Game Rooms 1v1. Don't build Diamond Dynasty, Franchise or other endpoints unless asked.
- Never commit game files, Sony data (`services.xml`, WAD contents, the EBOOT), captures, `server/certs/`, or logs.
- Communication with RPCS3 maintainers (issues, PRs) must come from the human, not an agent.
