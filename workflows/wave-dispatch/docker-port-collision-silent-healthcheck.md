---
title: "Docker port collisions fail silently into the wrong container's health check"
type: "hazard"
category: "wave-dispatch"
---

When each rail spins up its own throwaway Postgres on an assigned port, `docker run -d --name X -p PORT:5432 ...` can fail because the port is already bound by a sibling rail's container — but a naive polling loop (`for i in ...; do docker exec $NAME pg_isready ...; done`) doesn't check `docker run`'s own exit code. It just polls whatever is already listening on that port, succeeds immediately, and the rail proceeds to run migrations/tests against a database it doesn't own.

**Confirmed live:** a rail's migration + 17 tests ran against a sibling's database before the mismatch was noticed on an unrelated sanity check. Damage was limited only by luck (uniquely-namespaced test rows).

**Rule:** the container-creation step must check its own success explicitly — `docker run -d --name X -p PORT:5432 ... || exit 1` followed by `docker ps --filter name=X` actually showing *your* container — before polling readiness. Never just chain `docker run; poll pg_isready` and trust it.

Same class of hazard as shared-stash and PID-kill collisions: a shared-resource-namespace collision that silent success can fully mask.
