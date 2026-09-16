"""Separate Solver HTTP ports from per-GPU vLLM internal port blocks."""

import argparse
import socket
from contextlib import ExitStack

STRIDE = 256


def port_plan(gpu_ids, http_base, internal_base=12000):
    if not gpu_ids or any(not gpu.isdigit() for gpu in gpu_ids):
        raise ValueError("Solver port isolation requires numeric VLLM_GPU_IDS")
    ids = [int(gpu) for gpu in gpu_ids]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate Solver GPU IDs")
    http_ports = set(range(http_base, http_base + len(ids)))
    if min(http_ports) < 1024 or max(http_ports) > 65535:
        raise ValueError("Invalid Solver HTTP ports")
    result = []
    for index, gpu in enumerate(ids):
        start = internal_base + STRIDE * gpu
        block = range(start, start + STRIDE)
        if start < 1024 or block.stop > 65536 or http_ports.intersection(block):
            raise ValueError("Invalid/overlapping Solver internal and HTTP ports")
        result.append((http_base + index, start, start + STRIDE // 2))
    return result


def check_available(plan):
    # Check the entire block before launching *any* service. Never kill an owner
    # or let an already occupied block silently spill into the next GPU's block.
    # Like vLLM's own get_open_port(), this is not an OS-level reservation after
    # the sockets close; use a dedicated node/range to exclude unrelated jobs.
    for http, start, _ in plan:
        with ExitStack() as stack:
            for port in [http, *range(start, start + STRIDE)]:
                sock = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                try:
                    sock.bind(("", port))
                except OSError as error:
                    raise RuntimeError(f"Solver port {port} unavailable; refusing launch") from error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu-ids", required=True)
    parser.add_argument("--http-base", type=int, required=True)
    parser.add_argument("--internal-base", type=int, default=12000)
    args = parser.parse_args()
    plan = port_plan([gpu.strip() for gpu in args.gpu_ids.split(",")],
                     args.http_base, args.internal_base)
    check_available(plan)
    for ports in plan:
        print(*ports)


if __name__ == "__main__":
    main()
