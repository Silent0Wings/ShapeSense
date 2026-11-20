# 2_data_preparation/cleaning - Null data handling

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-20
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is verbatim from the session log (recorded in `docs/prompts.csv` of the snapshot); the reply was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt P07 (verbatim, 2026-10-19)

> but maybe the null is implied as in its missing a compatibility and has to be converted to mathc our shcema

_Source: Claude Code session 2026-10-20, user message 85. Confidence: low. The prompt is dated one day after the commit. It is the closest null-handling prompt in the log, so treat the link as a guess._

## Response (the reply was not saved; the work it produced, verbatim)

### `phase1_report.tex (section D. Data Preparation)`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````latex
\section*{D. Data Preparation}
\addcontentsline{toc}{section}{D. Data Preparation}
% =====================================================================

\textbf{Null data.} Mapped onto our schema, every source is missing some
fields. Our rules: no label $\to$ drop; no size $\to$ derive it; no
license $\to$ \texttt{unknown} (source excluded). Dropping rows without
a class label and filling a global constant follow \cite[slide 24]{lecdp}.

\begin{table}[H]
\centering
\caption{Real null cases when mapping sources onto the schema.}
\small
\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{4.4cm}
  >{\raggedright\arraybackslash}p{4.4cm}
  >{\raggedright\arraybackslash}X r@{}}
\toprule
Source & Missing field & Handling & Images \\
\midrule
reevald, El Korchi, hand-drawn & \texttt{label\_id} (no matching
  class) & dropped: kite, trapezoid, parallelogram, heptagon, nonagon,
  other & 34{,}787 \\
reevald, El Korchi, hand-drawn & label (no metadata) & taken from folder or
  file name & all \\
Quick, Draw! & width, height (vector strokes) & drawn on a
  $256{\times}256$ canvas & 3{,}500 \\
all sources & per-image license & inherited from the \emph{Source} table &
  all \\
Dinesh & license (``Unknown'') & \texttt{unknown}, source excluded &
  30{,}000 \\
\bottomrule
\end{tabularx}
\end{table}

\textbf{Outlier detection.} Results from our build:
\begin{itemize}
  \item \textbf{No contrast:} 1 image got rejected, the shape was the exact same color as
        its background (Figure~\ref{fig:outliers}, top).
  \item \textbf{Exact duplicates:} 32 identical images were removed before the split.
  \item \textbf{Near duplicates:} 2,972 images ended up in near-identical groups
        (perceptual hash \cite{zauner}); each group stays in one split so data dosent leak.
  \item \textbf{Low diversity:} El Korchi shapes mostly differ in color,
        size and position, which standardisation removes; one group alone holds
        175 near-identical pentagons (Figure~\ref{fig:outliers}, bottom).
  \item \textbf{Not yet filtered:} Quick, Draw!'s \texttt{diamond}
        still includes some gemstone drawings that we might filter later..
\end{itemize}

\begin{figure}[H]
\centering
\includegraphics[width=0.55\linewidth]{figures/outlier_examples.png}
\caption{Top: rejected (no contrast). Bottom: a near-duplicate group of
175 pentagons.}
\label{fig:outliers}
\end{figure}

\textbf{Split.} 70/15/15 split by near-duplicate group: 12,761 train, 2,890
validation, 2,849 test. Augmentation and synthetic data strictly come after the
split, on the training set only \cite{lones}\cite[slide 58]{lecclf}.

\textbf{Transformation.} Images are stored as $64{\times}64$ 8-bit PNGs,
normalized to $[0,1]$ on load; labels use their index
(table~\ref{tab:labels}). Training images (real and synthetic) get five
augmentations \cite{labellerr}: rotation, scale, shear, noise, blur . 
Shear and non-uniform scaling are disabled for circle, ellipse, square,
rectangle and diamond, since those transforms would actually chnage the geometric class!

\begin{figure}[H]
\centering
\begin{minipage}[b]{0.48\linewidth}
  \centering
  \includegraphics[width=\linewidth]{figures/data_augmentation_example.png}
  \caption{Augmentation examples (adapted from \cite{labellerr}).}
  \label{fig:augexample}
\end{minipage}\hfill
\begin{minipage}[b]{0.48\linewidth}
  \centering
  \includegraphics[width=\linewidth]{figures/transform_pixel_grid.png}
  \caption{A circle before and after resizing to the $64\times64$
  grid.}
  \label{fig:pixelgrid}
\end{minipage}
\end{figure}



% =====================================================================
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Each null case was counted on the built dataset (findings.md section 6).

## Our decision

The user's point was that a null can be implied, meaning a missing compatibility that must be converted to match the schema. So nulls were handled at the schema level. A label with no matching class is dropped (34,787 images). Labels come from the folder or file name. Quick, Draw! vectors get a 256x256 canvas. The licence comes from the Source table, and the 'Unknown' licence source (Dinesh, 30,000) is excluded.

## Measured effect

No model at this stage.
