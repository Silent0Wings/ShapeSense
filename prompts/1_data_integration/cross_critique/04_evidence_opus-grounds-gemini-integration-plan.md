# 1_data_integration - Opus 5.5 grounds Gemini 4 Neon's integration plan in citable sources

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Critiqued output: Gemini 4 Neon (its draft plan, linked in the Response)
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-10-19
- Owner: 40256377
- Worksheet entries: I03, I06
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.
-  [I03](../claude_opus/06_I03_global-phash-grouping-and-group-split.md), [I03](../gemini_4_neon/05_I03_global-phash-hamming-and-giant-groups.md), [I06](../claude_opus/09_I06_cross-source-standardization-and-outline-redraw.md), [I06](../gemini_4_neon/08_I06_standardization-and-holdout-rebuild-recovery.md)

## Prompt (inferred, not saved)

> _Inferred:_ Plan 02 describes the integration pipeline without citations. Find real, citable sources for each technique and correct anything unsupported.

## Response (saved output, verbatim)

### `research_notes/Shape dataset integration and tooling/integration_techniques.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Integration Techniques for Heterogeneous Image Datasets

## Dimension/aspect-ratio handling: what is the standard, citable approach for resizing images of different native resolutions/aspect ratios to a fixed size without distorting shape geometry?

### Takeaway
The standard, widely documented technique is "letterboxing" — scale the image so its longest side matches the target size (preserving aspect ratio), then pad the remaining space with a constant fill color to reach the final fixed square/rectangle. This is implemented directly in Albumentations as a two-step `LongestMaxSize` + `PadIfNeeded` pipeline (or the single `LetterBox` transform), and is distinct from a naive non-aspect-preserving resize (e.g., a tuple resize in torchvision), which does distort shape geometry.

### Cited Findings
- Albumentations' `LetterBox` transform is explicitly documented as the "YOLO letterbox" technique, described as equivalent to chaining `LongestMaxSize` + `PadIfNeeded`; it scales an image to fit a target canvas and pads the remainder, with a default pad fill value of 114 (the YOLO convention) — [Albumentations LetterBox docs](https://albumentations.ai/explore/transform/LetterBox/docs/)
- The documented standard classification/detection recipe is `Compose([LongestMaxSize(max_size=1024), PadIfNeeded(min_height=1024, min_width=1024)])`, which rescales the image so its longest side hits the target (keeping aspect ratio) and then pads to reach the fixed square canvas — [Albumentations Resize API reference](https://albumentations.ai/docs/api-reference/albumentations/augmentations/geometric/resize/); [Albumentations LongestMaxSize docs](https://explore.albumentations.ai/transform/LongestMaxSize/docs)
- `LongestMaxSize` does not crop; because it only rescales, "the resulting image may be smaller than specified in both dimensions," which is precisely why a follow-up padding step (`PadIfNeeded`) is the documented companion transform — [Albumentations LongestMaxSize docs](https://explore.albumentations.ai/transform/LongestMaxSize/docs)
- Small images are upscaled, not just shrunk, by these transforms when the longest side is below `max_size` (scale factor > 1.0) — [Albumentations LongestMaxSize docs](https://explore.albumentations.ai/transform/LongestMaxSize/docs)
- In torchvision, passing a single integer to `Resize` scales the image so the **shorter** edge matches that integer while the longer edge scales proportionally (aspect-preserving), whereas passing a `(height, width)` tuple forces an exact output shape and therefore **distorts** the original proportions — confirmed via a PyTorch forum discussion of an example (1024×512 → `Resize(256)` → 512×256) — [PyTorch Discuss: "Resize images while maintaining the aspect ratio"](https://discuss.pytorch.org/t/resize-images-while-maintaining-the-aspect-ratio/158329)
- torchvision's `Pad` transform only adds borders of a size you must compute yourself — it does not rescale — so the documented aspect-preserving pattern with torchvision's built-in transforms is: `Resize(size=N)` (int form, scales so the limiting dimension matches N) followed by a manually computed `Pad` to reach the final fixed square — [PyTorch Discuss: "How to resize and pad in a torchvision.transforms.Compose()?"](https://discuss.pytorch.org/t/how-to-resize-and-pad-in-a-torchvision-transforms-compose/71850)
- Other ecosystem implementations document the same letterbox pattern outside Python/Albumentations: AMD's Vitis Vision Libraries describe a hardware letterbox routine that "pads zeros when needed to keep the aspect ratio," used "typically in the preprocessing stage of machine learning pipelines" — [AMD Vitis Libraries 2024.2, Letterbox](https://docs.amd.com/r/2024.2-English/Vitis_Libraries/vision/overview.html_5_7)

### Inferences
- The letterbox pattern (aspect-preserving resize + constant-color padding) is the de facto cross-framework/cross-language standard for this problem (seen identically in Albumentations, AMD Vitis, SiMa.ai NEAT, PhotonVision, and go-rknnlite implementations), even though no single ITU/ISO-style formal "standard" document defines it — it is a convention that originated in and is most authoritatively documented through object-detection pipelines (notably YOLO, reflected in Albumentations naming it "YOLO letterbox" and defaulting to YOLO's pad value of 114).
- For a pure image-classification use case (no bounding boxes to remap), the `LongestMaxSize` + `PadIfNeeded` (or `LetterBox`) Albumentations pipeline, or the equivalent manual `Resize(int) + Pad` in torchvision, are the two most citable, documentation-backed implementations to reference.

### Gaps
- I did not find a single authoritative academic paper that formally names/defines "letterboxing" as a term of art (it is an informal but near-universal convention, not an ITU/ISO-style standard) — the strongest citations are official library documentation rather than a primary research paper.

## Grayscale conversion: what is the standard formula/standard for converting RGB images to grayscale, and which is more commonly used in modern computer vision libraries?

### Takeaway
Both OpenCV and Pillow use the legacy ITU-R BT.601 luma weights (Y = 0.299R + 0.587G + 0.114B) as their default single-channel grayscale conversion, even though BT.709 (0.2126R + 0.7152G + 0.0722B) is the modern HDTV/sRGB-consistent standard; BT.601 remains the de facto default in mainstream CV libraries for legacy/compatibility reasons.

### Cited Findings
- OpenCV's official color-conversions documentation gives the RGB[A]-to-Gray formula as `Y ← 0.299·R + 0.587·G + 0.114·B`, and lists `COLOR_BGR2GRAY` alongside the RGB variants (same weights, reversed channel order for BGR-ordered images from `imread`) — [OpenCV 4.x Color Conversions docs](https://docs.opencv.org/4.0.0/de/d25/imgproc_color_conversions.html)
- OpenCV's own Q&A documentation confirms images loaded via `imread` are in BGR channel order by default, so `COLOR_BGR2GRAY` (not `RGB2GRAY`) is the correct conversion for standard-loaded OpenCV images — [OpenCV Answers Q&A](https://answers.opencv.org/answers/121276/revisions)
- Pillow's `Image.convert('L')` documentation states it uses the "ITU-R 601-2 luma transform," with the exact formula `L = R * 299/1000 + G * 587/1000 + B * 114/1000` — [Pillow Image.convert documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.convert)
- The torchvision R documentation for `transform_rgb_to_grayscale` similarly describes the "ITU-R 601-2 luma transform" with decimal weights 0.2989, 0.5870, 0.1140 — [torchvision R docs](https://search.r-project.org/CRAN/refmans/torchvision/html/transform_rgb_to_grayscale.html)
- BT.709 (HDTV) luma weights are documented as 0.2126 (R), 0.7152 (G), 0.0722 (B), matching IEC 61966-2-1 — [V4L2 colorspace documentation](https://v4l-test.sourceforge.net/spec/x2123.htm); [Wikipedia: Luma (video)](https://en.wikipedia.org/wiki/Luma_(video))
- BT.601 (SD) luma weights are 0.299 (R), 0.587 (G), 0.114 (B) — same V4L2 reference — [V4L2 colorspace documentation](https://v4l-test.sourceforge.net/spec/x2123.htm)
- MATLAB's `im2gray` uses more precise BT.601-7-derived weights (0.298936, 0.587043, 0.114020), stated by MathWorks to be "identical to those used to calculate luminance (E'y) in Rec. ITU-R BT.601-7" after rounding — indicating small numerical differences are expected between libraries even when nominally using "the same" standard — [MathWorks im2gray documentation](https://www.mathworks.com/help/matlab/ref/im2gray.html)
- Current ITU reference document versions are BT.601-7 and BT.709-6 — [Imatest Luminance documentation](https://www.imatest.com/docs/luminance/)

### Inferences
- The fact that both OpenCV and Pillow — the two most widely used Python imaging/CV libraries — default to BT.601 weights rather than BT.709 strongly supports citing BT.601 as the "commonly used in modern CV libraries" default, even though BT.709 is technically the more modern broadcast standard matching modern (sRGB/HDTV) primaries.
- For the Phase-1 report, it is defensible to state: "modern CV libraries (OpenCV, Pillow) default to the legacy ITU-R BT.601 luma formula for grayscale conversion rather than the newer BT.709 formula," with the above citations.

### Gaps
- I did not independently verify PyTorch's own grayscale conversion weights from PyTorch's own official docs (only found via the torchvision R-bindings documentation, a secondary mirror of the same underlying C++/Python implementation) — worth a follow-up check of `torchvision.transforms.functional.rgb_to_grayscale` in the primary PyTorch docs if higher precision is needed.
- I was not able to directly fetch the primary ITU-R BT.601/BT.709 recommendation PDFs themselves (fetch blocked); all figures above are corroborated by multiple independent secondary technical references (V4L2 spec, Wikipedia, Imatest, MathWorks) rather than the ITU source documents directly.

## Contrast/polarity normalization: are there citable approaches for detecting and normalizing "background vs foreground" polarity across a mixed image dataset?

### Takeaway
There is no single named "standard" for foreground/background polarity normalization, but there are two concrete, citable, documented mechanisms: (1) histogram/dominant-intensity-based polarity detection (the background typically occupies the majority of pixels, so the dominant intensity reveals which side is background), and (2) explicit "foreground polarity" parameters in binarization tooling (e.g., MATLAB's `imbinarize`), which can be adapted as a design pattern even outside MATLAB.

### Cited Findings
- MATLAB's `imbinarize` function has a documented `ForegroundPolarity` name-value argument (for adaptive thresholding) with values `"bright"` (default; foreground brighter than background) or `"dark"` (foreground darker than background) — this is an official, citable example of a library explicitly exposing polarity as a controllable parameter in binarization — [MathWorks imbinarize documentation](https://www.mathworks.com/help/images/ref/imbinarize.html)
- Otsu's thresholding method (widely implemented, e.g., OpenCV's `cv2.threshold` with `THRESH_OTSU`) automatically computes an optimal threshold by minimizing intra-class variance on the image histogram, and works best on bimodal histograms (clear foreground/background separation); pixels above the computed threshold are conventionally treated as foreground, below as background — [Roboflow Image Threshold block docs](https://docs.roboflow.com/workflows/blocks/blocks/classical-computer-vision/image-threshold)
- Threshold-type libraries commonly expose both a standard binary mode and an explicit inverse mode (e.g., `binary` vs `binary_inv`, or OpenCV's `THRESH_BINARY` vs `THRESH_BINARY_INV`), allowing polarity to be flipped post-threshold — [Roboflow Image Threshold block docs](https://docs.roboflow.com/workflows/blocks/blocks/classical-computer-vision/image-threshold); [Augelab Image Threshold docs](https://docs.augelab.com/function-blocks/image-transformations/color-filters/image-threshold)
- A reference on binary image conventions notes: "the object is conventionally white and the background black, but polarity can flip depending on the source," and that "some morphological operators assume a certain polarity of the binary input image" — meaning downstream processing can silently fail or invert results if polarity is not normalized first — [HIPR2 Binary Images reference, University of Edinburgh](https://homepages.inf.ed.ac.uk/rbf/HIPR2/binimage.htm)
- A practical mitigation documented in OCR tooling: reversing (inverting) colors is recommended specifically because "recognition accuracy may suffer with white or light text on a black or dark background," and inversion "can be greatly improved by reversing the colors" — demonstrating polarity normalization as a standard OCR/CV preprocessing step, not merely a cosmetic choice — [Aspose.OCR color inversion documentation](https://docs.aspose.com/ocr/java/invert)
- Leptonica's adaptive background normalization (estimating a background map and dividing by it) is documented as a related but distinct technique for handling varying illumination, which can be combined with (but is not the same problem as) polarity correction — [Leptonica adaptmap documentation (metacpan mirror)](https://metacpan.org/pod/Image::Leptonica::Func::adaptmap)

### Inferences
- A defensible, citable engineering approach for a mixed dataset is: compute a simple polarity signal per image (e.g., mean intensity of border pixels, or which histogram mode has more pixels — background is typically the majority class) and invert any image whose detected polarity disagrees with the chosen dataset convention, drawing on the `ForegroundPolarity`-style pattern from MATLAB's `imbinarize` and the inverse-threshold-mode pattern common to thresholding libraries.
- This is best framed in the report as an adapted/engineered technique inspired by documented binarization-polarity controls, rather than citing it as a single formally named "polarity normalization standard" — no such single standard exists in the literature I found.

### Gaps
- I could not confirm the specific claim (from an initial search summary) that an arXiv paper on handwritten-numeral clustering (arXiv:2012.07599, Rahat-uz-Zaman & Hye, 2020) describes histogram-based polarity detection for mixed black-on-white/white-on-black datasets — when I fetched the actual abstract, it describes a Siamese-network similarity/clustering method and does not mention polarity or histogram-based background/foreground detection at all. This appears to have been a hallucinated/misattributed claim from an earlier search summary and should NOT be cited in the report. I recommend NOT using that paper as a source for this topic.
- I did not find a peer-reviewed paper specifically and solely about "cross-dataset polarity normalization" as a named technique; this remains a gap, and the report should present the polarity-normalization approach as an engineering adaptation of documented binarization/thresholding polarity controls rather than citing a dedicated academic standard.

## Deduplication: what is perceptual hashing (pHash) and how is it typically used for near-duplicate image detection across merged datasets?

### Takeaway
Perceptual hashing (pHash) generates a compact fingerprint from an image's low-frequency visual structure (typically via a DCT) such that visually similar images produce similar hashes; near-duplicates are then detected by computing the Hamming distance between hashes and flagging pairs below a threshold. The de facto standard open-source implementation for Python is the `imagehash` library (built on Pillow/numpy/scipy), and the original/foundational reference for the pHash algorithm is Christoph Zauner's 2010 master's thesis.

### Cited Findings
- The Python `imagehash` library (by Johannes Buchner) is built on "PIL/Pillow Image, numpy and scipy.fftpack (for pHash)" and provides `imagehash.phash()` among several hash algorithms (average, perceptual, difference, wavelet, color, crop-resistant hashing) — [imagehash GitHub README](https://github.com/JohannesBuchner/imagehash); [PyPI ImageHash 4.2.1](https://pypi.org/project/ImageHash/4.2.1)
- Near-duplicate detection with `imagehash` works by subtracting two hash objects to get a Hamming distance (e.g., `hash1 - hash2`); the library's own usage example computes this distance and the README states hashes "tell whether two images look nearly identical," with similar inputs producing similar hashes — [imagehash GitHub README](https://github.com/JohannesBuchner/imagehash)
- Hashes can be serialized to strings for storage (`str(hash)`) and restored (`imagehash.hex_to_hash()`) — useful for persisting dedup fingerprints across a merged dataset pipeline — [imagehash GitHub README / docs](https://docsearch.algolia.com/mcp/docs/repo/johannesbuchner/imagehash)
- The library's README explicitly cites only a non-academic source for pHash's algorithmic basis — a blog post by Hacker Factor ("Looks Like It," hackerfactor.com) — and does not itself cite an academic paper for the pHash algorithm specifically (it does cite an IEEE paper, but that is for the separate crop-resistant hashing method, not pHash) — [imagehash GitHub README](https://github.com/JohannesBuchner/imagehash)
- The original, most commonly cited academic/primary reference for the pHash algorithm is Christoph Zauner's 2010 master's thesis, "Implementation and Benchmarking of Perceptual Image Hash Functions" (Fachhochschule Hagenberg, Austria; dated July 2010), hosted at phash.org, which introduces a benchmarking framework ("Rihamark") for perceptual image hash functions — [Zauner thesis PDF, phash.org](https://phash.org/docs/pubs/thesis_zauner.pdf)
- The commonly described pHash algorithm mechanics (per secondary technical summaries corroborating each other): convert to grayscale, resize to a small fixed size (commonly 32×32), apply a Discrete Cosine Transform (DCT), retain the low-frequency top-left block (commonly 8×8 = 64 coefficients), and set each output bit via comparison against the block's median — yielding a 64-bit hash compared via Hamming distance — [Wikipedia: Perceptual hashing](https://en.wikipedia.org/wiki/Perceptual_hashing); summarized similarly across multiple secondary sources found in search but not independently verified against Zauner's primary thesis text in this research pass

### Inferences
- For the Phase-1 report, the most defensible citation chain is: cite the `imagehash` GitHub repository/PyPI package as the concrete tool used for deduplication, and cite the Zauner (2010) thesis as the academic/primary-source grounding for the pHash algorithm concept, while being explicit that the `imagehash` maintainers themselves point to a blog post (not a paper) as their practical reference.
- A typical "merged dataset" dedup workflow,  from documented library behavior: compute `imagehash.phash()` for every image after unifying format/size, group or sort by hash, and flag pairs with Hamming distance below a chosen threshold (the library's own demo script, `find_similar_images`, is described as implementing exactly this grouping behavior).

### Gaps
- I did not fetch or read the full text of the Zauner (2010) thesis itself in this pass — the algorithmic description (32×32 → DCT → 8×8 low-frequency block → median-threshold → 64-bit hash) is corroborated by multiple secondary sources (Wikipedia, third-party technical guides) that agree with each other, but I could not independently confirm this exact parameterization against the primary thesis text. Flagging this as the one point in this section not confirmed against a primary source directly.

## Synthetic data integration: how do modern training pipelines typically integrate on-the-fly synthetic data generation and data augmentation without pre-materializing every variant to disk?

### Takeaway
PyTorch's official pattern is to put all image loading and transformation logic inside a custom `Dataset.__getitem__` method, so each sample (including any synthetic/augmented variant) is generated lazily, on demand, per epoch, rather than precomputed and stored; Albumentations is designed to be called per-sample inside that same `__getitem__`, with its own pipeline (`Compose`) resampling random parameters on every call so each epoch yields different augmented variants without ever writing extra files to disk.

### Cited Findings
- PyTorch's official tutorial ("Writing Custom Datasets, DataLoaders and Transforms") establishes the core pattern: a custom dataset subclasses `torch.utils.data.Dataset` and overrides `__len__` and `__getitem__`; the tutorial explicitly reads lightweight metadata (e.g., a CSV index) in `__init__` but "leave[s] the reading of images to `__getitem__`," noting this "is memory efficient because all the images are not stored in the memory at once but read as required" — [PyTorch official tutorial: Writing Custom Datasets, DataLoaders and Transforms](https://docs.pytorch.org/tutorials/beginner/data_loading_tutorial.html)
- The same PyTorch tutorial documents that the dataset takes "an optional argument `transform` so that any required processing can be applied on the sample," i.e., the transform (which can include augmentation) is applied inside `__getitem__` on each access, not precomputed — [PyTorch official tutorial](https://docs.pytorch.org/tutorials/beginner/data_loading_tutorial.html); companion recipe at [pytorch.org custom_dataset_transforms_loader recipe](https://pytorch.org/tutorials/recipes/recipes/custom_dataset_transforms_loader.html)
- Albumentations' official documentation describes its `Compose` pipeline as a single callable that "applies the contained transforms sequentially to the input data" when called (e.g., `pipeline(image=image)`), and states that each transform's probability `p` is evaluated fresh "on every call," such that "a different subset of the defined transforms might actually be applied" each time the pipeline is invoked — this is the documented mechanism for on-the-fly, non-materialized augmentation — [Albumentations Pipelines documentation](https://albumentations.ai/docs/2-core-concepts/pipelines/)
- Albumentations documentation confirms its randomness is generated per-call via its own internal random generators ("call-local random generators, completely independent from global seeds"), meaning repeated calls to the same pipeline on the same image yield different random augmentations each time by design (unless a seed is explicitly fixed) — [Albumentations Pipelines documentation](https://albumentations.ai/docs/2-core-concepts/pipelines/)
- A PyTorch community discussion corroborates that the `DataLoader` + transform pattern means augmentation is applied fresh on each pass through the data: "each epoch shows a different variant of every item," and this does not create a fixed, larger, pre-materialized dataset (`len(train_loader)` stays constant) — [PyTorch Discuss: Data augmentation in PyTorch](https://discuss.pytorch.org/t/data-augmentation-in-pytorch/7925)
- The alternative — precomputing and saving every augmented variant to disk ahead of time (e.g., via `torch.save`) — is documented in PyTorch community discussion as a recognized but distinct alternative pattern, implying the on-the-fly approach is the more standard/default one for typical augmentation use cases — [PyTorch Discuss: Data augmentation before training](https://discuss.pytorch.org/t/data-augmentation-before-training/92258)

### Inferences
- For a Phase-1 report describing an integration pipeline design, the citable architecture to describe is: a custom `torch.utils.data.Dataset` subclass whose `__getitem__` (a) loads the base image lazily, (b) optionally invokes a synthetic-data generation function for that sample, and (c) passes the result through an Albumentations (or torchvision) `Compose` pipeline — all executed per-access, per-epoch, with no intermediate files written, following the documented PyTorch tutorial pattern plus Albumentations' per-call randomization design.
- Synthetic data generation itself (as opposed to augmentation of real images) is not separately documented as a named PyTorch/Albumentations pattern in the sources found; the clean citation is that it fits the *same* architectural slot as augmentation (inside `__getitem__`, called per-sample, per-epoch) because both are just sample-producing functions from the `Dataset`'s perspective.

### Gaps
- I did not find an official PyTorch or Albumentations document that uses the specific phrase "synthetic data generation" integrated into `Dataset`/`DataLoader`; the inference above (that synthetic generation fits the same `__getitem__` slot as augmentation) is my own architectural inference from the documented Dataset/transform pattern, not a directly cited claim — flagging this so the report writer distinguishes "documented pattern" (augmentation in `__getitem__`) from "inferred extension" (synthetic generation in the same slot).

## Train/test leakage avoidance: what do established ML practices say about excluding synthetic/augmented data from a held-out test set?

### Takeaway
Established ML methodology sources are consistent: data augmentation (and other sample-generating or distribution-fitting operations) must be applied only to the training split, after the train/test split has been made — never to the full dataset before splitting — because doing otherwise leaks augmented/duplicated variants of test-set source images into training (or vice versa), inflating evaluation metrics in a way that does not reflect real-world generalization.

### Cited Findings
- An academic guide on ML pitfalls for researchers states that data augmentation is useful for balancing datasets but "should be applied only to training data," and identifies a more serious problem when augmentation is run on the whole dataset before the train/test split — [Whalen et al./arXiv, "How to avoid machine learning pitfalls: a guide for academic researchers"](https://arxiv.org/pdf/2108.02497)
- A 2025 reproducible case-study dataset (covering tomato disease and rice pest detection tasks) empirically demonstrated that pre-split augmentation caused severe train/test leakage, inflating reported detection metrics (mAP50) by as much as 66 percentage points compared to correctly post-split augmentation — [Mendeley Data, "Towards Reliable Data Augmentation in Machine Learning"](https://data.mendeley.com/datasets/f9k79z29rp/1)
- The same leakage principle is documented for oversampling/synthetic minority techniques: a Towards Data Science explainer states that artificial/duplicate samples created to address class imbalance should be generated only after the train/test split, not before — [Towards Data Science, "Data leakage: what it is and why it causes our predictive systems to fail"](https://towardsdatascience.com/data-leakage-what-it-is-and-why-it-causes-our-predictive-systems-to-fail-4e5ed008489b/)
- The same leakage logic applies to feature scaling and SMOTE: fitting a scaler or running SMOTE on the full dataset (or across cross-validation folds) before splitting leaks test-set statistical information into training; the documented fix is to fit such transformations only within a pipeline scoped to each training fold — [Medium, "Split Smart: Avoiding Data Leakage in Cross-Validation"](https://medium.com/@pacosun/split-smart-avoiding-data-leakage-in-cross-validation-894863a93553)
- A related, directly relevant leakage case is documented for near-duplicate records generally: near-duplicate samples should be identified and removed/deduplicated before the train/test split is made, so that near-identical images do not end up split across both the training and test sets — [Towards Data Science, "An Introduction to Data Leakage"](https://towardsdatascience.com/an-introduction-to-data-leakage-f1c58f7c1d64)
- Practitioner guidance from a DeepLearning.AI community discussion on using the PyTorch `Dataset` class reinforces the same operational rule for implementation: augmentation transforms should be applied to the training dataset object only, leaving validation/test dataset objects unaugmented — [DeepLearning.AI Community, "Using the Dataset class for an on-the-fly augmentation"](https://community.deeplearning.ai/t/using-the-dataset-class-for-an-on-the-fly-augmentation/885120)

### Inferences
- Combining this with the deduplication findings above, a Phase-1 report can state the principled pipeline order: (1) deduplicate near-identical source images across merged datasets FIRST, (2) perform the train/test split on the deduplicated set of distinct source images, (3) apply synthetic generation/augmentation only to the training split afterward, inside the `Dataset.__getitem__` (per the PyTorch/Albumentations pattern documented above) — never applying augmentation before the split, and never letting augmented derivatives of a given source image appear on both sides of the split.
- This ordering directly generalizes the general "fit-only-on-training-fold" principle for scalers/SMOTE (cited above) to the image-augmentation case, since conceptually both are "operations that must not see or leak from the held-out evaluation set."

### Gaps
- None significant for this question — multiple independent, mutually corroborating sources (an academic methodology paper, an empirical dataset/case study, and several practitioner explainers) all converge on the same rule, giving high confidence in this finding.
````

### `08_integration_techniques_grounded.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** DONE: dedup before split, split by near-duplicate group, augmentation after split (train only); pHash and Lones citations in Section D.

# Plan 08: Grounded Integration Techniques (replaces speculative content in Plan 02)

## 1. Why this exists
Plan 02 described an integration pipeline in confident technical language
but without citations. A deep-research pass found real, citable sources for
each technique, and corrected one claim that was effectively unsupported.
Full sourcing: `research_notes/Shape dataset integration and tooling/integration_techniques.md`.

## 2. Aspect-ratio / dimension handling: letterboxing is the real standard
Rescale so the longest side matches the target size, preserving aspect
ratio, then pad the remainder with a constant fill color. This is the
documented, named technique across libraries, not an invented approach:
- Albumentations `LetterBox` (equivalent to `LongestMaxSize` + `PadIfNeeded`,
  defaults to YOLO's pad value 114): https://albumentations.ai/explore/transform/LetterBox/docs/
- torchvision equivalent: pass an int (not a tuple) to `Resize` to scale the
  shorter edge, then a manually computed `Pad`: https://discuss.pytorch.org/t/how-to-resize-and-pad-in-a-torchvision-transforms-compose/71850

## 3. Grayscale conversion: BT.601, not an invented formula
Both OpenCV and Pillow default to the **ITU-R BT.601 luma weights**
(Y = 0.299R + 0.587G + 0.114B), confirmed directly from each library's own
docs, not the newer BT.709 weights:
- OpenCV `COLOR_RGB2GRAY`/`COLOR_BGR2GRAY` docs state the formula explicitly.
- Pillow `Image.convert('L')` docs name the same "ITU-R 601-2 luma transform."

## 4. Polarity normalization: no single named standard — say so honestly
There is no one official "polarity normalization standard" to cite as such.
The defensible framing: compute a per-image polarity signal (e.g. border-
pixel mean intensity, or which histogram mode holds the majority of pixels)
and invert any image disagreeing with the dataset's chosen convention. This
mirrors real, documented patterns rather than inventing one:
- MATLAB `imbinarize`'s explicit `ForegroundPolarity` parameter:
  https://www.mathworks.com/help/images/ref/imbinarize.html
- OpenCV's `THRESH_BINARY_INV` mode and general inverse-threshold
  conventions.
**Correction**: an earlier-surfaced claim that arXiv:2012.07599 covers
histogram-based polarity detection for mixed handwritten numerals was
checked directly and is **false** — that paper is an unrelated Siamese-
network clustering paper. Do not cite it for this topic.

## 5. Deduplication: pHash via `imagehash`, correctly sourced
- Library: https://github.com/JohannesBuchner/imagehash (DCT-based
  perceptual hash via `scipy.fftpack`).
- Primary academic grounding: Christoph Zauner's 2010 master's thesis
  (https://phash.org/docs/pubs/thesis_zauner.pdf) — note the library's own
  README cites a blog post, not a paper, so don't overstate the rigor behind
  it in the report.

## 6. Synthetic data and augmentation: on-the-fly, inside `__getitem__`
- PyTorch's own "Writing Custom Datasets, DataLoaders and Transforms"
  tutorial establishes the canonical pattern: a custom `Dataset` subclass
  defers loading/transforming to `__getitem__`, executed lazily per access,
  explicitly framed as memory-efficient.
  https://docs.pytorch.org/tutorials/beginner/data_loading_tutorial.html
- Albumentations' `Compose` pipeline slots into the same call, re-sampling
  random parameters fresh every invocation (call-local RNG), so repeated
  epochs over one image yield different variants with no precomputed cache.
  https://albumentations.ai/docs/2-core-concepts/pipelines/
- **Honest caveat**: no official doc uses the phrase "synthetic data
  generation" in this exact pattern. Framing a generator function as
  occupying the same `__getitem__` slot as augmentation is this project's
  own architectural inference, not a directly-sourced claim — say so in the
  report rather than presenting it as an established convention.

## 7. The critical rule: augmentation only AFTER the train/test split
This is the best-sourced finding in the whole pass, with convergent,
independent evidence:
- Academic ML-pitfalls guide states flatly that augmentation "should be
  applied only to training data": https://arxiv.org/pdf/2108.02497
- A 2025 empirical case study showed pre-split augmentation inflated
  reported mAP50 by **up to 66 percentage points** vs. correctly post-split
  augmentation: https://data.mendeley.com/datasets/f9k79z29rp/1
- Deduplication should happen **before** the split (so near-duplicates don't
  land on both sides of it); any fitted transform (scaler, SMOTE,
  augmentation pipeline) must be scoped to the training fold only.

**Resulting pipeline order to state in the report**: deduplicate the merged
raw images first -> split into train/test on the deduplicated set -> only
then apply synthetic generation and augmentation, inside the training
`Dataset.__getitem__`, never before the split.

## 8. Action items
- [ ] Replace Plan 02's uncited technique descriptions with the citations
      above where the report's Section C is expanded.
- [ ] Explicitly state in the report that dedup happens before the split,
      and augmentation/synthetic generation happens only after, inside the
      training path — this is the single most defensible, most important
      addition from this research pass.
- [ ] Do not cite arXiv:2012.07599 for polarity detection; it doesn't support
      that claim.
- [ ] Frame the "synthetic generation fits the same architectural slot as
      augmentation" claim as this project's own inference, not a directly
      documented pattern.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Each technique was matched to documentation or a paper (Albumentations letterboxing, pHash by Zauner, augment-after-split by Lones). A misattributed arXiv citation was caught (findings.md section 10).

## Our decision

We kept letterboxing, dedup before the split, the split by near-duplicate group and augmentation after the split (train only), and cited pHash and Lones in Section D.

## Measured effect

2,972 near-duplicate images were grouped so that each group stays in one split. No model at this stage.
