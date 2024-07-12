from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run one or more migrations for the Qumulo plugin.\nUsage: coldfront run_migration <migration_name1> <migration_name2> ... <migration_nameN>"

    def add_arguments(self, parser):
        parser.add_argument("migrations", nargs="+")

    def handle(self, *args, **options):
        migration = __import__(
            f"coldfront_plugin_qumulo.management.migrations",
            fromlist=options["migrations"],
        )

        for arg in options["migrations"]:
            try:
                attribute = getattr(migration, arg)
                attribute.run()
            except AttributeError:
                print(f"Could not find migration {arg}")
