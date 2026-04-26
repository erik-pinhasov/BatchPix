"""
Self-contained 360° viewer HTML generator.
Produces a single HTML file with embedded JS/CSS that works offline.
"""


def generate_viewer_html(config, sprite_filename):
    """
    Generate a self-contained HTML file for the 360° spin viewer.
    
    Args:
        config: dict with keys: totalFrames, cols, frameSizePx, spriteSheetName
        sprite_filename: filename of the sprite sheet image (e.g. 'product_sprite.webp')
        
    Returns:
        str: Complete HTML document as a string
    """
    frame_size = config['frameSizePx']
    cols = config['cols']
    total_frames = config['totalFrames']

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>360° Product View</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #f0f2f5;
        }}

        .viewer-wrapper {{
            width: {frame_size}px;
            height: {frame_size}px;
            max-width: 95vw;
            max-height: 95vw;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
            cursor: grab;
            touch-action: none;
            user-select: none;
        }}

        .viewer-wrapper:active {{
            cursor: grabbing;
        }}

        .product-image {{
            width: 100%;
            height: 100%;
            background-repeat: no-repeat;
            background-position: 0 0;
        }}

        .hint {{
            position: absolute;
            bottom: 20px;
            width: 100%;
            text-align: center;
            color: #aaa;
            font-size: 14px;
            pointer-events: none;
            transition: opacity 0.6s ease;
        }}

        .hint.hidden {{
            opacity: 0;
        }}

        /* Loading spinner */
        .loader {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            border: 4px solid #e0e0e0;
            border-top-color: #437196;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}

        .loader.hidden {{
            display: none;
        }}

        @keyframes spin {{
            to {{ transform: translate(-50%, -50%) rotate(360deg); }}
        }}
    </style>
</head>
<body>

    <div class="viewer-wrapper" id="viewer">
        <div class="product-image" id="product-image"></div>
        <div class="loader" id="loader"></div>
        <div class="hint" id="hint">↔ Drag to Rotate</div>
    </div>

    <script>
    (function() {{
        const CONFIG = {{
            totalFrames: {total_frames},
            cols: {cols},
            frameSizePx: {frame_size}
        }};
        const SPRITE_URL = './{sprite_filename}';
        const SENSITIVITY = 10;
        const AUTO_SPIN_INTERVAL = 120; // ms between auto-spin frames

        const viewer  = document.getElementById('viewer');
        const imgEl   = document.getElementById('product-image');
        const loader  = document.getElementById('loader');
        const hint    = document.getElementById('hint');

        let currentFrame = 0;
        let isDragging   = false;
        let startX       = 0;
        let lastFrame    = 0;
        let autoSpinId   = null;
        let hasInteracted = false;

        // Set background size based on columns
        imgEl.style.backgroundSize = (CONFIG.cols * 100) + '%';

        function updateView() {{
            const col  = currentFrame % CONFIG.cols;
            const row  = Math.floor(currentFrame / CONFIG.cols);
            const rows = Math.ceil(CONFIG.totalFrames / CONFIG.cols);
            const xPos = CONFIG.cols > 1 ? (col / (CONFIG.cols - 1)) * 100 : 0;
            const yPos = rows > 1 ? (row / (rows - 1)) * 100 : 0;
            imgEl.style.backgroundPosition = xPos + '% ' + yPos + '%';
        }}

        function startAutoSpin() {{
            if (autoSpinId) return;
            autoSpinId = setInterval(function() {{
                currentFrame = (currentFrame + 1) % CONFIG.totalFrames;
                updateView();
            }}, AUTO_SPIN_INTERVAL);
        }}

        function stopAutoSpin() {{
            if (autoSpinId) {{
                clearInterval(autoSpinId);
                autoSpinId = null;
            }}
        }}

        // --- Drag handlers ---
        function onStart(e) {{
            e.preventDefault();
            isDragging = true;
            startX = e.clientX || e.touches[0].clientX;
            lastFrame = currentFrame;

            if (!hasInteracted) {{
                hasInteracted = true;
                stopAutoSpin();
                hint.classList.add('hidden');
            }}
        }}

        function onMove(e) {{
            if (!isDragging) return;
            var x = e.clientX !== undefined ? e.clientX : e.touches[0].clientX;
            var change = Math.floor((x - startX) / SENSITIVITY);
            var next = (lastFrame - change) % CONFIG.totalFrames;
            if (next < 0) next += CONFIG.totalFrames;
            if (next !== currentFrame) {{
                currentFrame = next;
                updateView();
            }}
        }}

        function onEnd() {{
            isDragging = false;
        }}

        viewer.addEventListener('mousedown',  onStart);
        viewer.addEventListener('touchstart', onStart);
        window.addEventListener('mousemove',  onMove);
        window.addEventListener('touchmove',  onMove);
        window.addEventListener('mouseup',    onEnd);
        window.addEventListener('touchend',   onEnd);

        // --- Load sprite sheet ---
        viewer.style.opacity = '0';
        var tempImg = new Image();
        tempImg.onload = function() {{
            imgEl.style.backgroundImage = "url('" + SPRITE_URL + "')";
            loader.classList.add('hidden');
            viewer.style.opacity = '1';
            viewer.style.transition = 'opacity 0.3s ease';
            startAutoSpin();
        }};
        tempImg.onerror = function() {{
            loader.classList.add('hidden');
            hint.textContent = 'Error loading sprite sheet';
            hint.classList.remove('hidden');
            viewer.style.opacity = '1';
        }};
        tempImg.src = SPRITE_URL;
    }})();
    </script>
</body>
</html>'''
