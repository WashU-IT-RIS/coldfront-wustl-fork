TERABYTE_IN_BYTES = 1024**4


def bytes_to_terabytes(value_in_bytes: int) -> float:
    return value_in_bytes / TERABYTE_IN_BYTES

def terabytes_to_bytes(value_in_terabytes: float) -> int:
    return int(value_in_terabytes * TERABYTE_IN_BYTES)
