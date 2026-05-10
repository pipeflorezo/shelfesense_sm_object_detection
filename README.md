# ShelfSense — Visual shelf intelligence

ShelfSense is a small web app that analyzes photos of retail shelves. Upload an image and the service returns the same picture with detected products outlined in green and missing-product gaps highlighted in red. A YOLOv5 model does the detection; a lightweight Flask UI lets you try it without writing any code.

## Architecture

Three services, each in its own container:

- **api** — Flask + Gunicorn front-end and JSON endpoint
- **model** — YOLOv5 inference worker
- **redis** — job queue between the API and the model

![Project Architecture](/utils/imgs/Project_arch.png)

## Run the app

```bash
docker compose up --build -d
```

Then open <http://localhost/>. Drop a shelf photo into the dropzone and click **Analyze shelf**. There is no login or token — the UI is open.

The first model start downloads YOLOv5 weights into `model/import/best.pt` if they aren't already there. To use your own trained weights, drop a `best.pt` file at that path before starting and it will be picked up via the volume mount.

To stop everything:

```bash
docker compose down
```

## JSON endpoint

For programmatic use, POST a multipart image to `/detect`:

```bash
curl -X POST -F "file=@shelf.jpg" http://localhost/detect
```

Response:

```json
{
  "success": true,
  "detections": {
    "Data": {
      "bouding_boxes": [[x1, y1, x2, y2, confidence, class], ...]
    }
  }
}
```

`class 0` = product, `class 1` = missing product (when using two-class weights).

## Run the API tests

From `/api`:

```bash
docker build -t flask_api_test --progress=plain --target test .
```

This builds the API image and runs the test suite inside the container.

## Stress tests

From `/stress_test`:

```bash
python run_stress_tests.py
```

Builds the three images and fires GET / POST traffic at the stack.

## Model training

Build the YOLOv5 image from `/model/yolov5`:

```bash
docker build -t yolo_v5_image -f utils/docker/Dockerfile .
```

Run the training container:

```bash
docker run --rm --net host -it --gpus all \
  -v $(pwd):/home/app/src --workdir /home/app/src \
  yolo_v5_image bash
```

Train YOLOv5-nano on SKU-110K (downloaded automatically if missing):

```bash
python train.py --data SKU-110K.yaml --cfg yolov5n.yaml \
  --weights yolov5n.pt --batch-size 16 --epochs 30 --device 0
```

SKU-110K only labels `product`. To teach the model to spot **missing-product** gaps, label a custom dataset, switch to a two-class YAML, and retrain. Helper scripts for sub-sampling the dataset and merging label classes live in `/utils`.

## Notebooks

Under `/notebooks`:

1. **EDA** — exploratory analysis of SKU-110K
2. **Evaluate** — single-class (product) model evaluation
3. **Evaluate_2_classes** — two-class (product + missing-product) evaluation
4. **Labels_Checker** — sanity check on the new class labels

## Stack

YOLOv5 · PyTorch · Flask · Gunicorn · Redis · Docker Compose
