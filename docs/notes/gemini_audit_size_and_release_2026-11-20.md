# Prompt interaction: audit of the advice on the size cell and the release zip (2026-11-20)

Registered as a prompt interaction. The text below is pasted unedited. It is an audit of the earlier advice on the Excel size cell, the release zip, and Git LFS. The model that wrote the audit was not recorded.

## Pasted interaction

SO ON THE EXCEL CHEAT WHAT DO I PUT ? 3:56 AM Put this in the size cell: 35 MB (selected from 137,299 raw files, about 277 MB of data; about 730 MB on disk) (plus synthetic shapes generated during training, not stored) 35 MB is the unified training set, which the pipeline builds. 277 MB is the actual size of the four raw sources, counting bytes. 730 MB is the disk-allocated size, which Explorer shows as "Size on disk." If the sheet only has room for one raw number, use 277 MB and say it's the data size, not the disk size. 35 MB (selected from 137,299 raw files, about 729 MB) (plus synthetic shapes generated during training, not stored) 3:56 AM Change the raw-size part from "729 MB" to "277 MB," since 277 MB is the actual data size. The 729 MB figure is the disk-allocated size, which I had mislabelled as data size. 35 MB (selected from 137,299 raw files, about 277 MB) (plus synthetic shapes generated during training, not stored) WE PUSH THIS =["C:\Users\Gica\Github_Clones\ShapeSense\data_set.zip"] ? OR PUT IT IN RELEASE ? 3:57 AM Put it in a release, not the repo. Three reasons: Size: the zip is 328 MB, which is over GitHub's 100 MB file limit. Pushing it would need Git LFS. History: anything pushed stays in the repo's history forever, even if you delete it later. Public: if the repo is public, the release is public too. The sources' licenses (CC BY 4.0 and CC0) allow this, but credit is required. Two steps before uploading: Re-zip with only the four source folders. The current zip is larger than those four folders, so it likely includes the generated unified set and the holdouts. Move the zip out of the repo folder. It's now at C:\Users\Gica\Github_Clones\ShapeSense\data_set.zip, and a careless git add . could commit it. Put it in a folder outside the repo, such as your Downloads folder, and upload it from there. Then create a release on GitHub, attach the zip as an asset, and use its direct download link in the notebook's setup cell. I won't push anything without your go-ahead. GIT LFS IS BAD ? 3:57 AM Git LFS isn't bad. It's the right tool for large binary files in general. For this case it's the weaker choice: Quota: free accounts get a small amount of storage and download bandwidth. Each Colab run downloads the zip, so a few runs can use up the bandwidth. I haven't checked the current numbers, so look them up on GitHub's pricing page. History: the zip stays in the repo's history even if you remove it later. Rules: the project keeps data out of the repo, so LFS would go against that. A release asset avoids all three: it sits outside the repo's history, it doesn't use the LFS quota, and the zip is under the 2 GB per-asset limit. LFS would make more sense if the zip changed often and had to be versioned with the code.

Put this exact text in the size cell:

35 MB (selected from 137,299 raw files, about 277 MB) (plus synthetic shapes generated during training, not stored)

Use 277 MB, not 729 MB: 277 MB is the actual byte size of the four raw sources; 729 MB is only the Windows "size on disk" allocation. The 35 MB is the built unified training set, and synthetic shapes are generated during training rather than stored in the released dataset.

If the cell needs one number, use: 277 MB. Then, if there is a separate description/notes cell, add:

Raw source data size; excludes 729 MB disk-allocation overhead and synthetic shapes generated during training.

Where the zip goes. Do not push C:\Users\Gica\Github_Clones\ShapeSense\data_set.zip into the repository. Put the re-zipped, source-only archive in a GitHub Release and attach it as a release asset; it is 328 MB, above GitHub's normal 100 MB repository-file limit, and release assets avoid adding the archive to Git history.

Before uploading:
- Re-zip only the four original source folders, not the generated unified set or holdouts.
- Move the zip outside the repo, for example to Downloads, so git add . cannot accidentally commit it.
- Create the GitHub release, upload the zip as an asset, and put its direct download URL in the notebook setup cell.
- Keep the required attribution for the CC BY 4.0 / CC0 sources.

Git LFS is not inherently bad, but for this one-time 328 MB dataset it is worse than a release asset: it consumes LFS storage/bandwidth quota, keeps the blob in repository history, and conflicts with the project's "data outside the repo" policy. Use LFS only if the dataset changes frequently and must be versioned alongside the code.

DO YOU AGREE ?

Yes. I agree with all three decisions.

Excel size cell. Use: 35 MB (selected from 137,299 raw files, about 277 MB) (plus synthetic shapes generated during training, not stored). It is accurate because it distinguishes the three different quantities:

| Figure | Meaning |
|---|---|
| 35 MB | Size of the unified training set produced by the pipeline |
| 137,299 | Number of raw source files considered |
| 277 MB | Actual byte size of the four raw sources |
| 729 MB | Windows "size on disk" allocation, not data size |
| Synthetic shapes | Generated during training; not part of the released archive |

The important correction is already right: 277 MB is the raw data size, while 729 MB is filesystem allocation overhead. Do not call 729 MB the dataset size.

Release, not repo. Yes: upload the source-only zip as a GitHub Release asset, not by pushing it into the repository.
- The current zip is 328 MB, above GitHub's ordinary 100 MB file limit.
- A pushed binary remains in Git history even if later deleted.
- A release asset stays outside the repository history and does not consume Git LFS quota.
- The 2 GB per-release-asset limit comfortably accommodates it.

Git LFS. Git LFS is not bad in general; it is simply the wrong fit here. It is appropriate for frequently changing, versioned binary assets that must stay tightly coupled to code. For a largely static dataset release, a release asset is simpler, cheaper, and cleaner.

One refinement. Before uploading, make the release zip contain only the four raw source folders. Then label it something like shapesense_raw_sources_v1.zip. In the release notes, state:

Raw source data: 137,299 files, approximately 277 MB uncompressed.
Unified training set: 35 MB, built by the ShapeSense pipeline.
Synthetic training shapes are generated during training and are not included.

That makes the Excel claim and the downloadable artifact consistent.

## Our assessment

- **277 MB** is confirmed. Measured byte size of the four sources is 86 + 126 + 64 + 1 MB, about 277 MB. The 730 MB figure is disk allocation.
- **137,299 "raw files" needs wording.** It counts image files plus the seven NDJSON files. The folders also hold 20,005 vertex CSVs, so the total on disk is 157,340 files. The sheet and release notes should say "137,299 image and NDJSON files."
- **github_handdrawn image count** on disk is 27,312, against 27,292 documented. The 20 extra files should be identified before the number is quoted.
- **The zip is larger than the four sources** (328 MB against about 277 MB). This is consistent with it holding the whole `data_set` folder, but the zip's contents were not listed.
- **The quota claims** for Git LFS and the GitHub pricing limits were not checked against current GitHub documentation.
- **The 2 GB release-asset limit** and the 100 MB single-file limit are the figures to confirm on GitHub's docs before the release is created.

## Decision

- Use the size cell text above, with "137,299 image and NDJSON files" in place of "raw files."
- Upload a source-only zip as a release asset, named `shapesense_raw_sources_v1.zip`.
- Do not push the zip to the repo. No LFS.
- Nothing has been uploaded or pushed.

## Measured effect

None. Documentation and decision record only.
