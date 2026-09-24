"""Shared SQL used by the created_by/updated_by/deleted_by CharField -> ForeignKey migrations.

Nulls out any audit value that isn't a real, existing user id before the ForeignKey
constraint (and the narrower varchar(20) column) is applied, so the migration doesn't
fail on stale/malformed data.
"""

AUDIT_FK_FIELDS = ("created_by", "updated_by", "deleted_by")

# Matches common.push_id.PushID.PUSH_CHARS, the only characters a real user id can contain.
PUSH_ID_PATTERN = r"^[-0-9A-Za-z_]{20}$"


def audit_fk_cleanup_sql(*table_names, fields=AUDIT_FK_FIELDS, user_table="accounts_user"):
    """Build the RunSQL body that cleans up `fields` on each of `table_names`."""
    statements = [
        f"""
        UPDATE {table_name}
        SET {field} = NULL
        WHERE {field} IS NOT NULL
          AND ({field} = ''
               OR {field} !~ '{PUSH_ID_PATTERN}'
               OR {field} NOT IN (SELECT id FROM {user_table}));
        """
        for table_name in table_names
        for field in fields
    ]
    return "\n".join(statements)
