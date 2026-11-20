# 3_modeling - P141: Asks how to minimise inference cost for the project model
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P141. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

[

<pasted_content id="18fa">
how to minimis inference cost


Minimise inference cost by reducing tokens processed, model size/quality tier, and idle hardware—then measure quality and latency after every change. The biggest wins are usually prompt/context trimming, caching, routing easy work to smaller models, and batching.

Start with measurement
Track cost per feature, model, request type, and user before optimizing. Record input/output tokens, cache-hit rate, latency (especially P95/P99), error rate, and a task-quality metric; otherwise you cannot tell whether a cheaper setup is acceptable.

text
cost_per_request = (input_tokens * input_price) + (output_tokens * output_price)
For self-hosted models, track GPU-hours, tokens/sec, concurrency, and utilization instead.

Reduce tokens first
This is usually the lowest-risk, highest-return change.

Remove boilerplate, repeated examples, and unused tool schemas from prompts.

Summarize or compress long conversation history instead of resending it verbatim.

In RAG, retrieve fewer and more relevant chunks; tune chunk size, top-k, reranking, and deduplication.

Cap output length and require structured, concise responses.

Prefer deterministic extraction or rule-based handling for simple requests.

Example: if a RAG prompt sends 20 chunks but only 3 materially affect the answer, reducing to 3–5 chunks can cut most of the input-token cost without changing the task.

Cache aggressively
Cache exact responses for stable queries, and use provider prompt caching for repeated prefixes such as system instructions, tool definitions, and reference documents. Prompt caching avoids reprocessing unchanged context on each request.

Use semantic caching only when near-duplicate questions can safely share an answer; otherwise it can return plausible but wrong results.

Route by difficulty
Use a small, cheap model for classification, formatting, extraction, simple Q&A, and routine agent steps. Escalate to a larger model only when confidence is low, the task is complex, or validation fails.

A simple cascade:

text
cheap model -> confidence check / validator -> large model if needed
Keep a small evaluation set per task so routing changes do not silently degrade output quality.

Optimize the serving stack
For self-hosted inference, use a production server with continuous or dynamic batching, paged KV-cache management, and efficient attention implementations. These increase requests served on the same hardware and reduce cost per request.

Lever	What it improves	Main tradeoff
Dynamic/continuous batching	GPU utilization and throughput	Higher queueing latency if over-batched
Quantization	Memory use and hardware cost	Possible quality loss; validate on your data
Pruning/distillation	Compute and memory needs	Requires careful quality evaluation
Right-sized GPUs	Idle-capacity spend	Too-small instances can hurt latency
Autoscaling	Idle spend during low traffic	Needs good load/queue metrics
Quantization, pruning, and smaller/distilled models reduce memory and compute, but should be accepted only after measuring accuracy on representative workloads.

Match deployment to traffic
Use the cheapest execution mode that still meets the latency requirement:

Real-time endpoint: predictable, latency-sensitive traffic.

Serverless/autoscaled endpoint: spiky traffic; avoids paying for idle capacity.

Batch API/job: offline, latency-insensitive workloads.

Async queue: large documents, media processing, and background agent jobs.

Scale on queue depth or batch pressure—not GPU utilization alone—so capacity tracks actual request load.

Add guardrails
Set per-feature and per-user spending limits, especially for agent loops where a failed tool call can trigger repeated expensive generations. Alert on token spikes, retry storms, low cache-hit rates, and unusually long outputs.

Practical order
Instrument cost and quality.

Trim prompts, context, and output.

Add exact and prefix/prompt caching.

Route simple work to smaller models.

Move offline jobs to batch/async processing.

Quantize or distill only after quality validation.

Enable batching, right-size hardware, and autoscale.

Continuously evaluate cost, latency, and output quality.

For a local AI harness, begin with small-model routing + trimmed retrieval + prompt caching; add quantization and a continuous-batching server only once you have a quality benchmark and a real traffic profile.

i meant for models like mlp cnn and others


For MLPs, CNNs, and other conventional neural networks, minimize inference cost by reducing compute per input, memory traffic, and wasted hardware time. The best sequence is: profile first, then reduce input work, use a compiled/runtime-optimized deployment, and only then apply compression techniques.

Cost drivers
For a CNN, cost is dominated by convolution compute and image resolution; for an MLP, it is dominated by matrix multiplications and hidden-layer width. For both, memory bandwidth, batching, and operator overhead can matter as much as FLOPs.

text
Approximate CNN cost ∝ input_resolution × channels × kernel_size × output_channels
Approximate MLP cost ∝ input_size × hidden_width + hidden_width² × depth
Highest-value changes
Change	Typical effect	Risk
Lower input resolution / crop	Large compute reduction for CNNs	Accuracy loss; validate
Reduce channels, layers, or MLP width	Fewer parameters and FLOPs	Accuracy loss
FP16/BF16 inference	Often roughly halves memory traffic vs FP32	Minor numerical risk
INT8 quantization	Smaller model and faster inference on supported hardware	Calibration/accuracy risk
ONNX graph optimization	Removes redundant ops, fuses nodes	Usually low risk
TensorRT / OpenVINO / Core ML	Kernel selection, fusion, hardware-specific execution	Build/deployment complexity
Batch requests	Better hardware utilization	Higher latency for individual items
Cache repeated preprocessing/results	Avoids duplicate work	Stale results if inputs change
TensorRT supports mixed precision including FP16, BF16, FP8, and INT8, and compiles models into engine artifacts optimized for a specific deployment configuration.

Recommended order
Profile before changing the model. Measure latency, throughput, GPU/CPU utilization, memory use, preprocessing time, and accuracy on representative inputs. PyTorch provides profiling and optimization guidance for this purpose.

Reduce preprocessing and input size. For CNNs, use the smallest resolution that preserves task accuracy; avoid unnecessary resizing, normalization, color conversion, or repeated decoding. For an MLP, remove unused features and reduce feature dimensionality where possible.

Export to ONNX and optimize the graph. ONNX Runtime can rewrite the computation graph, merge nodes, and eliminate redundancies before quantization.

Use FP16/BF16 first. It is usually the safest first precision reduction: TensorRT can execute layers in FP16/BF16 and generally trades a small accuracy risk for performance gains.

Try INT8 only with calibration. Use a representative calibration set, then compare accuracy against the FP32/FP16 baseline. If INT8 degrades quality, consider quantization-aware training rather than accepting the loss. TensorRT specifically recommends representative calibration data for INT8.

Compress only if needed. Pruning removes unimportant weights or structures; distillation trains a smaller student model to match a larger teacher. These can reduce size and accelerate inference, but require retraining or fine-tuning and careful validation.

Deploy with batching. Batch independent inputs when latency permits. For TensorRT, batch sizes that are multiples of 32 can achieve better Tensor Core utilization for FP16 and INT8 matrix-multiply workloads.

Model-specific tactics
CNNs
Use smaller input images, fewer channels, depthwise/separable convolutions, or a smaller backbone if accuracy permits.

Fuse convolution, bias, activation, and normalization where the runtime supports it.

Avoid Python-side per-tensor operations; keep the full preprocessing/inference pipeline in the optimized runtime.

For object detection or segmentation, consider reducing output resolution and using efficient postprocessing.

MLPs
Reduce hidden width and depth before trying exotic optimizations; an MLP’s cost grows quickly with layer width.

Fuse linear layers, activations, and normalization where supported.

Use FP16/BF16 or INT8 for weight-only or full integer inference where accuracy allows.

For many small requests, batch them; for one-off requests, avoid oversized batches that increase latency.

Small models
Do not over-optimize tiny models. If a model takes only a few milliseconds, framework startup, data transfer, preprocessing, and synchronization may dominate. In that case, reduce host-device copies, use persistent buffers, compile once, and batch requests rather than shrinking the network further.

Minimal deployment path
For a PyTorch CNN/MLP on NVIDIA hardware:

text
PyTorch model
  -> export ONNX
  -> ONNX Runtime graph optimization
  -> FP16 TensorRT engine
  -> benchmark accuracy + latency
  -> INT8 calibration only if needed
TensorRT accepts models from PyTorch and ONNX, supports dynamic input shapes, and applies hardware-specific optimizations such as kernel selection and layer fusion.

Validate every change
Keep an evaluation set and enforce thresholds before deployment:

Accuracy/metric drop within your accepted budget.

P50/P95/P99 latency within target.

Throughput at expected concurrency.

Memory footprint and peak allocation.

Numerical checks for NaN/Inf values after precision changes. TensorRT recommends validating layer outputs and comparing against a reference runtime such as ONNX Runtime.

For most practical projects, input-size reduction + ONNX optimization + FP16 + batching gives the best cost reduction per unit of engineering effort; INT8, pruning, and distillation are second-stage optimizations.

consider all the machine leraning algorithms not ust mlp and cnssn


For all ML algorithms, speed depends on the model family: neural networks benefit from GPU kernels and precision reduction, while tree models, linear models, SVMs, k-NN, clustering, and classical pipelines benefit more from compact data structures, vectorization, fewer features, and native/compiled inference.

Universal optimizations
These apply to nearly every model:

Reduce input features: remove irrelevant columns, use feature selection, or reduce dimensionality.

Use compact numeric types: float32 instead of float64; integer/category codes instead of strings.

Use sparse matrices for high-dimensional sparse data such as text or one-hot features.

Batch predictions: predict many rows at once rather than calling predict() in a loop.

Avoid repeated preprocessing: fit scalers, encoders, and vectorizers once; cache transformed inputs.

Export to a native runtime: ONNX Runtime, Treelite, or a compiled model can reduce Python overhead and improve portability.

Cache results: memoize identical feature vectors or repeated predictions.

Parallelize independent requests, but avoid oversubscribing CPU cores.

scikit-learn notes that ONNX artifacts can run without a Python environment and often need less RAM, while joblib supports memory mapping for efficient loading across processes.

Algorithm-specific tactics
Algorithm family	Main inference cost	Best speed levers
Linear/logistic regression	Dot products	Sparse inputs, fewer features, float32, vectorized batch prediction, ONNX
SVM	Kernel evaluations	Linear SVM when possible, fewer support vectors, precomputed kernels, batch prediction
k-NN	Distance to many training points	Smaller training set, dimensionality reduction, approximate nearest-neighbor index, vectorized distance computation
Decision trees	Tree traversal	Fewer/shallower trees, compact node arrays, native runtime, batch prediction
Random forest	Many tree traversals	Fewer trees, lower depth, parallel threads, compact serialization, ONNX/Treelite
Gradient boosting	Many tree traversals	hist tree method, fewer trees, lower depth, compact model format, native predictor
Naive Bayes	Simple probability arithmetic	Sparse matrices, vectorization; usually already fast
Clustering	Distance computations	Smaller k, approximate nearest neighbors, mini-batch variants, precomputed centroids
PCA/UMAP/t-SNE	Matrix operations or neighbor search	Fit once, cache embeddings, use approximate nearest neighbors, reduce dimensions
Neural networks	Matrix multiplication/convolutions	GPU, FP16/BF16, quantization, fusion, compilation, batching
Transformers/LLMs	Attention and large matrix multiplications	KV cache, quantization, batching, speculative decoding, optimized runtimes
Tree-based models
For XGBoost, LightGBM, CatBoost, and random forests, inference is usually dominated by traversing many trees. Reduce the number of trees, maximum depth, and number of leaves; use histogram-based training/inference where supported.

XGBoost’s hist method uses histogram-based approximate greedy splitting and is faster than exact tree construction; its QuantileDMatrix is designed to save memory for histogram-based methods.

python
model = xgb.XGBClassifier(
    n_estimators=200,       # fewer trees = faster
    max_depth=6,            # lower depth = faster traversal
    tree_method="hist",
    n_jobs=4
)
For deployment, convert boosted-tree models to a compact native format such as Treelite or ONNX where supported. Avoid Python-level loops over individual trees or samples.

Linear models and SVMs
For linear/logistic regression, ridge/lasso, and linear SVMs, inference is mostly matrix multiplication:

text
prediction = X @ weights + bias
Store X as float32 and, when appropriate, scipy.sparse.csr_matrix.

Predict in batches: model.predict(X_batch), not one row at a time.

Use SGDClassifier, LinearSVC, or logistic regression rather than kernel SVM when a linear boundary is sufficient.

For kernel SVMs, reduce support vectors or use approximate kernel methods; kernel evaluation can become expensive as support-vector count grows.

Export the model to ONNX with sklearn-onnx for lower-overhead scoring.

k-NN and similarity search
k-NN cost grows with training-set size and feature dimensionality:

text
cost ∝ n_training_samples × feature_dimension
Use:

PCA, random projections, or learned embeddings to lower dimensionality.

Approximate nearest-neighbor libraries such as FAISS, HNSW, Annoy, or ScaNN.

Product quantization or other vector compression for very large embedding collections.

A smaller candidate set via coarse filtering before exact reranking.

GPU batching for large embedding searches.

This is usually much more effective than optimizing the classifier itself.

Clustering and embeddings
For k-means, GMM, DBSCAN-like methods, and embedding retrieval:

Precompute centroids, cluster assignments, and distance matrices where valid.

Use mini-batch k-means for streaming or very large datasets.

Use approximate nearest-neighbor search for assignment and retrieval.

Store embeddings as float32 or quantized vectors, not Python lists.

Cache embeddings for unchanged documents, images, or users.

For retrieval systems, the expensive part is often the vector search rather than the final classifier.

Neural networks beyond MLP/CNN
For RNNs, transformers, diffusion models, GNNs, and other deep models:

Model type	Important optimizations
RNN/LSTM/GRU	Use cuDNN-backed implementations, avoid Python loops, batch sequences, truncate/pack sequences
Transformer	KV cache, FlashAttention-style kernels, FP16/BF16, batching, speculative decoding, quantization
Diffusion model	Fewer denoising steps, distilled scheduler, cached VAE/text encoder, FP16, batching
GNN	Sparse matrix kernels, neighbor sampling, graph partitioning, batching subgraphs
Autoencoder	Smaller latent dimension, quantization, cached encodings
Object detection	Smaller input resolution, efficient NMS, batch inference, quantization
Hugging Face Optimum supports ONNX export, graph optimization, and quantization for Transformers and related model families; ONNX Runtime can then execute the optimized artifact on supported hardware.

Deployment choices
Situation	Best approach
Small tabular model, low traffic	Keep scikit-learn/joblib; batch requests; use float32
Large random forest/boosted model	ONNX or Treelite; fewer/shallower trees
High-dimensional sparse text	Sparse CSR matrices + linear model or lightweight tree model
Millions of embeddings	FAISS/HNSW + quantized vectors
GPU vision model	ONNX + TensorRT, FP16, batching
CPU-only neural model	ONNX Runtime + dynamic INT8 quantization
Real-time API	Fixed-shape model, warm process, batching or CUDA Graphs
Offline bulk scoring	Large batches, parallel workers, queue-based processing
Measure the right thing
Before optimizing, split latency into stages:

text
total_latency =
  feature_extraction
+ preprocessing
+ model_forward
+ postprocessing
+ serialization/network overhead
A common mistake is optimizing a model that already takes 2 ms while preprocessing takes 80 ms. Profile each stage, optimize the largest one, and validate that accuracy, calibration, ranking quality, or task-specific metrics remain acceptable.

For most classical ML systems, the fastest practical path is: compact features + sparse arrays + batch prediction + native ONNX/Treelite deployment. For deep models, it is: right-sized architecture + FP16/BF16 + graph/runtime optimization + batching + quantization.

how to speed up xgboost inference
</pasted_content id="18fa">

]

## Response

This repo does not use XGBoost, so the tree-model advice in the pasted text does not apply here. The project's model is a small CNN. It is exported to ONNX and run with ONNX Runtime in `export/predict.py`.

#### Steps for this model

1. **Measure first.** Time the preprocessing, the model call and the postprocessing separately at batch size 1. The paste is right that a small model can be dominated by overhead, so the split matters more than the model call alone.
2. **Create the session once.** Load the ONNX Runtime session at startup and reuse it. Loading it per request would dominate the cost.
3. **Warm up.** Run a few dummy inputs before timing, so the first slow call does not skew the numbers.
4. **Check the browser path.** The in-browser version (task T86) has its own bottleneck. Measure it there before optimising the Python path.
5. **Leave precision alone for now.** FP16 and INT8 are not worth it for a model this small. Any change would need the accuracy check again, which means touching the frozen results.

#### What is missing

I have not measured any of this, so I have no timings for the current model. Tell me whether you want me to time the Python path and the in-browser path.

##### Why these steps, for this model
- The model is a small CNN, and the repo exports it to ONNX and runs it with ONNX Runtime in `export/predict.py` (checked in the repo). So the advice on ONNX Runtime applies, and the tree-model and XGBoost advice in the paste does not.
- Creating the session once matters because a small model's cost is often dominated by setup and overhead rather than the forward pass. Measuring each stage first confirms that before any change.
- The in-browser path (T86, the public site with in-browser inference) is a separate runtime with its own bottleneck. It is verified in the commit list, but its speed is not measured here.
- Precision reduction (FP16, INT8) is deferred. The model is small, so the gain is likely small, and any change would need a new accuracy check on the frozen results.

##### Consequences
- No change should be made until the Python and browser paths are both timed, because the bottleneck may be in either one.
- Any optimisation that changes the model's outputs would require re-validating accuracy, which touches the frozen results and the reproducibility rules.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
