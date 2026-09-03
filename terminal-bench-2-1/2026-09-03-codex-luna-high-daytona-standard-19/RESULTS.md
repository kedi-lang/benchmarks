# Terminal-Bench 2.1 Daytona Standard-Task Result

## Aggregate

| Measure | Result |
| --- | ---: |
| Attempted trials | 19 |
| Harbor-scored trials | 18 |
| Unscored infrastructure failures | 1 |
| Reward successes among scored trials | **11/18 (61.1%)** |
| Reward successes among all attempts | **11/19 (57.9%)** |
| Autobench/Kedi lifecycle statuses | 8 passed, 11 failed |
| Trials with provider usage evidence | 14/19 |
| Provider-reported cost for measured trials | $4.37852572 |
| Average cost across measured trials only | $0.31275184 |
| Requests across measured trials | 659 |
| Tool calls across measured trials | 972 |
| Input tokens across measured trials | 44,370,227 |
| Cache-read tokens | 26,459,136 (59.63%) |
| Non-cached input tokens | 17,911,091 |
| Output tokens | 222,604 |

Cost and token aggregates exclude five trials with missing Kedi usage records:
two Harbor timeouts, two reward-successful trials whose remote result capture
was lost, and the unscored Daytona installation failure. No full-batch cost per
task is claimed.

## Trials

| Task | Reward | Kedi state | Measured cost | Classification |
| --- | ---: | --- | ---: | --- |
| `bn-fit-modify` | 1.0 | completed | $0.01751868 | Clean pass |
| `build-pov-ray` | 0.0 | budget exhausted | $0.72112476 | Task solution failed authenticity and SSIM checks |
| `circuit-fibsqrt` | 1.0 | budget exhausted | $0.44169592 | Reward pass; agent reached its budget boundary |
| `compile-compcert` | 1.0 | budget exhausted | $0.48624944 | Reward pass; agent reached its budget boundary |
| `distribution-search` | 1.0 | completed | $0.01357172 | Clean pass |
| `extract-moves-from-video` | 1.0 | capture missing | - | Reward pass; remote Kedi result collection incomplete |
| `feal-differential-cryptanalysis` | 1.0 | completed | $0.02011088 | Clean pass |
| `feal-linear-cryptanalysis` | 1.0 | completed | $0.06392012 | Clean pass |
| `fix-ocaml-gc` | 0.0 | budget exhausted | $0.94230296 | Infrastructure-contaminated: verifier could not clone its public dependency |
| `install-windows-3.11` | 0.0 | budget exhausted | $0.41574936 | Task solution incomplete |
| `make-doom-for-mips` | 0.0 | agent timeout | - | Infrastructure-contaminated timeout |
| `make-mips-interpreter` | 0.0 | budget exhausted | $0.97815660 | Task solution incomplete |
| `path-tracing-reverse` | 1.0 | capture missing | - | Reward pass; remote Kedi result collection incomplete |
| `portfolio-optimization` | 1.0 | completed | $0.01493476 | Clean pass |
| `sam-cell-seg` | 1.0 | completed | $0.04050080 | Clean pass |
| `sparql-university` | 1.0 | completed | $0.01417624 | Clean pass |
| `train-fasttext` | 0.0 | agent timeout | - | Infrastructure-contaminated timeout |
| `video-processing` | 0.0 | completed | $0.20851348 | Task solution passed 3/5 verifier checks; frame boundaries were wrong |
| `winning-avg-corewars` | - | Daytona setup error | - | Unscored: connection reset during agent installation |

## Interpretation

The host sleep did not terminate the overall run: Harbor finalized all 19 trial
directories and Autobench finalized a complete, non-partial record. It did make
this batch unsuitable for clean latency analysis and contaminated four trial
records through network loss, timeout, or missing remote result capture.

The default bounded Pydantic tool-retry change was validated by
`circuit-fibsqrt`: the task recovered from the malformed tool call that had
aborted its earlier attempt and received reward `1.0`.

These results are useful engineering evidence for the Kedi harness, but the
61.1% scored rate is not a full Terminal-Bench 2.1 score and should not be
compared directly with five-trial leaderboard submissions.
