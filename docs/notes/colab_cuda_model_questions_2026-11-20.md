# Prompt interaction: moving a CUDA-trained model to Google Colab (2026-11-20)

Registered as a prompt interaction. The reply below is pasted unedited. The model that wrote it was not recorded.

## Prompt

> I TRAINED MY MODEL ON CUDA BUT NOW I NEED TO PUT IT IN GOOGLE COLAB. WHAT ARE MY OPTIONS

## Response

Yes—you can almost always run a CUDA-trained model in Google Colab. The key question is whether you mean a model trained with CUDA (PyTorch/TensorFlow/JAX) or custom CUDA C++ kernels; both work, but the setup differs.

1. If it's PyTorch / TensorFlow / JAX. This is the easiest case: Colab provides GPU runtimes with NVIDIA drivers and CUDA support already installed. Select Runtime → Change runtime type → T4 GPU → Save, then move the model and inputs to the GPU.

```python
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = MyModel()
model.load_state_dict(torch.load("model.pt", map_location=device))
model.to(device)

x = x.to(device)
out = model(x)
```

For TensorFlow:

```python
with tf.device("/GPU:0"):
    model = tf.keras.models.load_model("model.keras")
    predictions = model.predict(x)
```

You do not need to install CUDA manually for normal PyTorch/TensorFlow training or inference; Colab's GPU runtime includes the required CUDA stack.

2. Getting your files into Colab.

| Situation | Best option |
|---|---|
| Small model/checkpoint | Upload directly with Colab's Files panel or files.upload() |
| Model + dataset | Mount Google Drive |
| Code repository | Clone from GitHub |
| Large checkpoint | Keep it in Drive/Hugging Face/GitHub LFS and download only when needed |

Google Drive example:

```python
from google.colab import drive
drive.mount("/content/drive")

model = torch.load(
    "/content/drive/MyDrive/models/my_model.pt",
    map_location=device
)
```

GitHub example:

```bash
!git clone https://github.com/yourname/your-repo.git
%cd your-repo
!pip install -r requirements.txt
```

3. If you wrote custom CUDA C++ code. If your training pipeline uses .cu files or a custom CUDA extension, Colab can compile and run them with nvcc. A practical approach is to write the CUDA source to a file, compile it, then run it:

```python
%%writefile kernel.cu
// your CUDA code here
```

```bash
!nvcc -arch=sm_75 kernel.cu -o kernel
!./kernel
```

Colab's free T4 GPU uses compute capability 7.5, so -arch=sm_75 is commonly the right target.

If you built a PyTorch CUDA extension, install/compile it in Colab:

```bash
!pip install .
```

or:

```bash
!python setup.py install
```

Make sure the extension is compiled inside the Colab runtime after selecting the GPU runtime; a wheel compiled on your local Windows CUDA setup may not be compatible with Colab's Linux GPU environment.

4. Important compatibility checks. Run this first in Colab:

```python
!nvidia-smi
!nvcc --version

import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
```

Then check:
- Framework version: your local PyTorch/TensorFlow version should be compatible with the version installed in Colab.
- Checkpoint format: prefer .pt / .pth / .safetensors for PyTorch, or ONNX/SavedModel for portable inference.
- Custom CUDA code: recompile it on Colab rather than copying a Windows-built binary.
- GPU architecture: code compiled only for your local GPU's architecture may fail on Colab's T4; compile with the appropriate -arch flag or include PTX.
- Session lifetime: Colab VMs are temporary, so save checkpoints to Drive or another persistent location rather than relying on /content.

5. If you only need inference. You may not need a GPU at all. Export the trained model and run it on Colab's CPU:

```python
# PyTorch
torch.save(model.state_dict(), "model_state.pt")

# Or export for portable inference
torch.onnx.export(model, dummy_input, "model.onnx")
```

Then load it in Colab with PyTorch or ONNX Runtime. This avoids CUDA version and GPU-architecture issues entirely.

Recommended path. For most cases:
1. Save model weights from your local CUDA training run.
2. Upload weights and training/inference code to Drive or GitHub.
3. Open Colab and switch to a T4 GPU runtime.
4. Install only missing dependencies.
5. Load the checkpoint with map_location=device.
6. Run a tiny forward pass before launching full training or inference.

If you tell me whether you used PyTorch, TensorFlow, a custom CUDA .cu program, or a compiled extension, and paste the error you get in Colab, I can give you the exact conversion/load steps.

---

> DO I PUT FALL BACK ?

Yes—put a fallback in your code. Use GPU if Colab gives you one, otherwise run on CPU. This prevents a crash if the GPU runtime is unavailable or CUDA is not detected.

```python
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using:", device)

model = MyModel()
state_dict = torch.load("model.pt", map_location=device, weights_only=True)
model.load_state_dict(state_dict)
model.to(device)

x = x.to(device)
output = model(x)
```

map_location=device is the important fallback: it lets a checkpoint saved on CUDA load correctly even if Colab is running on CPU. PyTorch documents that map_location remaps stored tensors to the requested device.

If you mean "fallback runtime": If you mean "should I set a CPU fallback in Colab?"—yes, but do it in code, not by changing the runtime setting. Keep the notebook set to GPU when you need training speed; the device check above automatically handles the case where no GPU is available.

To switch Colab's hardware accelerator: Runtime → Change runtime type → Hardware accelerator → GPU. Colab notes that selecting a GPU runtime does not automatically make your code use it; your tensors and model must be moved to CUDA.

If you mean "fallback for CUDA errors": For a custom CUDA extension or .cu program, a CPU fallback is useful only if you wrote a CPU implementation too. Otherwise, do not silently fall back—surface the error, because results or performance may be wrong.

```python
try:
    output = cuda_model(x)
except Exception as e:
    print("CUDA path failed:", e)
    raise  # better than silently switching to CPU
```

For normal PyTorch models, though, use the first `device = ...` pattern. It is the standard, safe fallback.

Show me how to load it on cpu instead
How do I check if my GPU is active in Colab
What if my model file is too big for Colab
How do I fix CUDA out of memory errors
Show me the TensorFlow version of this code

## Our decision

- The pasted fallback pattern (`device = cuda if available else cpu`) is correct for loading a finished model for inference.
- It is not applied to the training pipeline. `configs/pipeline.yaml` line 140 sets `device: cuda` and says "cuda fails loudly when no GPU is visible." A silent CPU run would not be comparable with the recorded GPU results, and `requirements.txt` notes that CPU and GPU runs are not numerically identical.
- The stages already load checkpoints with `map_location="cpu"` (`src/stage5_eval/evaluate.py:99`, `src/stage6_report/export.py:106`), so the repo already handles CUDA-trained checkpoints on CPU.
- The notebook keeps its GPU check (cell 4) and gains an explanation of why it stops on a CPU runtime.

## Measured effect

None. Documentation and notebook explanation only.
