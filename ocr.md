You are a senior computer vision and Python engineer.

Your task is to implement a **Numbered Musical Notation (简谱) symbol detection pipeline** from images.

The goal is NOT to understand music theory.
The goal is purely **visual detection of symbols with bounding boxes**.

The system must detect symbols from numbered musical notation images and output a structured JSON.

---

# Overall Architecture

The pipeline should combine three methods:

1. OCR (Aliyun OCR API)
2. Vision LLM (Aliyun Vision model)
3. Traditional Computer Vision (OpenCV)

Each method detects different symbol types.

Final result = merge detections from all three.

---

# Symbols to Detect

Detect the following visual symbols:

Numbers:

- 1
- 2
- 3
- 4
- 5
- 6
- 7
- 0

Modifiers:

- dot_above
- dot_below
- dot_after (duration dot)

Structure:

- barline
- double_barline
- repeat_start
- repeat_end

Articulation:

- slur
- tie

Other:

- rest
- dash (sustain line)

---

# Input

Input is a **numbered musical notation image**.

Example:

input/
score1.png
score2.jpg

---

# Output Format

Output must be JSON.

Example:

{
"image": "score1.png",
"symbols": [
{
"type": "number",
"value": "5",
"bbox": [120, 340, 28, 30],
"confidence": 0.98,
"source": "ocr"
},
{
"type": "dot_above",
"bbox": [150, 310, 8, 8],
"confidence": 0.85,
"source": "vision_llm"
},
{
"type": "barline",
"bbox": [420, 100, 4, 220],
"confidence": 0.92,
"source": "opencv"
}
]
}

bbox format:

[x, y, width, height]

Coordinates are pixel-based relative to the image.

---

# Module Design

Implement the system as modular Python components.

project structure:

music_ocr/

main.py

detectors/
ocr_detector.py
vision_llm_detector.py
cv_detector.py

utils/
image_preprocess.py
bbox_merge.py
config.py

output/
results/

---

# Step 1 Image Preprocessing

Use OpenCV to:

- convert to grayscale
- remove noise
- deskew image
- normalize contrast

Functions:

preprocess_image(image)

---

# Step 2 OCR Detection

Use **Aliyun OCR API** to detect:

- numbers
- duration dots after numbers

Return:

list of

{
type
value
bbox
confidence
source="ocr"
}

---

# Step 3 Vision LLM Detection

Use **Aliyun Vision LLM** to detect symbols not handled by OCR.

Detect:

- dot_above
- dot_below
- slur
- tie
- repeat symbols

Prompt example:

"Detect all numbered musical notation symbols in this image.
Return JSON with bounding boxes.

Symbols:
dot_above
dot_below
slur
tie
repeat_start
repeat_end"

Parse the response and convert to structured JSON.

---

# Step 4 OpenCV Detection

Use OpenCV to detect structural lines:

- barline
- double_barline
- sustain dash

Techniques:

- Canny edge detection
- Hough line transform
- morphology operations

Return bounding boxes.

---

# Step 5 Bounding Box Merge

Combine detections from:

- OCR
- Vision LLM
- OpenCV

Rules:

1. If two boxes overlap >70% IoU, keep the higher confidence one.
2. Prefer OCR for numbers.
3. Prefer OpenCV for barlines.

---

# Step 6 Final Output

Write JSON to:

output/results/<image_name>.json

---

# Libraries

Use:

Python 3.11+

opencv-python
numpy
requests
pydantic
Pillow

---

# Additional Requirements

The system must support batch processing:

python main.py input_folder/

The program should process all images and output JSON.

---

# Code Quality

- Use clear class structure
- Add docstrings
- Separate API keys into config file
- Handle API failures

---

# Important

Focus on **visual symbol detection only**.

Do NOT attempt to interpret musical meaning.

Do NOT convert to MIDI.

Only detect symbols and bounding boxes.

---

Now generate the full Python project implementation.

你可以参照：

- https://help.aliyun.com/zh/model-studio/qwen-vl-ocr?spm=5176.12127803.J_8905993520.1.4c495542H4fw6D&scm=20140722.H_2860683._.OR_help-T_cn~zh-V_1#187cc987fb46k
- https://help.aliyun.com/zh/model-studio/qwen-vl-ocr-api-reference?spm=a2c4g.11186623.0.0.47772ab0340V8C
- https://help.aliyun.com/zh/ocr/getting-started/use-process?spm=a2c4g.11186623.help-menu-252763.d_1_0.29835af3jNk0Qu&scm=20140722.H_2862010._.OR_help-T_cn~zh-V_1
- https://help.aliyun.com/zh/ocr/developer-reference/api-ocr-api-2021-07-07-recognizeadvanced?spm=a2c4g.11186623.0.i4
