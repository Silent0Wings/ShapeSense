# Candidate 2D shape datasets (recorded from a pasted list)

> Recorded from a pasted overview. **Not verified** against the sources. Check each link, size and license before using it. The datasets already used by this project are listed in [data_sets.md](data_sets.md).

## Synthetic classification

- **2D Geometric Shapes Dataset** (El Korchi and Ghanou, 2020): 9 classes (triangle, square, pentagon, hexagon, heptagon, octagon, nonagon, circle, star), 10k images per class, 200x200 RGB, random position, scale, rotation and color. Includes a generator script. Host: Mendeley Data.
- **Khalid1G/shapes-dataset** (GitHub): 16 classes (circle, semicircle, oval, triangle, square, rectangle, parallelogram, rhombus, trapezoid, kite, pentagon to decagon), 100 PNGs per class at 224x224, transparent backgrounds. Includes a Pillow generator.
- **Kaggle "Four Shapes" and "Geometric Shapes"**: small CSV and image packs, often used in tutorials, 4-class circle, triangle, square and rectangle variants. Less controlled than the papers above.

## Latent factors and disentanglement

- **dSprites** (TensorFlow Datasets): 737,280 binary 64x64 images, 6 known latent factors: shape (square, ellipse, heart), scale, rotation, x, y, color (fixed white). Exhaustively enumerated.

## Shape structure and part decomposition

- **2D Shape Structure Database** (Inria, 2dshapesstructure.github.io): crowdsourced decompositions of about 1,200 shapes across 70 classes, 41,953 annotations. Hierarchical part segmentations and geometric relations. JSON, OBJ and CSV.

## Spatial relations and concept learning

- **GeoConShapes** (proximity-based spatial relation concepts): three subsets, simple geometric shapes (SGS), artificial crack and void patterns (ACV), and complex semantic instances (CSI). SGS has rectangles, triangles, ellipses, parallelograms and trapezoids, labelled alone, close, far or overlap. Host: Mendeley Data, code on GitHub.

## Education and geometry problems

- **ElementaryCQT** (Circle, Quadrilateral, Triangle): figures with and without extra markings (diagonals, perpendiculars, tangents, chords). Benchmark for geometry-problem pipelines. Host: Mendeley Data.

## Hubs

- **Hugging Face Datasets**: at least one mirror of a 2D geometric shapes dataset (for example rfromeofrancesco/2d-geometric-shapes-dataset).
- **Mendeley Data**: host of El Korchi and Ghanou 2020, ElementaryCQT and GeoConShapes.

## Relevance to this project

- The project's 10 classes (circle, ellipse, triangle, square, rectangle, pentagon, hexagon, octagon, star, diamond) overlap most with El Korchi and Ghanou 2020 (already used as the Kaggle/Mendeley-style source in the project's data list, to be confirmed in [data_sets.md](data_sets.md)) and Khalid1G.
- dSprites and the Inria structure database are not classification sources for this project's 10 classes.
