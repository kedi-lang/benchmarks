# Results

## Summary

This immutable run covers all 89 Terminal-Bench 2.1 tasks exactly once. Harbor's official verifier awarded reward 1 to **68/89 tasks (76.40%)**. The Wilson 95% interval for this single-trial pass proportion is **66.61%-84.02%**; it describes sampling uncertainty, not five-trial leaderboard accuracy.

| Metric | Result |
| --- | ---: |
| Official reward | 68/89 (76.40%) |
| Provider-reported total cost | $4.93781512 |
| Cost per attempted task | $0.05548107 (5.548 cents) |
| Cost per solved task | $0.07261493 (7.261 cents) |
| Input tokens | 119,974,598 |
| Cache-read input tokens | 113,355,776 (94.48%) |
| Uncached input tokens | 6,618,822 |
| Output tokens | 1,122,446 |
| Model requests | 3,121 |
| Tool calls | 3,800 |
| Observed wall span | 7.88 hours |
| Sum of per-task durations | 14.12 hours |

## Configuration

- Model: `codex/gpt-5.6-luna`, high effort.
- Adapter: Kedi Pydantic adapter; CodeMode disabled; artifacts and history enabled; compaction disabled.
- Transport: WebSocket first with HTTP fallback; Logfire disabled.
- Execution: 81 standard tasks at concurrency 2, followed by 8 high-memory tasks at concurrency 1.
- Timeout: six hours per agent; one attempt per task and no automatic trial retries.
- Environment: Daytona sandboxes; Harbor 0.22.0; Kedi 0.4.0; codex-auth-helper 1.8.0.
- Dataset: Terminal-Bench 2.1, with the `evalstate` infrastructure-only QEMU fixes for `qemu-alpine-ssh` and `qemu-startup`.

## Distribution

| Metric | Median | Mean | P90 | P95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cost (USD) | $0.02364 | $0.05548 | $0.14343 | $0.19746 | $0.58565 |
| Duration (s) | 335.7 | 571.0 | 1269.7 | 1786.6 | 4018.4 |
| Input tokens | 267,611 | 1,348,029 | 3,564,265 | 5,068,932 | 22,352,464 |
| Output tokens | 8,429 | 12,611 | 35,364 | 43,794 | 60,956 |
| Model requests | 21 | 35.1 | 81.0 | 100.0 | 217 |
| Tool calls | 30 | 42.7 | 86.6 | 131.8 | 245 |

## Batch Breakdown

| Batch | Tasks | Solved | Score | Cost | Cache-read ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Standard C2 | 81 | 62 | 76.54% | $4.43934284 | 94.66% |
| High-memory C1 | 8 | 6 | 75.00% | $0.49847228 | 92.77% |

## Reward-Zero Tasks

All 21 tasks below reached Harbor grading and received reward 0. None ended with a Harbor exception. The observation column is post-run diagnosis and does not alter the official score.

| Task | Observed verifier failure | Cost | Duration |
| --- | --- | ---: | ---: |
| [cancel-async-tasks](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/cancel-async-tasks__etxtW4G/result.json) | 5/6 verifier tests passed; queued-task cleanup messages were missing. | $0.00635 | 123.2s |
| [chess-best-move](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/chess-best-move__xPbKX6a/result.json) | The answer returned one winning move where the verifier required both. | $0.01661 | 216.2s |
| [configure-git-webserver](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/configure-git-webserver__UDo2qsc/result.json) | The verifier received HTTP 000 and found no usable deployment. | $0.02119 | 260.4s |
| [count-dataset-tokens](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/count-dataset-tokens__ca6krts/result.json) | The command returned 63,841 tokens instead of 79,586. | $0.01910 | 183.8s |
| [db-wal-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/db-wal-recovery__NrM2Ary/result.json) | The WAL update was not recovered; 5/7 tests passed. | $0.02357 | 319.1s |
| [dna-assembly](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/dna-assembly__nNBJ8Gm/result.json) | The required BsaI site was absent from the produced primers. | $0.04067 | 438.8s |
| [extract-elf](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/extract-elf__8SwFYpc/result.json) | The output format passed, but none of the expected values matched. | $0.02444 | 278.4s |
| [filter-js-from-html](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/filter-js-from-html__t8DipHs/result.json) | Unsafe cases survived and five benign files were modified. | $0.04877 | 562.9s |
| [gcode-to-text](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/gcode-to-text__3Dw5JE5/result.json) | The reconstructed phrase did not match the target flag. | $0.09462 | 770.8s |
| [install-windows-3.11](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/install-windows-3.11__2snQhLC/result.json) | Keyboard input produced no qualifying visual change; 3/4 tests passed. | $0.19011 | 1313.4s |
| [make-doom-for-mips](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/make-doom-for-mips__xBQWFrs/result.json) | The expected graphics initialization output was absent; 2/3 tests passed. | $0.58565 | 1740.5s |
| [model-extraction-relu-logits](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/model-extraction-relu-logits__zXFBEGT/result.json) | Nine rows of the extracted matrix did not match. | $0.01864 | 251.5s |
| [mteb-retrieve](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/mteb-retrieve__J6FFxfz/result.json) | The package check passed, but the retrieved document was incorrect. | $0.00610 | 176.7s |
| [protein-assembly](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/protein-assembly__WUXc9MJ/result.json) | The required donor sequence was absent from the assembled gBlock. | $0.06784 | 650.9s |
| [query-optimize](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/query-optimize__DdsHaCA/result.json) | Correctness passed, but runtime exceeded the limit by about 27 ms. | $0.01268 | 961.6s |
| [raman-fitting](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/raman-fitting__XzMjSMP/result.json) | The fitted peak centers were far from the required values. | $0.04180 | 445.3s |
| [regex-chess](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/regex-chess__zWFxEBg/result.json) | Three valid-position game tests were missing legal moves. | $0.20049 | 1817.4s |
| [torch-pipeline-parallelism](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/torch-pipeline-parallelism__wjDTbh9/result.json) | Backward gradients mismatched for rank 1, microbatch 0; 2/3 tests passed. | $0.02312 | 551.0s |
| [train-fasttext](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/train-fasttext__rmbpmEv/result.json) | Accuracy was 0.618 against the required 0.620. | $0.03777 | 3809.8s |
| [video-processing](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/video-processing__7VsE5Pt/result.json) | Both reported event frames were five frames outside accepted ranges. | $0.05225 | 443.3s |
| [winning-avg-corewars](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/winning-avg-corewars__zpKCECd/result.json) | The warrior scored 7% against snake.red; 33% was required. | $0.17764 | 1264.0s |

## Per-Task Results

| Task | Reward | Batch | Duration | Cost | Input | Cache read | Cache ratio | Output | Requests | Tools |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [adaptive-rejection-sampler](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/adaptive-rejection-sampler__jLGJ92B/result.json) | 1 | standard81-c2 | 699.4s | $0.05417 | 746,265 | 667,136 | 89.4% | 20,832 | 39 | 45 |
| [bn-fit-modify](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/bn-fit-modify__bNdoc38/result.json) | 1 | standard81-c2 | 256.8s | $0.02269 | 226,365 | 186,368 | 82.3% | 9,137 | 19 | 24 |
| [break-filter-js-from-html](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/break-filter-js-from-html__svRTvcY/result.json) | 1 | standard81-c2 | 527.1s | $0.03357 | 289,662 | 235,520 | 81.3% | 15,026 | 24 | 30 |
| [build-cython-ext](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/build-cython-ext__XiU5Uq6/result.json) | 1 | standard81-c2 | 389.8s | $0.05323 | 1,426,859 | 1,350,656 | 94.7% | 9,144 | 48 | 52 |
| [build-pmars](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/build-pmars__YHyXEdB/result.json) | 1 | standard81-c2 | 209.2s | $0.03163 | 613,850 | 539,136 | 87.8% | 4,924 | 27 | 45 |
| [build-pov-ray](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/build-pov-ray__TRWXZUe/result.json) | 1 | standard81-c2 | 624.2s | $0.10045 | 2,998,576 | 2,864,640 | 95.5% | 13,643 | 74 | 75 |
| [caffe-cifar-10](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/caffe-cifar-10__yezFpff/result.json) | 1 | high-memory8-c1 | 654.4s | $0.03205 | 599,280 | 528,384 | 88.2% | 6,086 | 37 | 46 |
| [cancel-async-tasks](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/cancel-async-tasks__etxtW4G/result.json) | 0 | standard81-c2 | 123.2s | $0.00635 | 26,466 | 12,288 | 46.4% | 2,721 | 7 | 6 |
| [chess-best-move](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/chess-best-move__xPbKX6a/result.json) | 0 | standard81-c2 | 216.2s | $0.01661 | 63,619 | 28,160 | 44.3% | 7,462 | 11 | 12 |
| [circuit-fibsqrt](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/circuit-fibsqrt__iBGnw9B/result.json) | 1 | standard81-c2 | 1447.4s | $0.18929 | 4,898,103 | 4,698,624 | 95.9% | 46,186 | 97 | 141 |
| [cobol-modernization](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/cobol-modernization__7kpsAa7/result.json) | 1 | standard81-c2 | 329.6s | $0.03384 | 378,356 | 315,904 | 83.5% | 12,528 | 25 | 34 |
| [code-from-image](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/code-from-image__73LE2nW/result.json) | 1 | standard81-c2 | 350.5s | $0.04262 | 552,811 | 433,664 | 78.4% | 8,429 | 39 | 49 |
| [compile-compcert](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/compile-compcert__kNhXfSo/result.json) | 1 | standard81-c2 | 776.1s | $0.05157 | 1,102,530 | 982,016 | 89.1% | 6,521 | 50 | 46 |
| [configure-git-webserver](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/configure-git-webserver__UDo2qsc/result.json) | 0 | standard81-c2 | 260.4s | $0.02119 | 146,128 | 111,104 | 76.0% | 9,969 | 15 | 17 |
| [constraints-scheduling](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/constraints-scheduling__yykdZEG/result.json) | 1 | standard81-c2 | 107.1s | $0.00349 | 19,128 | 12,288 | 64.2% | 1,563 | 4 | 5 |
| [count-dataset-tokens](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/count-dataset-tokens__ca6krts/result.json) | 0 | standard81-c2 | 183.8s | $0.01910 | 254,793 | 205,312 | 80.6% | 4,250 | 22 | 21 |
| [crack-7z-hash](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/crack-7z-hash__LRrfKwT/result.json) | 1 | standard81-c2 | 242.0s | $0.02325 | 301,334 | 228,864 | 76.0% | 3,486 | 19 | 33 |
| [custom-memory-heap-crash](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/custom-memory-heap-crash__JGEC5pU/result.json) | 1 | standard81-c2 | 366.4s | $0.03395 | 731,355 | 683,008 | 93.4% | 8,851 | 38 | 62 |
| [db-wal-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/db-wal-recovery__NrM2Ary/result.json) | 0 | standard81-c2 | 319.1s | $0.02357 | 267,611 | 227,840 | 85.1% | 9,220 | 18 | 39 |
| [distribution-search](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/distribution-search__bZexQSc/result.json) | 1 | standard81-c2 | 150.6s | $0.00880 | 43,706 | 23,552 | 53.9% | 3,581 | 9 | 8 |
| [dna-assembly](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/dna-assembly__nNBJ8Gm/result.json) | 0 | standard81-c2 | 438.8s | $0.04067 | 524,053 | 478,208 | 91.3% | 18,283 | 24 | 28 |
| [dna-insert](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/dna-insert__8xmmC5j/result.json) | 1 | standard81-c2 | 273.2s | $0.01902 | 193,938 | 165,376 | 85.3% | 8,337 | 20 | 23 |
| [extract-elf](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/extract-elf__8SwFYpc/result.json) | 0 | standard81-c2 | 278.4s | $0.02444 | 222,318 | 186,880 | 84.1% | 11,346 | 14 | 17 |
| [extract-moves-from-video](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/extract-moves-from-video__zE7mbCe/result.json) | 1 | standard81-c2 | 4018.4s | $0.19943 | 6,127,223 | 5,937,152 | 96.9% | 35,560 | 125 | 133 |
| [feal-differential-cryptanalysis](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/feal-differential-cryptanalysis__gxxFrVz/result.json) | 1 | standard81-c2 | 335.7s | $0.01684 | 107,098 | 84,992 | 79.4% | 8,936 | 13 | 12 |
| [feal-linear-cryptanalysis](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/feal-linear-cryptanalysis__DqPhmkM/result.json) | 1 | standard81-c2 | 1282.0s | $0.03347 | 502,620 | 450,048 | 89.5% | 11,631 | 35 | 48 |
| [filter-js-from-html](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/filter-js-from-html__t8DipHs/result.json) | 0 | high-memory8-c1 | 562.9s | $0.04877 | 648,894 | 575,488 | 88.7% | 18,820 | 38 | 42 |
| [financial-document-processor](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/financial-document-processor__ZwkFPYV/result.json) | 1 | standard81-c2 | 212.6s | $0.02106 | 293,121 | 238,080 | 81.2% | 4,411 | 21 | 35 |
| [fix-code-vulnerability](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/fix-code-vulnerability__Ks39Edn/result.json) | 1 | standard81-c2 | 125.8s | $0.01109 | 170,700 | 141,824 | 83.1% | 2,063 | 15 | 22 |
| [fix-git](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/fix-git__GxSsgJR/result.json) | 1 | standard81-c2 | 115.1s | $0.00533 | 55,964 | 45,056 | 80.5% | 1,869 | 10 | 26 |
| [fix-ocaml-gc](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/fix-ocaml-gc__2jgmS2e/result.json) | 1 | standard81-c2 | 2189.6s | $0.06196 | 1,682,702 | 1,569,280 | 93.3% | 6,576 | 47 | 52 |
| [gcode-to-text](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/gcode-to-text__3Dw5JE5/result.json) | 0 | standard81-c2 | 770.8s | $0.09462 | 1,756,491 | 1,648,128 | 93.8% | 33,324 | 49 | 48 |
| [git-leak-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/git-leak-recovery__KZbY3cE/result.json) | 1 | standard81-c2 | 114.0s | $0.00706 | 36,260 | 13,312 | 36.7% | 1,836 | 8 | 21 |
| [git-multibranch](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/git-multibranch__Mk3jrKe/result.json) | 1 | standard81-c2 | 294.6s | $0.03003 | 373,198 | 309,760 | 83.0% | 9,287 | 22 | 32 |
| [gpt2-codegolf](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/gpt2-codegolf__HhaiyJc/result.json) | 1 | high-memory8-c1 | 1103.0s | $0.19451 | 5,182,819 | 4,926,464 | 95.1% | 37,261 | 129 | 134 |
| [headless-terminal](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/headless-terminal__L4BdXkJ/result.json) | 1 | standard81-c2 | 305.4s | $0.02364 | 204,625 | 162,304 | 79.3% | 9,941 | 21 | 23 |
| [hf-model-inference](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/hf-model-inference__omCX2bD/result.json) | 1 | standard81-c2 | 171.8s | $0.00736 | 53,390 | 32,768 | 61.4% | 2,154 | 12 | 14 |
| [install-windows-3.11](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/install-windows-3.11__2snQhLC/result.json) | 0 | standard81-c2 | 1313.4s | $0.19011 | 4,667,914 | 4,365,824 | 93.5% | 35,316 | 102 | 119 |
| [kv-store-grpc](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/kv-store-grpc__5U6YVDM/result.json) | 1 | standard81-c2 | 140.8s | $0.00842 | 80,762 | 60,928 | 75.4% | 2,699 | 15 | 17 |
| [large-scale-text-editing](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/large-scale-text-editing__3vLhtV4/result.json) | 1 | standard81-c2 | 707.0s | $0.01493 | 161,562 | 133,632 | 82.7% | 5,563 | 21 | 35 |
| [largest-eigenval](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/largest-eigenval__QRdSEDW/result.json) | 1 | standard81-c2 | 282.7s | $0.02464 | 262,763 | 211,456 | 80.5% | 8,455 | 26 | 26 |
| [llm-inference-batching-scheduler](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/llm-inference-batching-scheduler__iL6VCWd/result.json) | 1 | standard81-c2 | 240.8s | $0.02024 | 229,211 | 197,632 | 86.2% | 8,311 | 18 | 24 |
| [log-summary-date-ranges](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/log-summary-date-ranges__rgBvMVs/result.json) | 1 | standard81-c2 | 114.3s | $0.00622 | 46,890 | 29,696 | 63.3% | 1,820 | 6 | 9 |
| [mailman](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/mailman__fuFom9g/result.json) | 1 | standard81-c2 | 487.2s | $0.07204 | 1,845,130 | 1,747,456 | 94.7% | 14,629 | 45 | 53 |
| [make-doom-for-mips](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/make-doom-for-mips__xBQWFrs/result.json) | 0 | standard81-c2 | 1740.5s | $0.58565 | 21,697,216 | 21,260,800 | 98.0% | 60,956 | 200 | 245 |
| [make-mips-interpreter](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/make-mips-interpreter__U7dPAXH/result.json) | 1 | standard81-c2 | 1926.3s | $0.56316 | 22,352,464 | 22,038,528 | 98.6% | 49,669 | 217 | 242 |
| [mcmc-sampling-stan](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/mcmc-sampling-stan__h3bs4vp/result.json) | 1 | high-memory8-c1 | 1266.7s | $0.03792 | 742,449 | 657,920 | 88.6% | 6,544 | 40 | 54 |
| [merge-diff-arc-agi-task](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/merge-diff-arc-agi-task__TQcSrDL/result.json) | 1 | standard81-c2 | 180.3s | $0.01449 | 174,963 | 143,360 | 81.9% | 4,422 | 21 | 43 |
| [model-extraction-relu-logits](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/model-extraction-relu-logits__zXFBEGT/result.json) | 0 | standard81-c2 | 251.5s | $0.01864 | 112,375 | 82,432 | 73.4% | 9,167 | 11 | 10 |
| [modernize-scientific-stack](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/modernize-scientific-stack__ufeTEbA/result.json) | 1 | standard81-c2 | 105.6s | $0.00535 | 31,853 | 17,920 | 56.3% | 1,838 | 7 | 11 |
| [mteb-leaderboard](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/mteb-leaderboard__d2L6jmm/result.json) | 1 | high-memory8-c1 | 601.3s | $0.11660 | 3,176,709 | 2,973,184 | 93.6% | 13,693 | 86 | 85 |
| [mteb-retrieve](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/mteb-retrieve__J6FFxfz/result.json) | 0 | standard81-c2 | 176.7s | $0.00610 | 32,548 | 10,752 | 33.0% | 1,271 | 8 | 9 |
| [multi-source-data-merger](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/multi-source-data-merger__ZENMX8v/result.json) | 1 | standard81-c2 | 138.0s | $0.00720 | 32,468 | 14,336 | 44.2% | 2,735 | 7 | 12 |
| [nginx-request-logging](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/nginx-request-logging__5oRHBbS/result.json) | 1 | standard81-c2 | 139.2s | $0.01132 | 55,872 | 22,016 | 39.4% | 3,420 | 8 | 18 |
| [openssl-selfsigned-cert](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/openssl-selfsigned-cert__Ykk9XeP/result.json) | 1 | standard81-c2 | 139.8s | $0.00699 | 33,043 | 16,384 | 49.6% | 2,775 | 8 | 8 |
| [overfull-hbox](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/overfull-hbox__iX2Edfu/result.json) | 1 | standard81-c2 | 451.8s | $0.06697 | 1,415,346 | 1,283,072 | 90.7% | 12,378 | 70 | 83 |
| [password-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/password-recovery__rVnBEEb/result.json) | 1 | standard81-c2 | 168.6s | $0.01471 | 176,195 | 138,240 | 78.5% | 3,632 | 18 | 23 |
| [path-tracing](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/path-tracing__uAufBDB/result.json) | 1 | standard81-c2 | 1063.8s | $0.13488 | 3,495,359 | 3,380,736 | 96.7% | 36,948 | 67 | 69 |
| [path-tracing-reverse](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/path-tracing-reverse__becqzo6/result.json) | 1 | standard81-c2 | 1014.2s | $0.20648 | 6,182,481 | 6,003,712 | 97.1% | 42,212 | 85 | 99 |
| [polyglot-c-py](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/polyglot-c-py__w9TN5zA/result.json) | 1 | standard81-c2 | 183.2s | $0.01028 | 65,067 | 50,176 | 77.1% | 5,247 | 12 | 17 |
| [polyglot-rust-c](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/polyglot-rust-c__YZPLs8z/result.json) | 1 | standard81-c2 | 212.4s | $0.01566 | 127,726 | 97,792 | 76.6% | 6,428 | 18 | 31 |
| [portfolio-optimization](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/portfolio-optimization__vgR2CFx/result.json) | 1 | standard81-c2 | 266.2s | $0.01192 | 98,724 | 72,192 | 73.1% | 4,312 | 13 | 18 |
| [protein-assembly](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/protein-assembly__WUXc9MJ/result.json) | 0 | standard81-c2 | 650.9s | $0.06784 | 1,146,951 | 1,033,728 | 90.1% | 20,437 | 41 | 43 |
| [prove-plus-comm](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/prove-plus-comm__rfhks36/result.json) | 1 | standard81-c2 | 135.6s | $0.00506 | 41,584 | 27,136 | 65.3% | 1,357 | 11 | 10 |
| [pypi-server](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/pypi-server__yicTorj/result.json) | 1 | standard81-c2 | 207.9s | $0.01827 | 176,591 | 132,096 | 74.8% | 5,611 | 23 | 45 |
| [pytorch-model-cli](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/pytorch-model-cli__mQcpPma/result.json) | 1 | standard81-c2 | 271.9s | $0.01770 | 167,394 | 138,752 | 82.9% | 7,665 | 15 | 22 |
| [pytorch-model-recovery](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/pytorch-model-recovery__xtNrixJ/result.json) | 1 | standard81-c2 | 550.7s | $0.02389 | 279,396 | 243,200 | 87.0% | 9,826 | 23 | 24 |
| [qemu-alpine-ssh](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/qemu-alpine-ssh__4ynAsoX/result.json) | 1 | standard81-c2 | 397.8s | $0.07029 | 1,747,799 | 1,606,656 | 91.9% | 8,276 | 80 | 89 |
| [qemu-startup](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/qemu-startup__yXqMcLt/result.json) | 1 | standard81-c2 | 457.7s | $0.03831 | 635,279 | 559,616 | 88.1% | 9,990 | 39 | 41 |
| [query-optimize](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/query-optimize__DdsHaCA/result.json) | 0 | standard81-c2 | 961.6s | $0.01268 | 87,553 | 59,904 | 68.4% | 4,964 | 11 | 14 |
| [raman-fitting](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/raman-fitting__XzMjSMP/result.json) | 0 | standard81-c2 | 445.3s | $0.04180 | 391,253 | 310,784 | 79.4% | 16,244 | 20 | 22 |
| [regex-chess](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/regex-chess__zWFxEBg/result.json) | 0 | standard81-c2 | 1817.4s | $0.20049 | 4,696,208 | 4,403,200 | 93.8% | 44,850 | 87 | 86 |
| [regex-log](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/regex-log__7hU8vrh/result.json) | 1 | standard81-c2 | 156.7s | $0.00765 | 18,930 | 6,656 | 35.2% | 4,220 | 4 | 3 |
| [reshard-c4-data](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/reshard-c4-data__HXsbcwx/result.json) | 1 | standard81-c2 | 505.1s | $0.04696 | 633,339 | 566,272 | 89.4% | 18,515 | 36 | 36 |
| [rstan-to-pystan](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/rstan-to-pystan__JGuuWmw/result.json) | 1 | high-memory8-c1 | 345.3s | $0.02215 | 329,260 | 292,352 | 88.8% | 7,432 | 20 | 34 |
| [sam-cell-seg](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/sam-cell-seg__LPsQyVe/result.json) | 1 | standard81-c2 | 565.9s | $0.02969 | 266,643 | 228,864 | 85.8% | 14,631 | 17 | 18 |
| [sanitize-git-repo](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/sanitize-git-repo__abkMYba/result.json) | 1 | standard81-c2 | 434.5s | $0.03407 | 345,247 | 290,304 | 84.1% | 14,392 | 25 | 30 |
| [schemelike-metacircular-eval](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/schemelike-metacircular-eval__o2qpfFi/result.json) | 1 | standard81-c2 | 690.0s | $0.05318 | 844,041 | 780,288 | 92.4% | 20,684 | 36 | 53 |
| [sparql-university](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/sparql-university__yKFo7fm/result.json) | 1 | standard81-c2 | 157.9s | $0.01203 | 76,953 | 49,664 | 64.5% | 4,653 | 9 | 9 |
| [sqlite-db-truncate](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/sqlite-db-truncate__S7KktJm/result.json) | 1 | standard81-c2 | 158.8s | $0.00937 | 49,545 | 28,672 | 57.9% | 3,850 | 9 | 15 |
| [sqlite-with-gcov](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/sqlite-with-gcov__N4JcPsa/result.json) | 1 | standard81-c2 | 177.2s | $0.00939 | 101,757 | 75,264 | 74.0% | 2,154 | 13 | 22 |
| [torch-pipeline-parallelism](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/torch-pipeline-parallelism__wjDTbh9/result.json) | 0 | high-memory8-c1 | 551.0s | $0.02312 | 118,133 | 91,136 | 77.1% | 13,246 | 12 | 12 |
| [torch-tensor-parallelism](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1/torch-tensor-parallelism__jJ48ZzR/result.json) | 1 | high-memory8-c1 | 390.6s | $0.02335 | 129,051 | 91,136 | 70.6% | 11,622 | 15 | 14 |
| [train-fasttext](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/train-fasttext__rmbpmEv/result.json) | 0 | standard81-c2 | 3809.8s | $0.03777 | 592,090 | 493,056 | 83.3% | 6,751 | 39 | 43 |
| [tune-mjcf](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/tune-mjcf__Dt2j9KS/result.json) | 1 | standard81-c2 | 194.7s | $0.00790 | 58,924 | 40,960 | 69.5% | 2,910 | 10 | 11 |
| [video-processing](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/video-processing__7VsE5Pt/result.json) | 0 | standard81-c2 | 443.3s | $0.05225 | 768,139 | 677,376 | 88.2% | 17,128 | 30 | 32 |
| [vulnerable-secret](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/vulnerable-secret__yB8UTLq/result.json) | 1 | standard81-c2 | 89.1s | $0.00576 | 69,302 | 49,664 | 71.7% | 701 | 9 | 12 |
| [winning-avg-corewars](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/winning-avg-corewars__zpKCECd/result.json) | 0 | standard81-c2 | 1264.0s | $0.17764 | 3,839,890 | 3,653,632 | 95.1% | 56,099 | 80 | 130 |
| [write-compressor](evidence/harbor/daytona-luna-high-full89-c2-c1-20260912-standard81-c2/write-compressor__TyNTN9K/result.json) | 1 | standard81-c2 | 854.3s | $0.07752 | 1,244,045 | 1,115,648 | 89.7% | 24,604 | 53 | 70 |

## Interpretation And Limits

The aggregate is a complete one-trial measurement of this frozen harness configuration, not a stable estimate of model accuracy. Task outcomes are stochastic; the intended production-style Terminal-Bench aggregate uses five trials per task. Cost is provider-reported and includes cached input pricing as returned by the runtime.

The 21 failures cost $1.70943164 in total, or $0.08140 per failed task, compared with $0.04748 per solved task. Expensive failures therefore materially raise the overall mean even though the median task cost is only $0.02364. This run records 119.97M cumulative input tokens, but 94.48% were cache reads; uncached input was 6.62M tokens.

The two QEMU tasks use an unreleased infrastructure repair from `evalstate/terminal-bench-2-1` commit `75f5a2e66b2dfd9d7eba3065a9d919c1f9da5c5e`. Their rewards are retained as engineering evidence, but this makes the aggregate ineligible for direct official leaderboard submission. No comparison in this repository should treat this single run as causal evidence for Kedi-specific improvements.

The historical Kedi wheel was built from a dirty but fully hashed source tree. Its wheel SHA256 and per-source hashes are preserved in `manifests/experiment-contract.json` and `manifests/expected-sources.json`; the wheel and credentials are intentionally not published. Consequently the record is replayable and auditable, while byte-identical subject re-execution requires the privately retained wheel.
