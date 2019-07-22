import json
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import RandomState
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from tqdm import trange

from src import runner_
from src.datasets.utils import load_coco_val_2017
from src.plotting.utils import print_results, visualize_scores
from src.problemgenerator.array import Array
from src.problemgenerator.filters import GaussianNoise
from src.problemgenerator.series import Series
from src.utils import generate_unique_path


class Preprocessor:
    def run(self, _, imgs):
        return None, imgs, {}


class YOLOv3Model:

    def __init__(self):
        self.random_state = RandomState(42)
        self.coco91class = [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27, 28, 31, 32, 33,
            34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
            62, 63, 64, 65, 67, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88, 89, 90
        ]
        self.results = []

    def __get_results_for_img(self, img, img_id, net):
        conf_threshold = .25
        nms_threshold = .4
        img_h = img.shape[0]
        img_w = img.shape[1]
        inference_size = 416
        scale = 1 / 255

        blob = cv2.dnn.blobFromImage(img, scale, (inference_size, inference_size), (0, 0, 0), True, crop=False)
        net.setInput(blob)

        out_layer_names = net.getUnconnectedOutLayersNames()
        outs = net.forward(out_layer_names)

        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = round(scores[class_id], 3)
                if confidence > conf_threshold:
                    center_x = detection[0] * img_w
                    center_y = detection[1] * img_h
                    w = round(detection[2] * img_w, 2)
                    h = round(detection[3] * img_h, 2)
                    x = round(center_x - w / 2, 2)
                    y = round(center_y - h / 2, 2)
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
        for i in indices:
            i = i[0]
            x, y, w, h = boxes[i]

            self.results.append({
                "image_id": img_id,
                "category_id": self.coco91class[class_ids[i]],
                "bbox": [x, y, w, h],
                "score": confidences[i],
            })

    def run(self, _, imgs, model_params):
        img_ids = model_params["img_ids"]

        net = cv2.dnn.readNet("data/yolov3.weights", "data/yolov3.cfg")
        [self.__get_results_for_img(imgs[i], img_ids[i], net) for i in trange(len(imgs))]
        if not self.results:
            return {"mAP-50": 0}

        path_to_results = generate_unique_path("tmp", "json")
        with open(path_to_results, "w") as fp:
            json.dump(self.results, fp)

        coco_gt = COCO("data/annotations/instances_val2017.json")
        coco_eval = COCOeval(coco_gt, coco_gt.loadRes(path_to_results), "bbox")
        coco_eval.params.imgIds = img_ids
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()
        return {"mAP-50": round(coco_eval.stats[1], 3)}


def visualize(df):
    visualize_scores(df, ["mAP-50"], "std", "YOLOv3 object detection scores with added error", log=False)
    # visualize_scores(df, ["mAP-50"], "snowflake_probability",
    #                  "YOLOv3 object detection scores with added error", log=True)
    # visualize_scores(df, ["mAP-50"], "probability", "YOLOv3 object detection scores with added error", log=True)
    # visualize_scores(df, ["mAP-50"], "quality", "YOLOv3 object detection scores with added error", log=False)
    plt.show()


def main(argv):
    if len(argv) != 2:
        exit(0)

    imgs, img_ids, class_names = load_coco_val_2017(int(argv[1]))

    err_params_list = [{"mean": 0, "std": std} for std in [10 * i for i in range(0, 4)]]
    # err_params_list = [{"std": std} for std in [i for i in range(0, 4)]]
    # err_params_list = [{"snowflake_probability": p, "snowflake_alpha": .4, "snowstorm_alpha": 1}
    #                    for p in [10 ** i for i in range(-4, 0)]]
    # err_params_list = [{"probability": p} for p in [10 ** i for i in range(-4, 0)]]
    # err_params_list = [
    #     {"probability": p, "radius_generator": GaussianRadiusGenerator(0, 50), "transparency_percentage": 0.2}
    #     for p in [10 ** i for i in range(-6, -2)]]
    # err_params_list = [{"quality": q} for q in [25, 50, 75, 100]]

    model_params_dict_list = [{"model": YOLOv3Model, "params_list": [{"img_ids": img_ids, "class_names": class_names}]}]

    err_node = Array()
    err_root_node = Series(err_node)

    err_node.addfilter(GaussianNoise("mean", "std"))
    # err_node.addfilter(Blur_Gaussian("std"))
    # err_node.addfilter(Snow("snowflake_probability", "snowflake_alpha", "snowstorm_alpha"))
    # err_node.addfilter(Rain("probability"))
    # err_node.addfilter(StainArea("probability", "radius_generator", "transparency_percentage"))
    # err_node.addfilter(JPEG_Compression("quality"))

    df = runner_.run(None, imgs, Preprocessor, err_root_node, err_params_list, model_params_dict_list)

    print_results(df, ["img_ids", "class_names", "mean", "std", "radius_generator", "transparency_percentage"])
    visualize(df)


if __name__ == "__main__":
    main(sys.argv)
