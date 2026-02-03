import os

from constants import STORAGE_2_PREFIX, STORAGE_3_PREFIX
import argparse


class ArgumentParser:

    def __init__(self):
        self.perform_reset = False
        self.allocation_name = ""
        self.allocation_root = ""
        self.num_walkers = 0
        self.num_workers_per_walk = 0
        self.target_dir = ""
        self.sub_allocations = []
        self.log_dir = ""
        self.storage_suffix = ""
        self.access_mode = ""

    def get_perform_reset(self):
        return self.perform_reset

    def get_access_mode(self):
        return self.access_mode

    def get_allocation_name(self):
        return self.allocation_name

    def get_allocation_root(self):
        return self.allocation_root

    def get_num_walkers(self):
        return self.num_walkers

    def get_num_workers_per_walk(self):
        return self.num_workers_per_walk

    def get_target_dir(self):
        return self.target_dir

    def get_sub_allocations(self):
        return self.sub_allocations

    def get_storage_suffix(self):
        return self.storage_suffix

    def get_log_dir(self):
        return self.log_dir

    def retrieve_args(self):

        parser = argparse.ArgumentParser(
            description="Parse arguments for the ArgumentParser class."
        )

        parser.add_argument(
            "--perform_reset",
            type=str,
            required=True,
            choices=["y", "n"],
            help="Specify whether to perform reset ('y' or 'n').",
        )
        parser.add_argument(
            "--allocation_root",
            type=str,
            required=True,
            help=f"Specify the allocation root path. Must start with '{STORAGE_2_PREFIX}' or '{STORAGE_3_PREFIX}'.",
        )
        parser.add_argument(
            "--target_dir",
            type=str,
            required=True,
            help="Specify the target directory. Must exist and be within the allocation root.",
        )
        parser.add_argument(
            "--sub_allocations",
            type=str,
            default="",
            help="Comma-separated list of sub-allocation names. Optional.",
        )
        parser.add_argument(
            "--num_walkers",
            type=int,
            required=True,
            help="Specify the number of walkers. Must be a positive integer.",
        )
        parser.add_argument(
            "--num_workers_per_walk",
            type=int,
            required=True,
            help="Specify the number of workers per walk. Must be a positive integer.",
        )
        parser.add_argument(
            "--log_dir",
            type=str,
            required=True,
            help="Specify the log directory. Can be absolute or relative.",
        )
        parser.add_argument(
            "--storage_suffix",
            type=str,
            default="",
            help="Suffix for storage in groupname. Ex: groupname = 'storage2_foo_rw' => --storage_suffix=2",
        )
        parser.add_argument(
            "--access_mode",
            type=str,
            required=False,
            default="standard-access",
            choices=["standard-access", "admin-access"],
            help="Specify the access mode ('standard-access' or 'admin-access'). Default is 'standard-access'.",
        )

        args = parser.parse_args()

        self.perform_reset = args.perform_reset.lower() == "y"

        def validate_allocation_root(value):
            if not (
                value.startswith(STORAGE_2_PREFIX) or value.startswith(STORAGE_3_PREFIX)
            ):
                raise ValueError(
                    f"Root path must look like '{STORAGE_2_PREFIX}<ROOT>' or '{STORAGE_3_PREFIX}<ROOT>'."
                )
            allocation_root_name = (
                value.replace(STORAGE_2_PREFIX, "").strip("/")
                if value.startswith(STORAGE_2_PREFIX)
                else value.replace(STORAGE_3_PREFIX, "").strip("/")
            )
            if "/" in allocation_root_name:
                raise ValueError(
                    f"Root path must look like '{STORAGE_2_PREFIX}<ROOT>' or '{STORAGE_3_PREFIX}<ROOT>'."
                )
            if not (os.path.exists(value) and os.path.isdir(value)):
                raise ValueError(f"Root path does not exist: {value}")
            return value

        self.allocation_root = validate_allocation_root(args.allocation_root)
        self.allocation_name = (
            self.allocation_root.replace(STORAGE_2_PREFIX, "").strip("/")
            if self.allocation_root.startswith(STORAGE_2_PREFIX)
            else self.allocation_root.replace(STORAGE_3_PREFIX, "").strip("/")
        )

        if not (
            os.path.exists(args.target_dir)
            and os.path.isdir(args.target_dir)
            and args.target_dir.startswith(self.allocation_root)
        ):
            raise ValueError("Invalid target directory.")
        self.target_dir = args.target_dir

        def validate_sub_allocation_names(value, allocation_root):
            if value == "":
                return []
            sub_alloc_names = value.split(",")
            sub_alloc_paths = [
                os.path.join(f"{allocation_root}/Active/", name.strip())
                for name in sub_alloc_names
            ]
            if not all(
                os.path.exists(path) and os.path.isdir(path) for path in sub_alloc_paths
            ):
                raise ValueError("Invalid sub-allocation names.")
            return sub_alloc_names

        self.sub_allocations = validate_sub_allocation_names(
            args.sub_allocations, self.allocation_root
        )

        if args.num_walkers <= 0:
            raise ValueError("Number of walkers must be a positive integer.")
        self.num_walkers = args.num_walkers

        if args.num_workers_per_walk <= 0:
            raise ValueError("Number of workers per walk must be a positive integer.")
        self.num_workers_per_walk = args.num_workers_per_walk

        candidate_dir = args.log_dir
        if not os.path.isabs(candidate_dir):
            candidate_dir = os.path.join(os.getcwd(), args.log_dir)
        if not os.path.exists(candidate_dir):
            os.makedirs(candidate_dir)
        self.log_dir = candidate_dir
        self.storage_suffix = args.storage_suffix

        if os.listdir(self.log_dir):
            raise ValueError(f"Log directory is not empty: {self.log_dir}")
