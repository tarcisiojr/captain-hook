import pymongo
from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        self.db.domain_schema.create_index(
            [("name", pymongo.ASCENDING)],
            name="idx_name",
            unique=True
        )

        self.db.domain.create_index(
            [
                ('schema_name', pymongo.ASCENDING),
                ('domain_id', pymongo.ASCENDING)
            ],
            name="idx_schema_and_id",
            unique=True,
        )

    def downgrade(self):
        pass
