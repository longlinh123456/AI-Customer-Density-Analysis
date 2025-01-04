# coding=utf-8
import os
import json, time
import threading
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel, QSizePolicy
from qt_thread_updater import get_updater
import torch
import csv
from models import vgg19
from torchvision import transforms
from src import config as co
import ipdb


class Main:
    def __init__(self, MainGUI):
        self.MainGUI = MainGUI
        self.camera = None
        self.ret = False
        self.start_camera = True
        self.Label_Counting = []
        self.device = torch.device("cpu")
        model_path = "weights/model_couting.pth"
        self.model = vgg19()
        self.model.to(self.device)
        self.model.load_state_dict(
            torch.load(model_path, self.device, weights_only=True)
        )
        self.model.eval()
        self.fps = 20
        self.density_map = None
        self.person_count = 0
        self.data_csv = [["STT", "Num Frams", "Count"]]
        print("Load model done")

    def predict(self, image, model):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        inp = transforms.ToTensor()(pil_image).unsqueeze(0)
        inp = inp.to(self.device)
        with torch.set_grad_enabled(False):
            outputs, _ = model(inp)
        count = torch.sum(outputs).item()
        vis_img = outputs[0, 0].cpu().numpy()
        vis_img = (vis_img - vis_img.min()) / (vis_img.max() - vis_img.min() + 1e-5)
        vis_img = (vis_img * 255).astype(np.uint8)
        vis_img = cv2.applyColorMap(vis_img, cv2.COLORMAP_JET)
        vis_img = cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB)
        return vis_img, int(count)

    def img_cv_2_qt(self, img_cv):
        height, width, channel = img_cv.shape
        bytes_per_line = channel * width
        img_qt = QtGui.QImage(
            img_cv, width, height, bytes_per_line, QtGui.QImage.Format_RGB888
        ).rgbSwapped()
        return QtGui.QPixmap.fromImage(img_qt)

    def init_devices(self, url_camera):
        self.camera = cv2.VideoCapture(url_camera)
        self.ret, frame = self.camera.read()
        if not self.ret:
            self.start_camera = False
            self.MainGUI.MessageBox_signal.emit(
                "Có lỗi xảy ra ! \n Không tìm thấy camera/video", "error"
            )
        else:
            self.fps = self.camera.get(cv2.CAP_PROP_FPS)
            self.start_camera = True

    def load_config(self, path_file):
        file_extension = os.path.splitext(path_file)[0]
        path_config = os.path.splitext(file_extension)[0] + ".json"
        if os.path.exists(path_config):
            with open(path_config, encoding="utf-8") as f:
                data = json.load(f)
                drawList_box = data["drawList"]
                for data in drawList_box:
                    bbox = [
                        data["xy"]["x"],
                        data["xy"]["y"],
                        data["xy"]["x"] + data["xy"]["width"],
                        data["xy"]["y"] + data["xy"]["height"],
                    ]
                    self.Label_Counting.append(bbox)

    def write_csv(self, path_file):
        file_extension = os.path.splitext(path_file)[0]
        path_csv = os.path.splitext(file_extension)[0] + ".csv"
        with open(path_csv, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self.data_csv)
        x_value = [sublist[1] for sublist in self.data_csv]
        y_value = [sublist[2] for sublist in self.data_csv]
        del x_value[0]
        del y_value[0]
        plt.plot(x_value, y_value, "bD--")
        path_img = os.path.splitext(file_extension)[0] + ".jpg"
        plt.savefig(path_img, format="jpg")
        self.data_csv = [["STT", "Num Frams", "Count"]]

    def auto_camera(self):
        url_camera = co.CAMERA_DEVICE
        self.init_devices(url_camera)
        self.data_csv = [["STT", "Num Frams", "Count"]]
        cnt = 0
        while self.ret and self.start_camera:
            try:
                ret, frame = self.camera.read()

                self.ret = ret
                if self.ret and self.start_camera:
                    if cnt == 0 or cnt % (2 * self.fps) == 0:
                        self.density_map, self.person_count = self.predict(
                            frame, self.model
                        )
                        data_count = [len(self.data_csv), cnt, self.person_count]
                        self.data_csv.append(data_count)
                    else:
                        time.sleep(float(1 / self.fps))
                    cnt += 1
                    get_updater().call_latest(
                        self.MainGUI.label_Image.setPixmap, self.img_cv_2_qt(frame)
                    )
                    get_updater().call_latest(
                        self.MainGUI.text_resutl.setText,
                        "Count: " + str(self.person_count),
                    )
                    get_updater().call_latest(
                        self.MainGUI.text_resutl.setStyleSheet,
                        "background-color: rgb(0, 255, 0);",
                    )
                    get_updater().call_latest(
                        self.MainGUI.label_View.setPixmap,
                        self.img_cv_2_qt(self.density_map),
                    )

                else:
                    break
            except Exception as e:
                print("Bug: ", e)
        self.write_csv("camera.csv")
        self.close_camera()

    def auto_video(self, path_video):
        url_camera = path_video
        self.load_config(url_camera)
        self.init_devices(url_camera)
        self.data_csv = [["STT", "Num Frams", "Count"]]
        cnt = 0
        while self.ret and self.start_camera:
            try:
                ret, frame = self.camera.read()
                self.ret = ret
                if self.ret and self.start_camera:
                    if len(self.Label_Counting) == 0:
                        # if cnt == 0 or cnt % (2 * self.fps) == 0:
                        if cnt == 0 or cnt % (int(2 * self.fps)) == 0:
                            self.density_map, self.person_count = self.predict(
                                frame, self.model
                            )
                            data_count = [len(self.data_csv), cnt, self.person_count]
                            self.data_csv.append(data_count)
                            print(self.data_csv, cnt)
                        else:
                            time.sleep(float(1 / self.fps))
                        cnt += 1
                    else:
                        # if cnt == 0 or cnt % (2 * self.fps) == 0:
                        if cnt == 0 or cnt % (int(2 * self.fps)) == 0:
                            self.person_count = 0
                            for box in self.Label_Counting:
                                image = frame[box[1] : box[3], box[0] : box[2]]
                                _, person_count = self.predict(image, self.model)
                                self.person_count += person_count
                            self.density_map, _ = self.predict(frame, self.model)
                            data_count = [len(self.data_csv), cnt, self.person_count]
                            self.data_csv.append(data_count)
                        else:
                            time.sleep(float(1 / self.fps))
                        cnt += 1
                        for box in self.Label_Counting:
                            cv2.rectangle(
                                frame,
                                (box[0], box[1]),
                                (box[2], box[3]),
                                (255, 0, 0),
                                2,
                            )
                    get_updater().call_latest(
                        self.MainGUI.label_Image.setPixmap, self.img_cv_2_qt(frame)
                    )
                    get_updater().call_latest(
                        self.MainGUI.text_resutl.setText,
                        "Count: " + str(self.person_count),
                    )
                    get_updater().call_latest(
                        self.MainGUI.text_resutl.setStyleSheet,
                        "background-color: rgb(0, 255, 0);",
                    )
                    get_updater().call_latest(
                        self.MainGUI.label_View.setPixmap,
                        self.img_cv_2_qt(self.density_map),
                    )
                else:
                    break
            except Exception as e:
                print("Bug: ", e)
        self.write_csv(url_camera)
        self.close_camera()

    def manual_image(self, path_image):
        self.load_config(path_image)
        image = cv2.imread(path_image)
        if len(self.Label_Counting) == 0:
            density_map, count = self.predict(image, self.model)
        else:
            count = 0
            for box in self.Label_Counting:
                image_crop = image[box[1] : box[3], box[0] : box[2]]
                _, person_count = self.predict(image_crop, self.model)
                count += person_count
            density_map, _ = self.predict(image, self.model)
            for box in self.Label_Counting:
                cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)

        get_updater().call_latest(
            self.MainGUI.label_Image.setPixmap, self.img_cv_2_qt(image)
        )
        get_updater().call_latest(
            self.MainGUI.text_resutl.setText, "Count: " + str(count)
        )
        get_updater().call_latest(
            self.MainGUI.text_resutl.setStyleSheet, "background-color: rgb(0, 255, 0);"
        )
        get_updater().call_latest(
            self.MainGUI.label_View.setPixmap, self.img_cv_2_qt(density_map)
        )

    def close_camera(self):
        try:

            if self.ret:
                self.camera.release()
            self.start_camera = False
            self.data_csv = [["STT", "Num Frams", "Count"]]
            self.camera = None
            self.ret = False
            self.Label_Counting = []
            time.sleep(1)
            self.MainGUI.label_Image.clear()
            self.MainGUI.label_View.clear()
            get_updater().call_latest(self.MainGUI.text_resutl.setText, "Stop")
            get_updater().call_latest(
                self.MainGUI.text_resutl.setStyleSheet,
                "background-color: rgb(255, 244, 0);",
            )

        except Exception as e:
            print("Bug: ", e)
