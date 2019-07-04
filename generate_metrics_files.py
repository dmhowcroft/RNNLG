from argparse import ArgumentParser
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

import json

argument_parser = ArgumentParser(description=__doc__)
argument_parser.add_argument("rnnlg_logfile", type=str,
                             help="log from running RNNLG in -mode test")
argument_parser.add_argument("test_refs", type=str,
                             help="file containing the references for the testset")
argument_parser.add_argument("output_prefix", type=str, default="./tmp",
                             help="filepath prefix for output")


def parse_mr_best_rlzn(log: str) -> List[Tuple[str, str]]:
    lines = log.split("\n")
    mr_rlzn_list = []
    for index, line in enumerate(lines):
        if line.startswith("inform("):
            mr_rlzn_list.append((line, lines[index + 2].split("\t")[3]))
    return mr_rlzn_list


def group_by_mr(list_of_pairs) -> Dict[str, Set[str]]:
    grouped = defaultdict(set)
    for mr, text in list_of_pairs:
        grouped[mr].add(text)
    return grouped


if __name__ == '__main__':
    args = argument_parser.parse_args()

    with open(args.rnnlg_logfile, 'r') as logfile:
        data = logfile.read()

    data = parse_mr_best_rlzn(data)

    with open(args.test_refs, 'r') as reffile:
        for _ in range(0, 5):
            next(reffile)
        refs = json.load(reffile)

    print(len(data))
    print(data[:3])
    rlzns_by_mr = group_by_mr(data)
    print(len(rlzns_by_mr))
    print(Counter([len(rlzns_by_mr[key]) for key in rlzns_by_mr]))

    print(len(refs))
    print(refs[:3])
    refs_by_mr = group_by_mr([(x, y) for x, y, _ in refs])
    print(len(refs_by_mr))
    print(Counter([len(refs_by_mr[key]) for key in refs_by_mr]))

    with open(f"{args.output_prefix}.rlzns.metrics", 'w') as rlzn_metrics_file:
        with open(f"{args.output_prefix}.ref.metrics", 'w') as ref_metrics_file:
            with open(f"{args.output_prefix}.mr.metrics", 'w') as mr_metrics_file:
                for mr in rlzns_by_mr:
                    if mr in refs_by_mr:
                        mr_metrics_file.write(mr + "\n")
                        rlzn_metrics_file.write(rlzns_by_mr[mr].pop() + "\n")
                        for ref in refs_by_mr[mr]:
                            ref_metrics_file.write(ref + "\n")
                        ref_metrics_file.write('\n')
                    else:
                        print(mr)
