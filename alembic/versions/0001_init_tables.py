"""init tables: users, vehicles, search_results, products, favorites, cart_items, orders, order_items, addresses, support"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic
revision = "0001_init_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- USERS ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("is_phantom", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- VEHICLES ---
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("vin", sa.String(64), index=True),
        sa.Column("brand", sa.String(128)),
        sa.Column("model", sa.String(128)),
        sa.Column("engine", sa.String(128)),
        sa.Column("kba_code", sa.String(64)),
    )

    # --- SEARCH_RESULTS ---
    op.create_table(
        "search_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("vehicle_id", sa.Integer, sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("raw_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- PRODUCTS ---
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("search_id", sa.Integer, sa.ForeignKey("search_results.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(512)),
        sa.Column("brand", sa.String(128)),
        sa.Column("price", sa.String(64)),
        sa.Column("image_url", sa.String(512)),
        sa.Column("product_url", sa.String(512)),
        sa.Column("delivery_time", sa.String(128)),
        sa.Column("description", sa.Text),
    )

    # --- FAVORITES ---
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE")),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_product_fav"),
    )

    # --- CART_ITEMS ---
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="CASCADE")),
        sa.Column("quantity", sa.Integer, default=1),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_product_cart"),
    )

    # --- ORDERS ---
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("total_price", sa.Numeric(10, 2)),
        sa.Column("status", sa.String(64), default="created"),
        sa.Column("payment_method", sa.String(64)),
        sa.Column("address", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- ORDER_ITEMS ---
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.id", ondelete="CASCADE")),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("quantity", sa.Integer, default=1),
        sa.Column("price_snapshot", sa.String(64)),  # сохраняем цену на момент покупки
    )

    # --- ADDRESSES (optional) ---
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("city", sa.String(128)),
        sa.Column("street", sa.String(128)),
        sa.Column("postal_code", sa.String(32)),
        sa.Column("country", sa.String(64), default="Germany"),
    )

    # --- SUPPORT (чат поддержки) ---
    op.create_table(
        "support",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_from_user", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("support")
    op.drop_table("addresses")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("favorites")
    op.drop_table("products")
    op.drop_table("search_results")
    op.drop_table("vehicles")
    op.drop_table("users")
