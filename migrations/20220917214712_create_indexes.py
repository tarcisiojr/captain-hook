import pymongo
from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        self.db.domain_event.create_index(
            [("schema_name", pymongo.ASCENDING)],
            name="idx_schema"
        )
        self.db.domain_event.create_index(
            [("schema_name", pymongo.ASCENDING),
             ("hook.queue_name", pymongo.ASCENDING)],
            name="idx_schema_queue"
        )

    def downgrade(self):
        pass
