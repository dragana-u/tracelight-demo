import cv2
import numpy as np
import streamlit as st
from matplotlib import pyplot as plt

from sketching import edge_detection, hatching, pencil_sketch

st.set_page_config(
    page_title="TraceLight",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&display=swap');

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    .stDeployButton {display: none;}

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    }

    .stApp {
        background:
            radial-gradient(1200px 600px at 80% -10%, rgba(180, 140, 100, 0.06), transparent),
            radial-gradient(900px 500px at 10% 110%, rgba(100, 130, 180, 0.05), transparent);
    }

    .brand-wrap {
        padding: 0.5rem 0 2rem 0;
        border-bottom: 1px solid rgba(128,128,128,0.15);
        margin-bottom: 2rem;
    }
    .brand-mark {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 500;
        font-size: 2.4rem;
        letter-spacing: -0.02em;
        line-height: 1;
        margin: 0;
    }
    .brand-mark .dot {
        color: #c97a3f;
        font-weight: 600;
    }
    .brand-sub {
        font-size: 0.92rem;
        color: rgba(150,150,150,0.95);
        margin-top: 0.35rem;
        letter-spacing: 0.01em;
        font-weight: 400;
    }
    .brand-meta {
        font-size: 0.78rem;
        color: rgba(150,150,150,0.7);
        margin-top: 0.2rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.12);
    }
    section[data-testid="stSidebar"] h2 {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(150,150,150,0.85) !important;
        margin-top: 1.6rem !important;
        margin-bottom: 0.6rem !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(128,128,128,0.04);
        border: 1px dashed rgba(128,128,128,0.35);
        border-radius: 10px;
        transition: all 0.15s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #c97a3f;
        background: rgba(201,122,63,0.05);
    }

    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        font-weight: 500;
        letter-spacing: 0.01em;
        padding: 0.5rem 0.2rem;
        margin-right: 1.6rem;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #c97a3f !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #c97a3f !important;
        height: 2px !important;
    }

    .img-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: rgba(150,150,150,0.85);
        margin-bottom: 0.6rem;
    }

    [data-testid="stImage"] img {
        border-radius: 6px;
        box-shadow:
            0 1px 2px rgba(0,0,0,0.08),
            0 8px 24px rgba(0,0,0,0.10);
    }

    .stDownloadButton button, .stButton button {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.88rem;
        border-radius: 8px;
        padding: 0.5rem 1.1rem;
        border: 1px solid rgba(128,128,128,0.25);
        transition: all 0.15s ease;
    }
    .stDownloadButton button:hover, .stButton button:hover {
        border-color: #c97a3f;
        color: #c97a3f;
    }

    [data-baseweb="slider"] [role="slider"] {
        background-color: #c97a3f !important;
    }

    .empty-card {
        border: 1px dashed rgba(128,128,128,0.25);
        border-radius: 14px;
        padding: 4rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    .empty-card h3 {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 500;
        font-size: 1.4rem;
        margin: 0 0 0.6rem 0;
    }
    .empty-card p {
        color: rgba(150,150,150,0.9);
        font-size: 0.92rem;
        margin: 0;
    }

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="brand-wrap">
        <h1 class="brand-mark">TraceLight<span class="dot">.</span></h1>
    </div>
    """,
    unsafe_allow_html=True,
)

EFFECTS = ["Pencil sketch", "Edge detection", "Directional hatching"]

with st.sidebar:
    st.markdown("## Source")
    uploaded = st.file_uploader(
        "Drop an image or browse",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
        label_visibility="collapsed",
    )

    st.markdown("## Effect")
    effect = st.selectbox(
        "Effect",
        EFFECTS,
        label_visibility="collapsed",
    )

    st.markdown("## Parameters")

    params = {}

    if effect == "Pencil sketch":
        params["blur_radius"] = st.slider(
            "Blur radius", 3, 101, 21, step=2,
            help="Higher = softer, broader strokes.",
        )
        params["intensity"] = st.slider(
            "Intensity", 0.1, 1.0, 1.0, step=0.05,
            help="Blend strength: 1.0 = full sketch.",
        )

    elif effect == "Edge detection":
        params["method"] = st.selectbox(
            "Method",
            ["Sobel", "Laplacian", "Canny"],
            help="Algorithm used to detect edges.",
        )
        params["smoothing"] = st.slider(
            "Pre-smoothing", 1, 21, 5, step=2,
            help="Gaussian blur kernel size applied before edge detection.",
        )

        if params["method"] in ("Sobel", "Laplacian"):
            params["ksize"] = st.select_slider(
                "Kernel size",
                options=[1, 3, 5, 7],
                value=3,
                help="Size of the differentiation kernel.",
            )
        else:
            params["low"] = st.slider(
                "Lower threshold", 0, 255, 50,
                help="Edges below this gradient are discarded.",
            )
            params["high"] = st.slider(
                "Upper threshold", 0, 255, 150,
                help="Edges above this gradient are kept as strong edges.",
            )

    elif effect == "Directional hatching":
        params["smoothing"] = st.slider(
            "Pre-smoothing", 1, 21, 5, step=2,
            help="Gaussian blur kernel size before gradient computation.",
        )
        params["n_bins"] = st.select_slider(
            "Stroke orientations",
            options=[2, 3, 4, 6, 8],
            value=4,
            help="Number of discrete stroke directions.",
        )
        params["spacing"] = st.slider(
            "Stroke spacing", 3, 20, 6,
            help="Pixels between parallel strokes in the hatching pattern.",
        )
        params["threshold"] = st.slider(
            "Edge threshold", 0, 255, 30,
            help="Minimum gradient magnitude for a stroke to be drawn.",
        )

if uploaded is None:
    st.markdown(
        """
        <div class="empty-card">
            <h3>No image yet</h3>
            <p>Upload a photo from the panel on the left to see the result.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

file_bytes = np.frombuffer(uploaded.read(), np.uint8)
img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

with st.spinner(""):
    if effect == "Pencil sketch":
        result = pencil_sketch.run(img, **params)
        output_img = result["sketch"]
        output_label = "Pencil sketch"
        pipeline_steps = [
            ("01 · Original", cv2.cvtColor(result["original"], cv2.COLOR_BGR2RGB), "BGR → RGB for display"),
            ("02 · Grayscale", result["grayscale"], "Y = 0.299R + 0.587G + 0.114B"),
            ("03 · Inverted", result["inverted"], "I_inv = 255 − I"),
            ("04 · Gaussian blur", result["blurred"], f"kernel {params['blur_radius']}×{params['blur_radius']}"),
            ("05 · Color dodge", result["sketch"], "S = G·255 / (255 − B)"),
        ]
        hist_pairs = [
            (result["grayscale"], "Grayscale", "#7a93ad"),
            (result["sketch"], "Pencil sketch", "#c97a3f"),
        ]

    elif effect == "Directional hatching":
        result = hatching.run(img, **params)
        output_img = result["hatched"]
        output_label = "Hatched sketch"
        pipeline_steps = [
            ("01 · Original", cv2.cvtColor(result["original"], cv2.COLOR_BGR2RGB), "BGR input"),
            ("02 · Grayscale", result["grayscale"], "cvtColor BGR2GRAY"),
            ("03 · Gaussian blur", result["blurred"], f"kernel {result['smoothing']}×{result['smoothing']}"),
            ("04 · Magnitude", result["magnitude"], "‖∇I‖ = √(Gx² + Gy²)"),
            ("05 · Direction", cv2.cvtColor(result["direction_viz"], cv2.COLOR_BGR2RGB), "θ = atan2(Gy, Gx) → hue"),
            ("06 · Quantized θ", result["quantized"], f"{result['n_bins']} orientation bins"),
            ("07 · Edge mask", result["edge_mask"], f"‖∇I‖ > {result['threshold']}"),
            ("08 · Hatched", result["hatched"], f"directional strokes, spacing {result['spacing']}px"),
        ]
        hist_pairs = [
            (result["grayscale"], "Grayscale", "#7a93ad"),
            (result["hatched"], "Hatched sketch", "#c97a3f"),
        ]

    else:
        result = edge_detection.run(img, **params)
        output_img = result["edges"]
        method = result["method"]
        output_label = f"{method} edges"

        if method == "Sobel":
            pipeline_steps = [
                ("01 · Original", cv2.cvtColor(result["original"], cv2.COLOR_BGR2RGB), "BGR input"),
                ("02 · Grayscale", result["grayscale"], "cvtColor BGR2GRAY"),
                ("03 · Gaussian blur", result["blurred"], f"kernel {result['smoothing']}×{result['smoothing']}"),
                ("04 · Gradient X", result["grad_x"], "Gx = ∂I/∂x"),
                ("05 · Gradient Y", result["grad_y"], "Gy = ∂I/∂y"),
                ("06 · Magnitude", result["edges"], "‖∇I‖ = √(Gx² + Gy²)"),
            ]
        elif method == "Laplacian":
            pipeline_steps = [
                ("01 · Original", cv2.cvtColor(result["original"], cv2.COLOR_BGR2RGB), "BGR input"),
                ("02 · Grayscale", result["grayscale"], "cvtColor BGR2GRAY"),
                ("03 · Gaussian blur", result["blurred"], f"kernel {result['smoothing']}×{result['smoothing']}"),
                ("04 · Laplacian", result["edges"], "∇²I = ∂²I/∂x² + ∂²I/∂y²"),
            ]
        else:
            pipeline_steps = [
                ("01 · Original", cv2.cvtColor(result["original"], cv2.COLOR_BGR2RGB), "BGR input"),
                ("02 · Grayscale", result["grayscale"], "cvtColor BGR2GRAY"),
                ("03 · Gaussian blur", result["blurred"], f"kernel {result['smoothing']}×{result['smoothing']}"),
                ("04 · Canny edges", result["edges"], f"thresholds {result['low']} / {result['high']}"),
            ]

        hist_pairs = [
            (result["grayscale"], "Grayscale", "#7a93ad"),
            (result["edges"], f"{method} edges", "#c97a3f"),
        ]

tab_result, tab_pipeline = st.tabs(["Result", "Pipeline"])

with tab_result:
    col_orig, col_out = st.columns(2, gap="large")

    with col_orig:
        st.markdown('<div class="img-label">Original</div>', unsafe_allow_html=True)
        st.image(
            cv2.cvtColor(result["original"], cv2.COLOR_BGR2RGB),
            use_container_width=True,
        )

    with col_out:
        st.markdown(
            f'<div class="img-label">{output_label}</div>',
            unsafe_allow_html=True,
        )
        st.image(output_img, use_container_width=True, clamp=True)

    st.write("")
    _, buffer = cv2.imencode(".png", output_img)
    st.download_button(
        label="Download PNG",
        data=buffer.tobytes(),
        file_name=f"{effect.lower().replace(' ', '_')}.png",
        mime="image/png",
    )

with tab_pipeline:
    st.markdown('<div class="img-label">Processing steps</div>', unsafe_allow_html=True)

    n_steps = len(pipeline_steps)
    fig, axes = plt.subplots(1, n_steps, figsize=(3.6 * n_steps, 4.2))
    fig.patch.set_alpha(0.0)

    if n_steps == 1:
        axes = [axes]

    for ax, (title, step_img, formula) in zip(axes, pipeline_steps):
        cmap = "gray" if step_img.ndim == 2 else None
        ax.imshow(step_img, cmap=cmap)
        ax.set_title(title, fontsize=9.5, color="#888", pad=10,
                     fontfamily="DejaVu Sans", loc="left")
        ax.set_xlabel(formula, fontsize=7.5, color="#888", labelpad=6)
        ax.set_facecolor("none")
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.write("")
    st.markdown('<div class="img-label">Intensity distribution</div>', unsafe_allow_html=True)

    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 3.2))
    fig2.patch.set_alpha(0.0)

    for ax, (data, label, color) in zip(axes2, hist_pairs):
        ax.hist(data.flatten(), 256, [0, 256], color=color, alpha=0.9, edgecolor="none")
        ax.set_title(label, color="#888", fontsize=9.5, loc="left", pad=8)
        ax.set_facecolor("none")
        ax.set_xlim([0, 256])
        ax.tick_params(colors="#888", labelsize=7.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#444")
            ax.spines[side].set_linewidth(0.6)

    plt.tight_layout()
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)
