# LangChain Full89 Results

One trial per task, 89 distinct Terminal-Bench 2.1 tasks. This is not best-of-N.

| Metric | Value |
|---|---:|
| Solved | 68/89 (76.40%) |
| Verifier reward 0 | 20 |
| Unscored, verifier timeout | 1 |
| Estimated API-equivalent cost | $5.05064428 |
| Cost per task | 5.6749 cents |
| Cost per solved task | 7.4274 cents |
| Token-weighted cache-read rate | 93.6471% |
| Input tokens (including cache) | 106,890,221 |
| Cache-read tokens | 100,099,584 |
| Output tokens | 1,408,771 |
| Completed model requests | 3,061 |
| Tool calls | 3,867 |
| First trial start to last trial finish | 9.527 hours |
| Largest single request input | 179,044 tokens |

## Interpretation

`model-extraction-relu-logits` has no verifier reward: Harbor reports a `VerifierTimeoutError` after 900 seconds. It is not silently converted to a reward-zero trial. The full-sample success denominator remains 89. The six-hour agent timeout does not extend this separate verifier timeout.

Prices are offline OpenAI API-equivalent estimates from `genai-prices`, not Codex subscription charges or an API invoice. Each completed request is priced individually at its recorded timestamp, preserving cached-token accounting and request-level pricing tiers. Original Harbor/Kedi cost fields remain unchanged. Request token totals and request counts match each task's captured usage.

The Pydantic comparison run also solved 68/89, at a published estimate of $4.93781512 and 94.48% cache reads. LangChain is about 2.29% more expensive here. One sample per task does not establish adapter equivalence or explain causality; model sampling, transport, sandbox, and verifier timing can all affect outcomes.

## Distributions

Percentiles use linear interpolation (inclusive method). Duration includes the whole Harbor trial, not only model latency. Aggregate trial time is not wall time.

| Metric | Mean | Median / p50 | p95 | Maximum |
|---|---:|---:|---:|---:|
| Duration (s) | 696.69220 | 362.35952 | 1,523.69993 | 7,484.72376 |
| Cost (USD) | 0.05675 | 0.03189 | 0.15467 | 0.43384 |
| Input tokens | 1,201,013.71910 | 328,160.00000 | 4,784,921.00000 | 16,930,847.00000 |
| Output tokens | 15,828.88764 | 9,355.00000 | 37,952.00000 | 164,835.00000 |
| Model requests | 34.39326 | 22.00000 | 91.00000 | 161.00000 |
| Tool calls | 43.44944 | 33.00000 | 103.60000 | 172.00000 |

## Per-Task Evidence

| Task | Reward | Cost (USD) | Duration (s) | Requests | Tool calls | Cache read |
|---|---:|---:|---:|---:|---:|---:|
| [adaptive-rejection-sampler](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/adaptive-rejection-sampler__zSz8F5A/result.json) | 1.0 | 0.07483488 | 922.65 | 49 | 48 | 91.05% |
| [bn-fit-modify](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/bn-fit-modify__RYcUh4V/result.json) | 1.0 | 0.01131108 | 199.01 | 10 | 14 | 50.74% |
| [break-filter-js-from-html](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/break-filter-js-from-html__LjPL6Kc/result.json) | 1.0 | 0.07005436 | 750.54 | 46 | 47 | 87.53% |
| [build-cython-ext](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/build-cython-ext__korAqBA/result.json) | 1.0 | 0.04412560 | 362.36 | 40 | 53 | 92.06% |
| [build-pmars](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/build-pmars__eNQUNaL/result.json) | 1.0 | 0.02484128 | 192.69 | 16 | 33 | 71.66% |
| [build-pov-ray](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/build-pov-ray__mvgEN5t/result.json) | 0.0 | 0.08800788 | 510.06 | 65 | 101 | 95.18% |
| [caffe-cifar-10](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/caffe-cifar-10__zibKeDw/result.json) | 1.0 | 0.06521088 | 1238.34 | 71 | 92 | 93.06% |
| [cancel-async-tasks](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/cancel-async-tasks__eYdQo8Q/result.json) | 1.0 | 0.00748840 | 151.83 | 7 | 6 | 38.59% |
| [chess-best-move](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/chess-best-move__D2jzEfB/result.json) | 1.0 | 0.04003324 | 493.80 | 36 | 40 | 81.37% |
| [circuit-fibsqrt](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/circuit-fibsqrt__bV9bmkw/result.json) | 1.0 | 0.11401988 | 848.00 | 67 | 94 | 96.27% |
| [cobol-modernization](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/cobol-modernization__HXRFuYu/result.json) | 1.0 | 0.03188964 | 341.74 | 23 | 36 | 82.24% |
| [code-from-image](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/code-from-image__a3rvWt8/result.json) | 1.0 | 0.06101324 | 493.38 | 58 | 61 | 93.29% |
| [compile-compcert](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/compile-compcert__wu5GL2d/result.json) | 1.0 | 0.09017720 | 1182.45 | 62 | 72 | 89.45% |
| [configure-git-webserver](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/configure-git-webserver__XDMdCXP/result.json) | 0.0 | 0.01476668 | 227.53 | 12 | 14 | 68.28% |
| [constraints-scheduling](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/constraints-scheduling__fq3vG6j/result.json) | 1.0 | 0.00301204 | 114.22 | 4 | 5 | 60.89% |
| [count-dataset-tokens](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/count-dataset-tokens__ApaQchw/result.json) | 1.0 | 0.01311708 | 209.46 | 15 | 15 | 72.29% |
| [crack-7z-hash](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/crack-7z-hash__ZadNwMh/result.json) | 1.0 | 0.10940072 | 1093.47 | 69 | 85 | 91.90% |
| [custom-memory-heap-crash](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/custom-memory-heap-crash__DYhw8jM/result.json) | 1.0 | 0.01992128 | 318.15 | 18 | 37 | 81.54% |
| [db-wal-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/db-wal-recovery__XwxfTpJ/result.json) | 0.0 | 0.00713436 | 119.30 | 9 | 15 | 55.72% |
| [distribution-search](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/distribution-search__xubB6fY/result.json) | 1.0 | 0.00606964 | 137.58 | 9 | 8 | 72.00% |
| [dna-assembly](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/dna-assembly__xfVqoyG/result.json) | 0.0 | 0.07992732 | 685.22 | 42 | 42 | 89.71% |
| [dna-insert](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/dna-insert__kbZefWb/result.json) | 1.0 | 0.01865416 | 232.59 | 19 | 20 | 81.09% |
| [extract-elf](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/extract-elf__iNJ5yWo/result.json) | 0.0 | 0.02738380 | 294.68 | 11 | 16 | 62.82% |
| [extract-moves-from-video](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/extract-moves-from-video__4RDHAwH/result.json) | 0.0 | 0.13628440 | 1741.95 | 79 | 89 | 95.81% |
| [feal-differential-cryptanalysis](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/feal-differential-cryptanalysis__AFhUQbJ/result.json) | 1.0 | 0.03318424 | 466.22 | 20 | 21 | 86.75% |
| [feal-linear-cryptanalysis](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/feal-linear-cryptanalysis__tcs5ar7/result.json) | 1.0 | 0.04600240 | 652.35 | 33 | 48 | 84.64% |
| [filter-js-from-html](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/filter-js-from-html__Xt26yzx/result.json) | 0.0 | 0.03556916 | 563.66 | 22 | 26 | 90.46% |
| [financial-document-processor](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/financial-document-processor__kxh9vbY/result.json) | 1.0 | 0.02203668 | 246.55 | 20 | 42 | 86.44% |
| [fix-code-vulnerability](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/fix-code-vulnerability__bdUEq6C/result.json) | 1.0 | 0.00728928 | 136.59 | 9 | 22 | 78.56% |
| [fix-git](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/fix-git__A656JUv/result.json) | 1.0 | 0.00833568 | 122.39 | 12 | 31 | 80.64% |
| [fix-ocaml-gc](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/fix-ocaml-gc__UdwwHpz/result.json) | 1.0 | 0.15884908 | 1435.03 | 85 | 103 | 96.94% |
| [gcode-to-text](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/gcode-to-text__oEFwnyj/result.json) | 0.0 | 0.13842088 | 915.08 | 58 | 60 | 91.39% |
| [git-leak-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/git-leak-recovery__6VyTj6P/result.json) | 1.0 | 0.00850160 | 148.26 | 10 | 28 | 58.01% |
| [git-multibranch](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/git-multibranch__YMiYhpQ/result.json) | 1.0 | 0.04414944 | 377.65 | 39 | 72 | 90.21% |
| [gpt2-codegolf](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/gpt2-codegolf__3XqABez/result.json) | 0.0 | 0.18186268 | 1105.70 | 99 | 104 | 97.03% |
| [headless-terminal](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/headless-terminal__9CdBEQc/result.json) | 1.0 | 0.02145340 | 277.07 | 19 | 18 | 76.21% |
| [hf-model-inference](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/hf-model-inference__crUnVke/result.json) | 1.0 | 0.01100480 | 240.88 | 18 | 23 | 72.04% |
| [install-windows-3.11](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/install-windows-3.11__736TyfD/result.json) | 0.0 | 0.14524276 | 865.59 | 95 | 129 | 96.62% |
| [kv-store-grpc](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/kv-store-grpc__G3hzhWK/result.json) | 1.0 | 0.00614564 | 132.48 | 12 | 13 | 67.26% |
| [large-scale-text-editing](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/large-scale-text-editing__buXD22n/result.json) | 1.0 | 0.07587276 | 1582.81 | 96 | 113 | 91.65% |
| [largest-eigenval](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/largest-eigenval__vpzHn2X/result.json) | 0.0 | 0.41944064 | 5468.61 | 95 | 99 | 96.81% |
| [llm-inference-batching-scheduler](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/llm-inference-batching-scheduler__aNbPr8y/result.json) | 1.0 | 0.03848376 | 450.00 | 27 | 33 | 90.86% |
| [log-summary-date-ranges](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/log-summary-date-ranges__vcJDkhX/result.json) | 1.0 | 0.00473432 | 107.98 | 5 | 6 | 48.95% |
| [mailman](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/mailman__zuZ6TGN/result.json) | 1.0 | 0.05690404 | 465.09 | 37 | 94 | 93.55% |
| [make-doom-for-mips](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/make-doom-for-mips__kK45Mtj/result.json) | 1.0 | 0.43383628 | 1175.73 | 161 | 172 | 98.42% |
| [make-mips-interpreter](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/make-mips-interpreter__5dNZVbu/result.json) | 0.0 | 0.09754152 | 620.55 | 61 | 91 | 96.16% |
| [mcmc-sampling-stan](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/mcmc-sampling-stan__Rw55Pdr/result.json) | 0.0 | 0.05815760 | 1088.40 | 60 | 72 | 90.44% |
| [merge-diff-arc-agi-task](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/merge-diff-arc-agi-task__khTbjLr/result.json) | 1.0 | 0.01297164 | 170.12 | 21 | 36 | 77.38% |
| [model-extraction-relu-logits](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/model-extraction-relu-logits__Vmp9F6s/result.json) | unscored | 0.03876120 | 1279.02 | 25 | 24 | 83.41% |
| [modernize-scientific-stack](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/modernize-scientific-stack__YRqmBqv/result.json) | 1.0 | 0.00491820 | 98.21 | 6 | 12 | 45.92% |
| [mteb-leaderboard](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/mteb-leaderboard__WnwK4Rd/result.json) | 1.0 | 0.08287520 | 529.19 | 54 | 56 | 91.40% |
| [mteb-retrieve](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/mteb-retrieve__szGEc5t/result.json) | 1.0 | 0.00803284 | 226.60 | 9 | 18 | 53.40% |
| [multi-source-data-merger](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/multi-source-data-merger__kH74N9A/result.json) | 1.0 | 0.00974204 | 160.28 | 10 | 16 | 47.61% |
| [nginx-request-logging](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/nginx-request-logging__e9Naowo/result.json) | 1.0 | 0.00978176 | 156.12 | 8 | 9 | 42.82% |
| [openssl-selfsigned-cert](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/openssl-selfsigned-cert__ChXP7ng/result.json) | 1.0 | 0.00861880 | 143.43 | 12 | 18 | 59.38% |
| [overfull-hbox](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/overfull-hbox__m9D6eoU/result.json) | 1.0 | 0.02234908 | 254.75 | 21 | 26 | 75.99% |
| [password-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/password-recovery__GVGA96n/result.json) | 1.0 | 0.01688060 | 230.08 | 25 | 35 | 80.84% |
| [path-tracing](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/path-tracing__BsUNgfA/result.json) | 1.0 | 0.14841352 | 1000.20 | 70 | 71 | 96.81% |
| [path-tracing-reverse](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/path-tracing-reverse__crYNDTZ/result.json) | 1.0 | 0.13172984 | 744.63 | 57 | 63 | 95.98% |
| [polyglot-c-py](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/polyglot-c-py__9Ln7ju5/result.json) | 1.0 | 0.01704752 | 227.25 | 17 | 21 | 76.40% |
| [polyglot-rust-c](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/polyglot-rust-c__N3h3soD/result.json) | 1.0 | 0.01509276 | 192.55 | 14 | 23 | 72.35% |
| [portfolio-optimization](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/portfolio-optimization__5Gv86yy/result.json) | 1.0 | 0.01131872 | 242.24 | 10 | 14 | 70.56% |
| [protein-assembly](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/protein-assembly__o6bbCZr/result.json) | 1.0 | 0.07516060 | 782.32 | 42 | 45 | 89.78% |
| [prove-plus-comm](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/prove-plus-comm__RtV6DZP/result.json) | 1.0 | 0.01258084 | 285.05 | 20 | 19 | 61.43% |
| [pypi-server](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/pypi-server__SgdxGQa/result.json) | 1.0 | 0.01725764 | 194.85 | 21 | 41 | 63.76% |
| [pytorch-model-cli](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/pytorch-model-cli__VTX3M9e/result.json) | 1.0 | 0.01585908 | 240.90 | 17 | 25 | 79.27% |
| [pytorch-model-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/pytorch-model-recovery__PLPRzUP/result.json) | 1.0 | 0.01673160 | 273.73 | 15 | 16 | 73.49% |
| [qemu-alpine-ssh](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/qemu-alpine-ssh__7gJ5Sie/result.json) | 1.0 | 0.03302540 | 258.50 | 45 | 50 | 84.94% |
| [qemu-startup](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/qemu-startup__uX9aC8U/result.json) | 1.0 | 0.01299276 | 264.74 | 17 | 24 | 78.59% |
| [query-optimize](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/query-optimize__KCSDVss/result.json) | 0.0 | 0.01932276 | 731.15 | 18 | 25 | 80.88% |
| [raman-fitting](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/raman-fitting__Y7xWcLo/result.json) | 0.0 | 0.10753436 | 942.15 | 50 | 49 | 92.49% |
| [regex-chess](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/regex-chess__LfK2NaZ/result.json) | 0.0 | 0.10904364 | 1102.52 | 61 | 61 | 94.91% |
| [regex-log](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/regex-log__zzLkHwx/result.json) | 1.0 | 0.01288768 | 167.93 | 7 | 6 | 15.47% |
| [reshard-c4-data](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/reshard-c4-data__i6merey/result.json) | 1.0 | 0.06726080 | 855.32 | 48 | 69 | 91.17% |
| [rstan-to-pystan](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/rstan-to-pystan__QMQC7RY/result.json) | 1.0 | 0.03081340 | 559.09 | 30 | 39 | 91.27% |
| [sam-cell-seg](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/sam-cell-seg__RCaFP2a/result.json) | 1.0 | 0.04969592 | 936.80 | 28 | 31 | 87.10% |
| [sanitize-git-repo](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/sanitize-git-repo__uxHWAG4/result.json) | 1.0 | 0.01765100 | 341.61 | 11 | 17 | 72.21% |
| [schemelike-metacircular-eval](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/schemelike-metacircular-eval__9LtykQq/result.json) | 1.0 | 0.03803476 | 897.01 | 25 | 30 | 89.84% |
| [sparql-university](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/sparql-university__CdAtbnD/result.json) | 1.0 | 0.01544632 | 210.01 | 11 | 11 | 70.40% |
| [sqlite-db-truncate](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/sqlite-db-truncate__oMBFmjM/result.json) | 1.0 | 0.00791012 | 132.04 | 7 | 8 | 44.92% |
| [sqlite-with-gcov](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/sqlite-with-gcov__piNnRTa/result.json) | 1.0 | 0.01820872 | 247.48 | 18 | 32 | 76.19% |
| [torch-pipeline-parallelism](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/torch-pipeline-parallelism__b8a8TuQ/result.json) | 0.0 | 0.03422064 | 687.07 | 17 | 17 | 84.66% |
| [torch-tensor-parallelism](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1/torch-tensor-parallelism__9SRitHQ/result.json) | 1.0 | 0.00899784 | 246.43 | 8 | 7 | 63.34% |
| [train-fasttext](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/train-fasttext__BKLkVQi/result.json) | 0.0 | 0.05496980 | 7484.72 | 57 | 59 | 86.13% |
| [tune-mjcf](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/tune-mjcf__bMtgF6H/result.json) | 1.0 | 0.04256168 | 699.05 | 31 | 31 | 82.40% |
| [video-processing](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/video-processing__7C9cyws/result.json) | 0.0 | 0.06437028 | 567.92 | 40 | 41 | 91.70% |
| [vulnerable-secret](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/vulnerable-secret__L2bstYq/result.json) | 1.0 | 0.00777700 | 107.73 | 9 | 16 | 57.74% |
| [winning-avg-corewars](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/winning-avg-corewars__KVr9zc5/result.json) | 0.0 | 0.32627396 | 4907.18 | 52 | 115 | 95.13% |
| [write-compressor](evidence/harbor/daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2/write-compressor__AFCnioc/result.json) | 1.0 | 0.08382428 | 722.00 | 67 | 78 | 93.14% |
