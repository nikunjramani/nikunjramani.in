# Schema Versioning

Every schema declares `"x-version": "MAJOR.MINOR.PATCH"`.

## The policy

| Change | Bump | Migration needed |
|---|---|---|
| New **optional** field | minor | No |
| New enum value | minor | No |
| Relaxed constraint (longer maxLength, wider range) | minor | No |
| Description or documentation only | patch | No |
| **New required field** | **major** | Yes |
| Rename a field | **major** | Yes |
| Change a field's type | **major** | Yes |
| Remove a field | **major** | Yes |
| Remove an enum value | **major** | Yes |
| Tightened constraint (shorter maxLength) | **major** | Yes — existing data may violate it |

Most changes are additive, which is the point of a model that is mostly optional fields
([ADR 0008](../docs/adr/0008-projects-drop-start-end-dates.md)).

## Breaking changes

1. Bump the major version in the schema
2. Write `backend/migrations/NNN_short_description.py`
3. Make it **idempotent** — it will get run twice by someone, eventually
4. Log the result to `audit_log`
5. Run it against the emulator with realistic data before production
6. Deploy the migration **before** the code that depends on it

## Tightening is the sneaky one

Reducing a `maxLength` or narrowing an enum looks additive but is not: existing documents
may already violate the new constraint. They will keep reading fine — Firestore does not
validate on read — and then fail the next time someone saves them through the admin panel,
which is a confusing way to find out.

Either migrate the data or leave the constraint alone.

## Removing an enum value

Never just delete it. Existing documents still hold the old value, and they will fail
validation on next write. Migrate them to a new value first, then remove it in a separate
change.
