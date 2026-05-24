# TraceLight

A web demo that turns photographs into pencil sketches using classical image processing.

---

## Quick start

### 1. Requirements

- **Python 3.10 or newer** (tested on 3.12)
- `pip` available on your PATH

Check your version:

```bash
python --version
```

### 2. Clone the repository

```bash
git clone <repo-url> tracelight-demo
cd tracelight-demo
```

### 3. Create a virtual environment (recommended)

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (cmd):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the app

```bash
streamlit run app.py
```

Streamlit will open the app automatically in your default browser at
**[http://localhost:8501](http://localhost:8501)**. Upload any image (PNG, JPG,
JPEG, BMP, or WEBP) from the sidebar and the sketch appears instantly.

To stop the server, press **Ctrl+C** in the terminal.

---

## Running in PyCharm

1. Open the project folder (`tracelight-demo`) in PyCharm.
2. **File → Settings → Project → Python Interpreter** → add the virtual
   environment you created above (or let PyCharm create one).
3. Open the terminal inside PyCharm (`Alt + F12`) and run
   `streamlit run app.py`. PyCharm will detect the running server.

---

## Project structure

```
tracelight-demo/
├── app.py                       # Streamlit web application (UI entry point)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── sketching/
    ├── __init__.py
    ├── pencil_sketch.py         # Pencil sketch effect (grayscale + color dodge)
    ├── edge_detection.py        # Sobel, Laplacian, and Canny edge detectors
    └── hatching.py              # Directional hatching (gradient-aligned strokes)
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.35.0 | Web UI framework |
| `opencv-python-headless` | ≥ 4.9.0 | Image loading, processing, and export |
| `numpy` | ≥ 1.26.0 | Array arithmetic |
| `matplotlib` | ≥ 3.8.0 | Pipeline visualization and histograms |

---

# Implementation reference

---

## Module: `sketching/pencil_sketch.py`

Contains the full pencil sketch algorithm, broken into individual steps so each
intermediate result can be captured and displayed in the pipeline view.

---

### `to_grayscale(img)`

**Signature:**
```python
def to_grayscale(img)
```

**Description:**
Converts a BGR image (as loaded by OpenCV) to a single-channel grayscale
image using the ITU-R BT.601 luminosity weights. These weights model human
perception, the eye is most sensitive to green, less so to red, and least
to blue.

**Formula:**
```
Y(x,y) = 0.299 · R(x,y) + 0.587 · G(x,y) + 0.114 · B(x,y)
```

**Parameters:**
- `img` — NumPy array of shape `(H, W, 3)`, dtype `uint8`, BGR order (OpenCV default).

**Returns:**
- NumPy array of shape `(H, W)`, dtype `uint8`.

**OpenCV call used:** `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`

---

### `invert(gray)`

**Signature:**
```python
def invert(gray)
```

**Description:**
Creates a photographic negative of a grayscale image by subtracting every
pixel value from 255. Dark areas become bright and vice versa. This is a
necessary intermediate step before the Gaussian blur, the blur must operate
on the inverted image so that the subsequent color dodge produces lines
(dark on white) rather than fills.

**Formula:**
```
I_inv(x,y) = 255 - I(x,y)
```

**Parameters:**
- `gray` — NumPy array of shape `(H, W)`, dtype `uint8`.

**Returns:**
- NumPy array of shape `(H, W)`, dtype `uint8`.

---

### `gaussian_blur(img, radius)`

**Signature:**
```python
def gaussian_blur(img, radius)
```

**Description:**
Applies a Gaussian blur to the image using a square kernel of size
`radius × radius`. The Gaussian kernel weights nearby pixels more than
distant ones, producing a smooth blur without harsh transitions.

OpenCV requires the kernel size to be an odd integer. If an even `radius`
is passed, the function increments it by 1 to enforce this constraint.

Setting `sigmaX=0` and `sigmaY=0` tells OpenCV to compute σ automatically
from the kernel size using:
```
σ = 0.3 · ((k - 1) / 2 - 1) + 0.8
```

**Formula (continuous Gaussian):**
```
G_σ(x,y) = (1 / 2πσ²) · exp(-(x² + y²) / 2σ²)
```

**Parameters:**
- `img` — NumPy array of shape `(H, W)`, dtype `uint8`.
- `radius` — Kernel size (odd integer). Controls the spread of the blur.
  Larger values produce softer, broader sketch strokes in the final result.

**Returns:**
- NumPy array of shape `(H, W)`, dtype `uint8`.

**OpenCV call used:** `cv2.GaussianBlur`

---

### `color_dodge(gray, blurred)`

**Signature:**
```python
def color_dodge(gray, blurred)
```

**Description:**
Applies the color dodge blending formula to produce the pencil sketch.
Color dodge is a standard blending mode in photo editing software
(Photoshop, GIMP) that brightens the base layer by dividing it by the
complement of the blend layer.

**Behavior:**
- Where `blurred ≈ 255` (bright in the blurred inverted image, meaning
  the original had a dark edge), the denominator approaches zero and the
  result is clipped to 255 — producing white (paper).
- Where `blurred` is small (original had a bright, flat area), the grayscale
  value passes through mostly unchanged, producing light gray or dark lines.

This contrast between white background and preserved dark strokes creates
the pencil-on-paper appearance.

**Formula:**
```
S(x,y) = min( G(x,y) · 255 / (255 - B(x,y) + ε), 255 )
```

Where:
- `G` = grayscale image
- `B` = blurred inverted image
- `ε = 1e-6` prevents division by zero

**Parameters:**
- `gray` — NumPy array of shape `(H, W)`, dtype `uint8`. Grayscale source.
- `blurred` — NumPy array of shape `(H, W)`, dtype `uint8`. Blurred inverted image.

**Returns:**
- NumPy array of shape `(H, W)`, dtype `uint8`. The pencil sketch.

**Implementation note:** Both inputs are cast to `float32` before the
division to avoid integer overflow and rounding errors. The result is
clipped to `[0, 255]` and cast back to `uint8`.

---

### `run(img, blur_radius, intensity)`

**Signature:**
```python
def run(img, blur_radius=21, intensity=1.0)
```

**Description:**
Executes the complete pencil sketch pipeline in sequence and returns
every intermediate result in a dictionary. The UI uses this dictionary
to render both the final result and the step-by-step pipeline view
without recomputing anything.

**Pipeline order:**
1. `to_grayscale` → `gray`
2. `invert` → `inverted`
3. `gaussian_blur` → `blurred`
4. `color_dodge` → `sketch`
5. *(optional)* intensity blend → updated `sketch`

**Intensity blending:**
When `intensity < 1.0`, the sketch is linearly blended back toward the
grayscale image using OpenCV's `addWeighted`:
```
Out = α · S + (1 - α) · G
```
Where `α = intensity`. At `intensity = 1.0` this step is skipped entirely.

**Parameters:**
- `img` — NumPy array of shape `(H, W, 3)`, dtype `uint8`, BGR order (OpenCV default).
- `blur_radius` — Passed to `gaussian_blur`. Default `21`.
- `intensity` — Float in `[0.1, 1.0]`. Controls how strongly the sketch
  effect is applied. Default `1.0` (full sketch).

**Returns:**
Dictionary with keys:

| Key | Type | Description |
|---|---|---|
| `"original"` | `(H, W, 3) uint8` | Original BGR image |
| `"grayscale"` | `(H, W) uint8` | After `to_grayscale` |
| `"inverted"` | `(H, W) uint8` | After `invert` |
| `"blurred"` | `(H, W) uint8` | After `gaussian_blur` |
| `"sketch"` | `(H, W) uint8` | Final pencil sketch |

---

## Module: `sketching/edge_detection.py`

Implements three classical edge detection algorithms — **Sobel**, **Laplacian**,
and **Canny**, sharing a common preprocessing pipeline (grayscale conversion
followed by Gaussian smoothing).

### Theory primer

An edge is a location where image intensity changes sharply. The two ways to
detect such locations are:

- **First-derivative methods** (Sobel) — compute the gradient ∇I and look for
  large magnitudes.
- **Second-derivative methods** (Laplacian) — compute ∇²I and look for
  zero-crossings or large absolute values.

Pre-smoothing with a Gaussian is essential because differentiation amplifies
high-frequency noise.

---

### `to_grayscale(img)` and `smooth(gray, ksize)`

Same conventions as in `pencil_sketch.py`:
- `to_grayscale` calls `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`.
- `smooth` applies `cv2.GaussianBlur(gray, (k, k), 0)`, forcing an odd kernel
  size.

---

### `sobel(gray, ksize=3)`

**Signature:**
```python
def sobel(gray, ksize=3)
```

**Description:**
Computes the horizontal gradient `Gx`, the vertical gradient `Gy`, and the
gradient magnitude `‖∇I‖`. Sobel kernels approximate the first derivative
along each axis:

```
        ⎡ -1  0  +1 ⎤              ⎡ -1  -2  -1 ⎤
Sx =    ⎢ -2  0  +2 ⎥      Sy =    ⎢  0   0   0 ⎥
        ⎣ -1  0  +1 ⎦              ⎣ +1  +2  +1 ⎦
```

**Formula:**
```
Gx = Sx ∗ I        Gy = Sy ∗ I        ‖∇I‖ = √(Gx² + Gy²)
```

**Parameters:**
- `gray` — single-channel `uint8` image.
- `ksize` — kernel size (1, 3, 5, or 7). OpenCV uses `cv2.CV_64F` to avoid
  overflow in the signed gradient.

**Returns:**
Tuple `(grad_x, grad_y, magnitude)`:
- `grad_x`, `grad_y` — `float64` arrays, raw signed gradients.
- `magnitude` — `uint8` image, normalized to `[0, 255]` via `cv2.normalize`.

**OpenCV calls used:** `cv2.Sobel`, `cv2.magnitude`, `cv2.normalize`.

---

### `laplacian(gray, ksize=3)`

**Signature:**
```python
def laplacian(gray, ksize=3)
```

**Description:**
Applies the discrete Laplacian operator — the sum of unmixed second
derivatives along each axis. The classic 3×3 Laplacian kernel is:

```
       ⎡  0  -1   0 ⎤
L =    ⎢ -1   4  -1 ⎥
       ⎣  0  -1   0 ⎦
```

**Formula:**
```
∇²I = ∂²I/∂x² + ∂²I/∂y²
```

The result is converted to an unsigned 8-bit image with
`cv2.convertScaleAbs` (absolute value, then clip to `[0, 255]`).

**Parameters:**
- `gray` — single-channel `uint8` image.
- `ksize` — kernel size (forced odd, typically 1, 3, 5, or 7).

**Returns:**
- `uint8` array of the same shape as `gray`.

**OpenCV calls used:** `cv2.Laplacian`, `cv2.convertScaleAbs`.

---

### `canny(gray, low=50, high=150)`

**Signature:**
```python
def canny(gray, low=50, high=150)
```

**Description:**
Runs the **Canny edge detector**, a multi-stage algorithm:

1. **Gaussian smoothing** (already applied by `smooth` upstream).
2. **Sobel gradient** computation.
3. **Non-maximum suppression** — thin gradient ridges to one-pixel-wide edges.
4. **Double thresholding** with `low` and `high`.
5. **Edge tracking by hysteresis** — only edges connected to a strong-edge
   pixel are kept.

The result is a binary `uint8` image where edges are `255` and everything
else is `0`.

**Parameters:**
- `gray` — single-channel `uint8` image.
- `low`, `high` — hysteresis thresholds. A common heuristic is `low ≈ high / 2`.

**Returns:**
- Binary `uint8` array.

**OpenCV call used:** `cv2.Canny`.

---

### `run(img, method, ksize, low, high, smoothing)`

**Signature:**
```python
def run(img, method="Sobel", ksize=3, low=50, high=150, smoothing=5)
```

**Description:**
Top-level dispatcher. Converts the image to grayscale, applies Gaussian
pre-smoothing, then routes to one of the three edge detectors based on
`method`.

**Parameters:**
- `img` — BGR image as returned by `cv2.imdecode`.
- `method` — `"Sobel"`, `"Laplacian"`, or `"Canny"`.
- `ksize` — used by Sobel and Laplacian.
- `low`, `high` — used by Canny.
- `smoothing` — Gaussian pre-smoothing kernel size.

**Returns:**
Dictionary. Common keys for all methods:

| Key | Description |
|---|---|
| `"original"` | Original BGR image |
| `"grayscale"` | Grayscale conversion |
| `"blurred"` | After Gaussian pre-smoothing |
| `"edges"` | Final edge image (`uint8`) |
| `"method"` | The method name (string) |
| `"smoothing"` | The pre-smoothing kernel size |

Sobel additionally returns `"grad_x"`, `"grad_y"`, and `"ksize"`.
Laplacian additionally returns `"ksize"`.
Canny additionally returns `"low"` and `"high"`.

---

## Module: `sketching/hatching.py`

Implements **directional hatching** — a sketching effect where the strokes
follow the local edge orientation. It builds directly on the Sobel operator
from `edge_detection.py`, but instead of using only the gradient *magnitude*,
it also exploits the gradient *direction* (the angle of steepest intensity
change).

### Theory primer

A real pencil-and-paper hatching artist draws **along** edges, not across
them. The direction of an edge at pixel `(x, y)` is perpendicular to the
gradient direction:

```
gradient direction  θ = atan2(Gy, Gx)
edge direction      φ = θ + 90°    (mod 180°)
```

Because a line is bidirectional, we treat angles modulo 180° (so 30° and
210° are the same orientation).

The algorithm quantizes φ into a small number of bins (typically 4 or 8),
generates one parallel-line texture per bin, then composites the textures
onto a white canvas — using the bin index to pick the texture and the
gradient magnitude as a mask.

---

### `gradient_polar(gray)`

**Signature:**
```python
def gradient_polar(gray)
```

**Description:**
Computes the Sobel gradients `Gx` and `Gy`, then converts them to **polar
form**: magnitude `‖∇I‖` and direction `θ`. The direction is returned in
degrees and folded into `[0, 180)` so that opposite-pointing vectors
(`θ` and `θ + 180°`) collapse into the same orientation, since hatching
strokes are direction-agnostic.

**Formulas:**
```
Gx = ∂I/∂x        Gy = ∂I/∂y
‖∇I‖ = √(Gx² + Gy²)
θ    = (atan2(Gy, Gx) + 180°) mod 180°
```

**Returns:**
- `magnitude` — `float64` array, same shape as input
- `direction` — `float64` array, values in `[0, 180)`

---

### `visualize_direction(magnitude, direction)`

**Signature:**
```python
def visualize_direction(magnitude, direction)
```

**Description:**
Produces a color visualization of the gradient field for the pipeline view.
The image is built in HSV space:

| Channel | Mapping |
|---|---|
| **H** (Hue) | gradient direction `θ` (since OpenCV uses hue range `[0, 179]`, this matches the `[0, 180)` direction range directly) |
| **S** (Saturation) | fixed at 255 |
| **V** (Value) | normalized magnitude `‖∇I‖` |

The result is converted to BGR via `cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)`.
Edges glow brightly in distinct colors per orientation; flat areas appear
black.

---

### `quantize_direction(direction, n_bins=4)`

**Signature:**
```python
def quantize_direction(direction, n_bins=4)
```

**Description:**
Rounds each direction value to the nearest of `n_bins` evenly-spaced bin
centers. With `n_bins=4`, the bin centers are 22.5°, 67.5°, 112.5°, 157.5°
— i.e., diagonal, vertical-ish, anti-diagonal, horizontal-ish.

**Formula:**
```
bin_index = ((θ + bin_width / 2) // bin_width) mod n_bins
where bin_width = 180° / n_bins
```

**Returns:**
- Integer array, same shape as `direction`, with values in `[0, n_bins)`.

---

### `make_hatching_texture(shape, angle_deg, spacing=6, thickness=1)`

**Signature:**
```python
def make_hatching_texture(shape, angle_deg, spacing=6, thickness=1)
```

**Description:**
Generates a full-image hatching pattern — parallel dark lines on a white
background, at the requested angle. Lines are drawn with `cv2.line` along
the diagonal so they always cover the entire image regardless of angle.

**Parameters:**
- `shape` — tuple `(height, width)` of the output texture
- `angle_deg` — line orientation in degrees
- `spacing` — pixels between adjacent parallel lines
- `thickness` — line thickness in pixels

**Returns:**
- `uint8` array of shape `(H, W)`. White (255) background, black (0) lines.

---

### `run(img, smoothing, spacing, n_bins, threshold)`

**Signature:**
```python
def run(img, smoothing=5, spacing=6, n_bins=4, threshold=30)
```

**Description:**
Top-level pipeline.

**Steps:**
1. Convert to grayscale (`cv2.cvtColor`).
2. Smooth with Gaussian (`cv2.GaussianBlur`) — reduces noise before
   differentiation.
3. Compute polar-form gradient (`gradient_polar`).
4. Rotate direction by 90° to get edge orientation (perpendicular to
   gradient).
5. Quantize the edge orientation into `n_bins` bins.
6. Build one full-image hatching texture per bin via
   `make_hatching_texture`.
7. Build an edge mask by thresholding the normalized gradient magnitude.
8. Initialize a white canvas. For each bin `i`, copy texture pixels from
   `textures[i]` into the canvas wherever the bin matches **and** the edge
   mask is set.

**Parameters:**
- `img` — BGR image from `cv2.imdecode`
- `smoothing` — Gaussian pre-smoothing kernel (odd)
- `spacing` — pixel spacing between strokes in each hatching texture
- `n_bins` — number of stroke orientations (2, 3, 4, 6, or 8)
- `threshold` — minimum normalized magnitude (0–255) for a pixel to get a stroke

**Returns:**
Dictionary with keys:

| Key | Type | Description |
|---|---|---|
| `"original"` | `(H, W, 3) uint8` | Original BGR image |
| `"grayscale"` | `(H, W) uint8` | After grayscale conversion |
| `"blurred"` | `(H, W) uint8` | After Gaussian smoothing |
| `"magnitude"` | `(H, W) uint8` | Normalized gradient magnitude |
| `"direction_viz"` | `(H, W, 3) uint8` | HSV-encoded direction map (BGR) |
| `"quantized"` | `(H, W) uint8` | Quantized bin indices, scaled for display |
| `"edge_mask"` | `(H, W) uint8` | Binary mask, 0 or 255 |
| `"hatched"` | `(H, W) uint8` | Final hatched sketch |
| `"n_bins"`, `"spacing"`, `"threshold"`, `"smoothing"` | int | Echo of the params for the UI |

---

## Application: `app.py`

The Streamlit application. It is the single entry point — run with
`streamlit run app.py`.

### Page configuration

Sets the browser tab title to **"TraceLight"**, uses a minimal half-disc glyph
(◐) as a favicon, and sets the layout to `wide` so the two-column result view
has room to breathe. A custom CSS block (injected via `st.markdown` with
`unsafe_allow_html=True`) overrides Streamlit's default look — Inter and
Fraunces from Google Fonts, a warm amber accent (`#c97a3f`), tightened
typography, and hidden default chrome (hamburger menu, footer, deploy button).

---

### Sidebar

The sidebar contains all user controls. Parameter widgets are rendered
**conditionally** based on the selected effect — a `params` dict is built up
inside an `if effect == ...` block and later passed to the relevant `run()`
function via `**params`.

**Always-visible controls:**

| Control | Widget | Range / Options | Description |
|---|---|---|---|
| Image upload | `st.file_uploader` | PNG, JPG, JPEG, BMP, WEBP | Uploads the source image |
| Effect | `st.selectbox` | `Pencil sketch`, `Edge detection`, `Directional hatching` | Top-level effect router |

**Pencil sketch parameters:**

| Control | Widget | Range / Options | Description |
|---|---|---|---|
| Blur radius | `st.slider` | 3–101, step 2 | Kernel size for Gaussian blur |
| Intensity | `st.slider` | 0.1–1.0, step 0.05 | Blend strength of the effect |

**Edge detection parameters:**

| Control | Widget | Range / Options | Description |
|---|---|---|---|
| Method | `st.selectbox` | `Sobel`, `Laplacian`, `Canny` | Edge detection algorithm |
| Pre-smoothing | `st.slider` | 1–21, step 2 | Gaussian blur kernel before differentiation |
| Kernel size | `st.select_slider` | 1, 3, 5, 7 | Sobel / Laplacian differentiation kernel (hidden for Canny) |
| Lower threshold | `st.slider` | 0–255 | Canny hysteresis low (hidden for others) |
| Upper threshold | `st.slider` | 0–255 | Canny hysteresis high (hidden for others) |

**Directional hatching parameters:**

| Control | Widget | Range / Options | Description |
|---|---|---|---|
| Pre-smoothing | `st.slider` | 1–21, step 2 | Gaussian blur kernel before gradient computation |
| Stroke orientations | `st.select_slider` | 2, 3, 4, 6, 8 | Number of discrete hatching directions |
| Stroke spacing | `st.slider` | 3–20 | Pixels between parallel strokes in each texture |
| Edge threshold | `st.slider` | 0–255 | Minimum gradient magnitude to draw a stroke |

If no image has been uploaded, `st.stop()` halts the app and shows the
empty-state card. Nothing below the guard executes until a file is provided.

### Effect dispatch

After loading the image, a single `if effect == ...` block decides which
module to call and builds the `pipeline_steps` list for the Pipeline tab. The
final image to display (and download) is exposed as `output_img`, regardless
of which effect produced it — this keeps the tab rendering code generic.

---

### Image loading

The uploaded file bytes are read from Streamlit's `UploadedFile` object
and decoded using OpenCV:

```python
file_bytes = np.frombuffer(uploaded.read(), np.uint8)
img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
```

`cv2.IMREAD_COLOR` always loads the image as a 3-channel BGR image,
regardless of the original format (RGBA PNG, grayscale, etc.), ensuring
consistent input for the algorithm. No Pillow dependency is needed.

When displaying the original image in Streamlit (`st.image`), it is
converted from BGR to RGB with `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`,
since Streamlit expects RGB. All other processing stays in BGR.

---

### Processing

`pencil_sketch.run()` is called inside `st.spinner` so the user sees a
loading indicator while the image is being processed. The returned
dictionary is reused across all three tabs.

---

### Tab: Result

Displays the original image and the pencil sketch side by side in a
two-column layout. Below the images, a `st.download_button` lets the
user save the sketch as a PNG file. The sketch is encoded in memory
using `cv2.imencode(".png", result["sketch"])` and the resulting byte
buffer is passed directly to the download button — no Pillow needed.

---

### Tab: Pipeline

**Step visualization:**
Renders all five intermediate images (Original → Grayscale → Inverted →
Gaussian Blur → Pencil Sketch) side by side using a single Matplotlib
figure with 5 subplots. Each subplot shows:
- The intermediate image (grayscale colormap for single-channel steps)
- The step name as the title
- The mathematical formula as the x-axis label

The figure background is set to Streamlit's dark background color
(`#0e1117`) so it blends with the app theme.

**Intensity histogram:**
A second Matplotlib figure shows pixel-intensity histograms for the
grayscale image and the final sketch side by side. This lets the user
observe how the color dodge operation shifts the distribution — the sketch
typically shows a strongly bimodal histogram (dark lines + white paper)
compared to the broader grayscale distribution.

Both figures are closed with `plt.close()` immediately after rendering to
release memory.

---

---

## Algorithm Summary

### Pencil sketch

```
Input: BGR image  (cv2.imdecode)
  │
  ▼
[1] Grayscale conversion     cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    Y = 0.299R + 0.587G + 0.114B
  │
  ▼
[2] Inversion                inverted = 255 - gray
  │
  ▼
[3] Gaussian blur            cv2.GaussianBlur(inverted, (k, k), 0)
  │
  ▼
[4] Color dodge blend        S = min(gray * 255 / (255 - blurred + ε), 255)
  │
  ▼
[5] Intensity blend          cv2.addWeighted(sketch, α, gray, 1-α, 0)
    (only if α < 1.0)
  │
  ▼
Output: Pencil sketch  (H, W) uint8 grayscale
```

### Edge detection — Sobel

```
Input: BGR image
  │
  ▼
[1] Grayscale          cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  │
  ▼
[2] Gaussian smoothing cv2.GaussianBlur(gray, (s, s), 0)
  │
  ▼
[3] Gradient X         Gx = cv2.Sobel(blurred, CV_64F, 1, 0, ksize=k)
[4] Gradient Y         Gy = cv2.Sobel(blurred, CV_64F, 0, 1, ksize=k)
  │
  ▼
[5] Magnitude          ‖∇I‖ = √(Gx² + Gy²)   then normalize to [0, 255]
  │
  ▼
Output: Edge image (uint8)
```

### Edge detection — Laplacian

```
Input: BGR image
  │
  ▼
[1] Grayscale          cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  │
  ▼
[2] Gaussian smoothing cv2.GaussianBlur(gray, (s, s), 0)
  │
  ▼
[3] Laplacian          L = cv2.Laplacian(blurred, CV_64F, ksize=k)
                       ∇²I = ∂²I/∂x² + ∂²I/∂y²
  │
  ▼
[4] Absolute scale     cv2.convertScaleAbs(L)
  │
  ▼
Output: Edge image (uint8)
```

### Edge detection — Canny

```
Input: BGR image
  │
  ▼
[1] Grayscale          cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  │
  ▼
[2] Gaussian smoothing cv2.GaussianBlur(gray, (s, s), 0)
  │
  ▼
[3] Canny              cv2.Canny(blurred, low, high)
    ├─ Sobel gradients
    ├─ Non-maximum suppression
    ├─ Double thresholding (low, high)
    └─ Hysteresis edge tracking
  │
  ▼
Output: Binary edge image (uint8)
```

### Directional hatching

```
Input: BGR image
  │
  ▼
[1] Grayscale          cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  │
  ▼
[2] Gaussian smoothing cv2.GaussianBlur(gray, (s, s), 0)
  │
  ▼
[3] Polar gradient     Gx, Gy via Sobel
                       ‖∇I‖ = √(Gx² + Gy²)
                       θ    = atan2(Gy, Gx)  mod 180°
  │
  ▼
[4] Edge orientation   φ = (θ + 90°) mod 180°
  │
  ▼
[5] Quantize           bin = round(φ / (180° / N))   ∈ {0, ..., N-1}
  │
  ▼
[6] Build N textures   parallel-line patterns at angles (i + 0.5) · 180°/N
  │
  ▼
[7] Edge mask          mask = (‖∇I‖_norm > threshold)
  │
  ▼
[8] Composite          canvas = white;
                       for each bin i:
                         canvas[ (bin == i) & mask ] = textures[i]
  │
  ▼
Output: Hatched sketch (H, W) uint8
```
