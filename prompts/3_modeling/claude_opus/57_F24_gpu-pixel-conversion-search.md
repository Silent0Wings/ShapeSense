# 3_modeling - F24: Converting pixels on the GPU would have changed every result. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F24 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f24) · Record: [F24](../inferred_prompts.md#f24)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Why does moving image preprocessing (uint8 to float conversion, resampling) from the CPU to the GPU change numerical results? Search for sources on floating-point differences between CPU and GPU, cuDNN nondeterminism and how to keep a pipeline bit-for-bit reproducible.

## Response

### Well established

- **IEEE 754 division is correctly rounded, wherever it runs.** The standard requires each basic operation to return the exact result rounded to the destination format ([Goldberg 1991, ACM Computing Surveys](https://docs.oracle.com/cd/E19957-01/816-2464/ncg_goldberg.html)). NVIDIA's [floating-point whitepaper](https://docs.nvidia.com/cuda/floating-point/) states that the basic IEEE operations give the same results "using any microprocessor, CPU or GPU". So a CPU/GPU difference in a simple divide means **a different operation ran**, not that the hardware is wrong.
- **PyTorch's CUDA kernel doesn't actually divide by a scalar.** The CUDA true-divide kernel says, in a code comment quoted in [pytorch/pytorch#114165](https://github.com/pytorch/pytorch/issues/114165): "if the second operand is a CPU scalar, compute a * reciprocal(b). Note that this may lose one bit of precision compared to computing the division." That issue (closed June 2024 by commit 2fa6f80) extended the same optimisation to `_foreach_div_`. A [forum report](https://discuss.pytorch.org/t/pytorch-1-6-0-wrong-true-divide-on-cuda/91990) shows it flipping a `ceil` result between CPU and CUDA.
- **Order and fusion change results too.** The whitepaper shows that a fused multiply-add (one rounding) and a separate multiply then add (two roundings) give different answers, and that `(A+B)+C ≠ A+(B+C)` in floating point ([NVIDIA](https://docs.nvidia.com/cuda/floating-point/)). Resampling kernels that sum weighted neighbours in a different order or with FMA will differ from a CPU implementation in the last bits.
- **PyTorch doesn't promise CPU/GPU equality.** The [reproducibility notes](https://docs.pytorch.org/docs/2.15/notes/randomness.html) say "Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms", and that CPU and GPU can differ even with identical seeds. Within the GPU, `torch.backends.cudnn.benchmark=False` makes the algorithm choice deterministic, and `torch.use_deterministic_algorithms(True)` or `cudnn.deterministic=True` stops convolution algorithms from varying between runs (same page).

### Single reports

A forum reader of the CUDA source reports that the reciprocal shortcut applies only when the divisor is a CPU scalar. A tensor divisor gets true division ([discussion 184858](https://discuss.pytorch.org/t/large-difference-in-results-between-cpu-and-cuda/184858)). I didn't verify this against the current kernel source.

### Reasoning, plus one check I ran

The ShapeSense CPU path is `images_u8.astype(np.float32) / 255` (`src/stage4_train/sampling.py`, `to_float`), a correctly rounded float32 divide. I compared it in NumPy with float32 multiplication by `float32(1/255)`, which is what the CUDA scalar path computes, over all 256 pixel values:

```
v = np.arange(256, dtype=np.float32)
(v / np.float32(255) != v * np.float32(1/np.float32(255))).sum()   # -> 126
```

The answer is **126 of 256**, exactly the number in the record. That strongly suggests the reciprocal shortcut is the mechanism. A one-ulp change in the input pixels then spreads through training (different gradients, different weights), so every downstream number would change, even though each change is tiny.

### Keeping it bit-for-bit

The documented tools are: run the same operation on both sides, or precompute. A 256-entry lookup table of the exact CPU float32 values, indexed by the uint8 pixel on the GPU, reproduces the CPU result exactly, because a gather does no arithmetic. Add the deterministic cuDNN settings above, fixed seeds, and a test that compares batches bit for bit.

### How it applies to ShapeSense

All five arms take the same `to_float` input, so changing the conversion would have moved every arm's macro F1 at once. That would break comparability with the earlier iterations and the frozen results, even if the arm-to-arm conclusions survived. GPU resampling (warps, rotation) would bring the same kind of difference, plus differences in summation order. That is why augmentation stays on the CPU here.

## Validation

The record says dividing by 255 on the GPU rounds 126 of the 256 pixel values differently from the CPU. The search found the mechanism: PyTorch CUDA computes `a * (1/b)` for a scalar divisor, by design and documented in the kernel comment. My local check reproduces the exact count of 126. The literature agrees with the record, and it adds the cause the record didn't state.

## Our decision

The project measured the difference before adopting the outside recommendation, rejected the plain GPU divide, and used a lookup table of the exact CPU values. The findings support that fully. A related caution: any future GPU-side resampling would need the same equivalence check. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## IEEE 754 Reciprocal Multiplication & Bit-Exact Normalization (`F24`)

### Metadata & Lineage

* **Entry ID / Type:** `F24` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis + NumPy verification)
* **Primary Artifacts:** `src/stage4_train/sampling.py` (`to_float`)

### Exact Floating-Point Mechanism Behind the `126/256` Pixel Discrepancy

1. **IEEE 754 Compliance vs. Compiler Reciprocal Strength Reduction:** While IEEE 754 guarantees correctly rounded division on both CPU and GPU hardware (Goldberg, ACM Computing Surveys 1991; NVIDIA Floating-Point Whitepaper), PyTorch's CUDA `true_divide` kernel optimizes scalar divisors by computing `a * reciprocal(b)` (`pytorch/pytorch#114165`), trading 1 ULP of precision for throughput.
2. **Exact Reproduction Across `uint8` Domain $[0, 255]$:**

```python
v = np.arange(256, dtype=np.float32)
diff_count = (v / np.float32(255) != v * np.float32(1 / np.float32(255))).sum()
# diff_count == 126 (exact match to ShapeSense empirical audit)
```

3. **Chaotic Gradient Divergence & Lookup-Table Solution:** A 1-ULP shift in `126 / 256` input intensities perturbs first-layer activations, batch-norm statistics, and downstream AdamW updates across `2,940` steps—breaking cross-iteration comparability. Replacing GPU scalar division with a 256-entry precomputed `float32` lookup table (`lut[images_u8]`) performs zero floating-point arithmetic on device, achieving bit-for-bit parity with CPU `to_float` while keeping geometric resampling on CPU to avoid FMA/reduction-order drift.

