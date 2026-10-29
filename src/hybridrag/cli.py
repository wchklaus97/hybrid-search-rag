"""hrag index build <folder>... | search "<q>" [--mode all] | eval | replay | agent-eval | index reset"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

from .config import load_config
from .embed import HashEmbedder, get_embedder
from .index import build_index
from .rerank import get_reranker
from .retrieve import MODES, Retriever
from .store import Store, reset_db

CORPORA = {
    "base": ["examples/harbour-lane"],  # the same 4 documents as repos 1 and 3
    "full": ["examples/harbour-lane", "examples/distractors"],  # + 6 look-alike documents
}


def _embedder(name: str, model: str = ""):
    emb = get_embedder(name, model)
    if name == "local" and isinstance(emb, HashEmbedder):
        raise RuntimeError("embedder 'local' needs sentence-transformers: pip install -e '.[local]'")
    return emb


def _modes(reranker) -> list[str]:
    return [m for m in MODES if reranker or not m.endswith("+rerank")]


def _temp_retriever(tmp: str, folders, cfg, embedder, reranker) -> Retriever:
    store = Store(Path(tmp) / "eval.db", embedder.name, embedder.dim)
    build_index(folders, cfg, embedder, store)
    return Retriever(store, embedder, reranker, cfg.pool)


# --- commands -----------------------------------------------------------------
def cmd_index_build(args, cfg) -> int:
    emb = get_embedder(cfg.embed_provider, cfg.embed_model)
    store = Store(cfg.db_path, emb.name, emb.dim)
    n = build_index(args.folders, cfg, emb, store, log=print)
    print(f"Done: {n} chunks added, {store.count()} total in {cfg.db_path}")
    return 0


def cmd_index_reset(_args, cfg) -> int:
    print(f"Deleted {cfg.db_path}" if reset_db(cfg.db_path) else "Nothing to delete")
    return 0


def cmd_search(args, cfg) -> int:
    emb = get_embedder(cfg.embed_provider, cfg.embed_model)
    store = Store(cfg.db_path, emb.name, emb.dim)
    if store.count() == 0:
        print("Index is empty. Run `hrag index build examples/harbour-lane` first.")
        return 1
    reranker = get_reranker(cfg.reranker, cfg.reranker_model)
    retriever = Retriever(store, emb, reranker, cfg.pool)
    modes = _modes(reranker) if args.mode == "all" else [args.mode]
    for mode in modes:
        print(f"== {mode}")
        for n, h in enumerate(retriever.search(args.question, args.k or cfg.top_k, mode, args.dept, args.entity), 1):
            why = "  ".join(f"{stage} #{rank} {score:.3f}" for stage, (rank, score) in h.stages.items())
            print(f"[{n}] {h.source} (chunk {h.chunk_index})   {why}")
            print(f"    {' '.join(h.text.split())[:150]}")
        print()
    return 0


def cmd_eval(args, cfg) -> int:
    from .evaluate import evaluate_mode, load_qa, results_table

    cfg = replace(cfg, pool=args.pool or cfg.pool)
    qa = load_qa(args.qa)
    reranker = get_reranker(cfg.reranker, cfg.reranker_model)
    results = []
    for corpus in args.corpus.split(","):
        for name in args.embed.split(","):
            emb = _embedder(name.strip())
            for size in [int(s) for s in args.sizes.split(",")]:
                run_cfg = replace(cfg, chunk_size=size, chunk_overlap=int(size * 0.15))
                with tempfile.TemporaryDirectory() as tmp:
                    retriever = _temp_retriever(tmp, CORPORA[corpus], run_cfg, emb, reranker)
                    n_chunks = retriever.store.count()
                    for mode in _modes(reranker):
                        label = f"{corpus} ({n_chunks} chunks) · {name.strip()} · {size} · pool {cfg.pool} · **{mode}**"
                        r = evaluate_mode(retriever, qa, mode, args.k, label)
                        print(f"  {label:<70} hit@{args.k}={r.hitk:.2f}  MRR={r.mrr:.2f}")
                        results.append(r)
                    retriever.store.close()
    table = results_table(results, args.k, len(qa))
    print("\n" + table)
    if args.show_misses:
        for r in results:
            print(f"misses [{r.label}]: {', '.join(r.misses) or '-'}")
    if args.out:
        Path(args.out).write_text(table, encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


def cmd_replay(args, cfg) -> int:
    from .evaluate import load_replay, replay_mode, replay_table

    cfg = replace(cfg, pool=args.pool or cfg.pool)
    items = load_replay(args.replay)
    reranker = get_reranker(cfg.reranker, cfg.reranker_model)
    emb = _embedder(args.embed)
    run_cfg = replace(cfg, chunk_size=args.chunk_size, chunk_overlap=int(args.chunk_size * 0.15))
    with tempfile.TemporaryDirectory() as tmp:
        retriever = _temp_retriever(tmp, CORPORA[args.corpus], run_cfg, emb, reranker)
        results = [replay_mode(retriever, items, mode, args.k) for mode in _modes(reranker)]
        n_chunks = retriever.store.count()
        retriever.store.close()
    header = (f"corpus `{args.corpus}` ({n_chunks} chunks), embedder `{emb.name}`, "
              f"chunk {run_cfg.chunk_size}/{run_cfg.chunk_overlap}, candidate pool {cfg.pool} per retriever")
    table = header + "\n\n" + replay_table(results, items, args.k)
    print(table)
    if args.out:
        Path(args.out).write_text(table, encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


def cmd_agent_eval(args, cfg) -> int:
    try:
        from agentrag.agent import Deps, build_agent
        from agentrag.evaluate import load_qa, run_case, summarize, to_markdown
    except ImportError:
        print("error: needs repo 3's agent - pip install -e '.[agent]'", file=sys.stderr)
        return 2
    import json

    from .agent_bridge import HybridSearcher

    cfg = replace(cfg, pool=args.pool or cfg.pool)
    qa = load_qa(args.qa)
    reranker = get_reranker(cfg.reranker, cfg.reranker_model)
    emb = _embedder(args.embed)
    run_cfg = replace(cfg, chunk_size=args.chunk_size, chunk_overlap=int(args.chunk_size * 0.15))
    model = args.model or "openai:openai/gpt-4o-mini"
    summaries = []
    dump = open(args.dump, "a", encoding="utf-8") if args.dump else None
    with tempfile.TemporaryDirectory() as tmp:
        retriever = _temp_retriever(tmp, CORPORA[args.corpus], run_cfg, emb, reranker)
        for mode in args.modes.split(","):
            agent, deps = build_agent(model), Deps(HybridSearcher(retriever, mode))
            label = f"{model} · {emb.name} · {args.corpus} · chunk {run_cfg.chunk_size} · pool {cfg.pool} · **{mode}**"
            cases = []
            for item in qa:
                case = run_case(agent, deps, item)
                cases.append(case)
                mark = "PASS" if case.passed else "FAIL " + (case.error or ",".join(k for k, v in case.checks.items() if not v))
                print(f"  [{mode}] {item.id:<18} {mark}")
                if dump:
                    dump.write(json.dumps({"run": label, "id": item.id, "tools": case.tool_calls, "tool_args": case.tool_args,
                                           "checks": case.checks, "error": case.error, "output": case.output},
                                          ensure_ascii=False) + "\n")
            summaries.append(summarize(label, cases))
        retriever.store.close()
    if dump:
        dump.close()
    table = to_markdown(summaries)
    print("\n" + table)
    if args.out:
        Path(args.out).write_text(table, encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    p = argparse.ArgumentParser(prog="hrag", description=__doc__)
    p.add_argument("--config")
    top = p.add_subparsers(dest="group", required=True)

    idx = top.add_parser("index", help="build or reset the index").add_subparsers(dest="cmd", required=True)
    s = idx.add_parser("build", help="ingest -> chunk -> embed -> SQLite (vectors + FTS5)")
    s.add_argument("folders", nargs="+")
    s.set_defaults(fn=cmd_index_build)
    idx.add_parser("reset").set_defaults(fn=cmd_index_reset)

    s = top.add_parser("search", help="search and show WHY each chunk ranked where it did")
    s.add_argument("question")
    s.add_argument("--mode", default="all", choices=("all", *MODES))
    s.add_argument("-k", type=int)
    s.add_argument("--dept")
    s.add_argument("--entity")
    s.set_defaults(fn=cmd_search)

    s = top.add_parser("eval", help="score every search mode on a QA set (evidence-based hits)")
    s.add_argument("--qa", default="eval/harbour_lane_qa.jsonl")
    s.add_argument("--corpus", default="base,full", help="base | full (comma list)")
    s.add_argument("--embed", default="hash", help="comma list: hash,local")
    s.add_argument("--sizes", default="200,400")
    s.add_argument("-k", type=int, default=3)
    s.add_argument("--out")
    s.add_argument("--pool", type=int, help="candidates per retriever before fusion/rerank (default: config)")
    s.add_argument("--show-misses", action="store_true")
    s.set_defaults(fn=cmd_eval)

    s = top.add_parser("replay", help="re-run the queries repo 3's agent actually sent, against every mode")
    s.add_argument("--replay", default="eval/agent_replay.jsonl")
    s.add_argument("--corpus", default="base", choices=tuple(CORPORA))
    s.add_argument("--embed", default="local")
    s.add_argument("--chunk-size", type=int, default=200)
    s.add_argument("--pool", type=int, help="candidates per retriever before fusion/rerank (default: config)")
    s.add_argument("-k", type=int, default=4)
    s.add_argument("--out")
    s.set_defaults(fn=cmd_replay)

    s = top.add_parser("agent-eval", help="repo 3's agent + eval, with this repo's search behind the tool")
    s.add_argument("--qa", default="eval/agent_qa.jsonl")
    s.add_argument("--modes", default="vector,hybrid+rerank")
    s.add_argument("--model")
    s.add_argument("--embed", default="local")
    s.add_argument("--corpus", default="base", choices=tuple(CORPORA))
    s.add_argument("--chunk-size", type=int, default=200)
    s.add_argument("--pool", type=int, help="candidates per retriever before fusion/rerank (default: config)")
    s.add_argument("--dump")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_agent_eval)

    args = p.parse_args(argv)
    cfg = load_config(args.config)
    try:
        return args.fn(args, cfg)
    except (RuntimeError, LookupError, FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
