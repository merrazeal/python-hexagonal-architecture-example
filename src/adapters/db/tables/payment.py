import sqlalchemy as sa

from src.adapters.db import metadata

payment_table = sa.Table(
    "payments",
    metadata,
    sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
    sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column("currency", sa.String(3), nullable=False),
    sa.Column("description", sa.Text, nullable=False),
    sa.Column("metadata", sa.JSON, nullable=False),
    sa.Column("status", sa.String(20), nullable=False),
    sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
    sa.Column("webhook_url", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("failure_reason", sa.Text, nullable=True),
)

payment_outbox_table = sa.Table(
    "payment_outbox",
    metadata,
    sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
    sa.Column(
        "payment_id",
        sa.UUID(as_uuid=True),
        sa.ForeignKey("payments.id"),
        nullable=False,
        index=True,
    ),
    sa.Column("status", sa.String(20), nullable=False, index=True),
    sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column("currency", sa.String(3), nullable=False),
    sa.Column("webhook_url", sa.Text, nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, index=True),
)
