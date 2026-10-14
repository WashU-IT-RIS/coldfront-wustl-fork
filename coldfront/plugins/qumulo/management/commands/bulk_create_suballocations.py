import runpy

from django.core.management.base import BaseCommand


class Command(BaseCommand):
	help = "Run the batch Qumulo suballocation creation script."

	def add_arguments(self, parser):
		parser.add_argument(
			"--class-washu-keys",
			dest="class_washu_keys",
			type=str,
			required=True,
			help="Path to a CSV file containing WashU keys.",
		)
		parser.add_argument(
			"--allocation-attributes",
			dest="allocation_attributes",
			type=str,
			required=True,
			help="Path to a JSON file containing a list of allocation attribute objects.",
		)

	def handle(self, *args, **options):
		runpy.run_module(
			"coldfront.plugins.qumulo.services.batch_create_sub_allocations",
			run_name="__main__",
			init_globals={
				"class_washu_keys": options["class_washu_keys"],
				"allocation_attributes": options["allocation_attributes"],
			},
		)
