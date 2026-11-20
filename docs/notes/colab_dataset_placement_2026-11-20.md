# Prompt interaction: where to put the dataset and the augmentation script for Colab (2026-11-20)

Registered as a prompt interaction. The reply below is pasted unedited. The model that wrote it was not recorded.

## Prompt

> WHERE TO PUT THE DATA SET IT IS ABOUT 700 MB + PYTHON SCRIPT FOR AUGEMENTATION DO I PUT IN GITHUB OR BETTER TO PUT IT ON GOOGLE COLLAB SAME FOLDER AS THE NOTE BOOK

## Response

Put the 700 MB dataset in Google Drive, not directly in the same Colab folder. Put the Python augmentation script and notebook in GitHub (or Drive); then, when Colab starts, copy the dataset from Drive to Colab's temporary /content folder for fast training.

Recommended layout

```text
Google Drive/
└── my_project/
    ├── dataset.zip          # 700 MB dataset, zipped
    ├── model.pt             # optional trained weights
    └── augmentation.py      # optional, if you do not want it in GitHub

GitHub repository/
├── train_notebook.ipynb     # Colab notebook
├── augmentation.py          # augmentation script
├── requirements.txt
└── src/ or model code
```

Do not commit a 700 MB dataset to a normal GitHub repository. GitHub is best for code, notebook, configs, and small assets; large datasets belong in Drive, Hugging Face Datasets, Kaggle Datasets, or a release/LFS asset.

Why Drive + local copy. Colab's /content folder is on the temporary VM and is fast for training, but it disappears when the runtime resets. Google Drive is persistent, but reading thousands of small image files directly from mounted Drive can be slow.

So use this pattern:
1. Store dataset.zip in Drive.
2. Mount Drive.
3. Copy the zip to /content.
4. Unzip it into /content/data.
5. Train from /content/data.

Colab setup

```python
from google.colab import drive
drive.mount("/content/drive")
```

```python
# Copy the 700 MB archive to Colab's fast temporary disk
!cp "/content/drive/MyDrive/my_project/dataset.zip" /content/

# Extract it
!unzip -q /content/dataset.zip -d /content/data
```

Then your augmentation script should read from:

```python
DATA_DIR = "/content/data"
```

For example:

```python
from pathlib import Path

DATA_DIR = Path("/content/data")
train_dir = DATA_DIR / "train"
val_dir = DATA_DIR / "val"
```

Get the script into Colab. If your augmentation script is in GitHub:

```python
!git clone https://github.com/yourname/your-repo.git
%cd your-repo
```

Then run it:

```python
!python augmentation.py --input /content/data --output /content/augmented
```

Or, if you keep augmentation.py in Drive:

```python
!cp "/content/drive/MyDrive/my_project/augmentation.py" /content/
!python /content/augmentation.py --input /content/data --output /content/augmented
```

Do not put dataset beside the notebook. Putting the dataset in the same Colab notebook folder means it lives in /content, which is temporary. If Colab disconnects or resets, you lose it and must re-upload it.

| Item | Where to keep it | Why |
|---|---|---|
| Notebook | GitHub and/or Drive | Version control and persistence |
| augmentation.py | GitHub | Code should be versioned |
| 700 MB dataset | Google Drive, zipped | Persistent and easy to restore |
| Extracted dataset during training | /content/data | Faster local VM disk access |
| Model checkpoints | Google Drive | Survive runtime resets |
| Augmented outputs | /content during training; optionally zip back to Drive | Avoid filling Drive with duplicate data |

Save augmented data carefully. If augmentation creates a new 700 MB+ dataset, do not automatically save every augmented image to Drive. Usually, augment images on the fly during training instead:

```python
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(0.2, 0.2, 0.2),
    transforms.ToTensor(),
])
```

That avoids storing a large duplicate dataset. If your script must generate augmented files, save them to /content/augmented, train from there, and only zip/upload the final output if you really need it later.

One practical note. A 700 MB zip is completely fine for Drive; free Google accounts include 15 GB shared across Drive, Gmail, and Photos, so ensure you have enough free quota.

Best answer: GitHub for the notebook and augmentation script; Google Drive for the zipped dataset; copy/unzip it into /content/data at the start of each Colab session.

Show me how to structure the code
Show me how to zip and unzip it efficiently
Show me how to handle requirements and dependencies
Show me how to push code to GitHub
Show me an example folder structure

## Our decision

- The advice matches the project's own rule: `data_set/` is gitignored and must not go into GitHub, so the raw data goes to Drive as a zip.
- Our raw data is about 730 MB for the four sources (see the notebook correction), not the 700 MB in the prompt, and Stage 1 needs exact folder names (`quickdraw/subset`, `2D geometric shapes dataset/output`, `kaggle_reevald/dataset`, `github_handdrawn/data/user.*/images`). The zip must keep those names, or Stage 1 stops.
- Augmentation in this project is part of the pipeline (`src/stage2_augment` and the synthetic generator in Stage 3), not a standalone `augmentation.py`. It runs inside the notebook's pipeline steps, so the script does not need to be copied separately.
- The notebook's data cell still points at a Drive folder without a copy-and-unzip step. That change is not made yet and needs a decision.

## Measured effect

None. Documentation only.
