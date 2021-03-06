# MIT License
#
# Copyright (c) 2019 Tuomas Halvari, Juha Harviainen, Juha Mylläri, Antti Röyskö, Juuso Silvennoinen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from numpy.random import RandomState
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from tqdm import trange

from dpemu import runner
from dpemu.dataset_utils import load_coco_val_2017
from dpemu.filters.image import Brightness
from dpemu.ml_utils import load_yolov3
from dpemu.nodes import Array
from dpemu.nodes.series import Series
from dpemu.plotting_utils import print_results_by_model, visualize_scores
from dpemu.utils import generate_unique_path
from dpemu.utils import get_project_root

cv2.ocl.setUseOpenCL(False)
torch.multiprocessing.set_start_method("spawn", force="True")


def get_data(argv):
    return load_coco_val_2017(int(argv[1]), is_shuffled=True)


def get_err_root_node():
    err_node = Array()
    err_root_node = Series(err_node)
    # err_node.addfilter(GaussianNoise("mean", "std"))
    # err_node.addfilter(Blur_Gaussian("std"))
    # err_node.addfilter(Snow("snowflake_probability", "snowflake_alpha", "snowstorm_alpha"))
    # err_node.addfilter(FastRain("probability", "range"))
    # err_node.addfilter(StainArea("probability", "radius_generator", "transparency_percentage"))
    # err_node.addfilter(JPEG_Compression("quality"))
    # err_node.addfilter(Resolution("k"))
    err_node.addfilter(Brightness("tar", "rat", "range"))
    # err_node.addfilter(SaturationVectorized("tar", "rate", "range"))
    # err_node.addfilter(Identity())
    return err_root_node


def get_err_params_list():
    # err_params_list = [{"mean": 0, "std": std} for std in [10 * i for i in range(0, 4)]]
    # err_params_list = [{"std": std} for std in [i for i in range(0, 4)]]
    # err_params_list = [{"snowflake_probability": p, "snowflake_alpha": .4, "snowstorm_alpha": 0}
    #                    for p in [10 ** i for i in range(-4, 0)]]
    # err_params_list = [{"probability": p, "range": 255} for p in [10 ** i for i in range(-4, 0)]]
    # err_params_list = [
    #     {"probability": p, "radius_generator": GaussianRadiusGenerator(0, 50), "transparency_percentage": 0.2}
    #     for p in [10 ** i for i in range(-6, -2)]]
    # err_params_list = [{"quality": q} for q in [10, 20, 30, 100]]
    # err_params_list = [{"k": k} for k in [1, 2, 3, 4]]
    err_params_list = [{"tar": 1, "rat": rat, "range": 255} for rat in [0, .4, .8, 1.2]]
    # err_params_list = [{}]
    return err_params_list


class Preprocessor:
    def run(self, _, imgs, params):
        return None, imgs, {}


class YOLOv3CPUModel:

    def __init__(self):
        self.random_state = RandomState(42)
        self.coco91class = [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27, 28, 31, 32, 33,
            34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
            62, 63, 64, 65, 67, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88, 89, 90
        ]
        self.show_imgs = False

    @staticmethod
    def __draw_box(img, class_id, class_names, confidence, x, y, w, h):
        label = str(class_names[class_id]) + " " + str(confidence)
        colors = np.random.randint(0, 255, size=(len(class_names), 3), dtype="uint8")
        color = [int(c) for c in colors[class_id]]
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def __get_results_for_img(self, img, img_id, class_names, net):
        conf_threshold = 0
        nms_threshold = .4
        img_h = img.shape[0]
        img_w = img.shape[1]
        inference_size = 608
        scale = 1 / 255

        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        blob = cv2.dnn.blobFromImage(img, scale, (inference_size, inference_size), (0, 0, 0), True)
        net.setInput(blob)
        out_layer_names = net.getUnconnectedOutLayersNames()
        outs = net.forward(out_layer_names)

        class_ids = []
        confs = []
        boxes = []
        results = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                conf = float(scores[class_id])
                if conf > conf_threshold:
                    center_x = detection[0] * img_w
                    center_y = detection[1] * img_h
                    w = detection[2] * img_w
                    h = detection[3] * img_h
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confs.append(conf)
                    boxes.append([x, y, w, h])

        indices = cv2.dnn.NMSBoxes(boxes, confs, conf_threshold, nms_threshold)
        for i in indices:
            i = i[0]
            x, y, w, h = boxes[i]

            results.append({
                "image_id": img_id,
                "category_id": self.coco91class[class_ids[i]],
                "bbox": [x, y, w, h],
                "score": confs[i],
            })

            if self.show_imgs:
                self.__draw_box(img, class_ids[i], class_names, round(confs[i], 2), int(round(x)), int(round(y)),
                                int(round(w)), int(round(h)))

        if self.show_imgs:
            cv2.imshow(str(img_id), img)
            path_to_img = generate_unique_path("out", "jpg")
            cv2.imwrite(path_to_img, img, [cv2.IMWRITE_JPEG_QUALITY, 100])
            cv2.waitKey()
            cv2.destroyAllWindows()

        return results

    def run(self, _, imgs, params):
        img_ids = params["img_ids"]
        class_names = params["class_names"]
        self.show_imgs = params["show_imgs"]
        path_to_yolov3_weights = params["path_to_yolov3_weights"]
        path_to_yolov3_cfg = params["path_to_yolov3_cfg"]

        net = cv2.dnn.readNet(path_to_yolov3_weights, path_to_yolov3_cfg)
        results = []
        for i in trange(len(imgs)):
            results.extend(self.__get_results_for_img(imgs[i], img_ids[i], class_names, net))
        if not results:
            return {"mAP-50": 0}

        path_to_results = generate_unique_path("tmp", "json")
        with open(path_to_results, "w") as fp:
            json.dump(results, fp)

        coco_gt = COCO(f"{get_project_root()}/data/annotations/instances_val2017.json")
        coco_eval = COCOeval(coco_gt, coco_gt.loadRes(path_to_results), "bbox")
        coco_eval.params.imgIds = img_ids
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()
        return {"mAP-50": round(coco_eval.stats[1], 3)}


def get_model_params_dict_list(img_ids, class_names, path_to_yolov3_weights, path_to_yolov3_cfg):
    return [
        {"model": YOLOv3CPUModel, "params_list": [{
            "img_ids": img_ids,
            "class_names": class_names,
            "show_imgs": True,
            "path_to_yolov3_weights": path_to_yolov3_weights,
            "path_to_yolov3_cfg": path_to_yolov3_cfg
        }]}
    ]


def visualize(df):
    # visualize_scores(df, ["mAP-50"], [True], "std", "Object detection with Gaussian noise", x_log=False)
    # visualize_scores(df, ["mAP-50"], [True], "std", "Object detection with Gaussian blur", x_log=False)
    # visualize_scores(df, ["mAP-50"], [True], "snowflake_probability", "Object detection with snow filter", x_log=True)
    # visualize_scores(df, ["mAP-50"], [True], "probability", "Object detection with rain filter", x_log=True)
    # visualize_scores(df, ["mAP-50"], [True], "probability", "Object detection with added stains", x_log=True)
    # visualize_scores(df, ["mAP-50"], [True], "quality", "Object detection with JPEG compression", x_log=False)
    # visualize_scores(df, ["mAP-50"], [True], "k", "Object detection with reduced resolution", x_log=False)
    visualize_scores(df, ["mAP-50"], [True], "rat", "Object detection with added brightness", x_log=False)
    # visualize_scores(df, ["mAP-50"], [True], "rate", "Object detection with added saturation", x_log=False)
    plt.show()


def main(argv):
    if len(argv) != 2:
        exit(0)

    imgs, img_ids, class_names, _ = get_data(argv)
    path_to_yolov3_weights, path_to_yolov3_cfg = load_yolov3()

    df = runner.run(
        train_data=None,
        test_data=imgs,
        preproc=Preprocessor,
        preproc_params=None,
        err_root_node=get_err_root_node(),
        err_params_list=get_err_params_list(),
        model_params_dict_list=get_model_params_dict_list(img_ids, class_names, path_to_yolov3_weights,
                                                          path_to_yolov3_cfg),
        n_processes=1
    )

    print_results_by_model(df, ["img_ids", "class_names", "show_imgs", "mean", "radius_generator",
                                "transparency_percentage", "range", "snowflake_alpha", "snowstorm_alpha"])
    visualize(df)


if __name__ == "__main__":
    main(sys.argv)
