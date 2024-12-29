# coding=utf-8
import os
import json
import cv2
import numpy as np
from os import path
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import *
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.drawer import drawer
from src import Parameter as pa
from src import config as co, Timer


class SetupGUI(QtWidgets.QDialog):
    """ This class handles all events and make modifications on all widgets except the image area 
        (still handles zooming feature)
    """
    tableWidget_DrawList_signal = QtCore.pyqtSignal(dict, str)
    Window_resized_signal = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(SetupGUI, self).__init__()
        self.parent = parent 
        self.init_Config()
        self.path_file_label = None

    def init_Config(self):
        self.ui = uic.loadUi(co.SETUP_GUI, self)
        self.pushButton_SelectImage.clicked.connect(self.browser_file)
        self.pushButton_ConfirmDraw.clicked.connect(self.confirm_draw)
        self.pushButton_SaveModel.clicked.connect(self.save_config)
        self.pushButton_CheckDraw.clicked.connect(self.check_draw)
        self.tableWidget_DrawList_signal.connect(self.tableWidget_DrawList_slot)

        self.tableWidget_DrawList.itemClicked.connect(self.handle_item_clicked)
        self.pushButton_ZoomIn.clicked.connect(self.zoomIn)
        self.pushButton_ZoomOut.clicked.connect(self.zoomOut)
        self.pushButton_FitView.clicked.connect(self.fitView)
        self.pushButton_exit.clicked.connect(self.close_config_window)
        self.Window_resized_signal.connect(self.window_resize)

    def close_config_window(self):
        pa.DRAW_COORDINATE = None
        self.close()
        
    def tableWidget_DrawList_slot(self, data, typ):
        r = self.tableWidget_DrawList.rowCount() if typ == "append" else 0
        c = self.tableWidget_DrawList.columnCount()
        self.tableWidget_DrawList.setHorizontalHeaderLabels(['STT', 'Đối tượng', 'Tọa độ'])
        self.tableWidget_DrawList.setRowCount(r + len(data))
       
        for n, key in enumerate(data.keys()):  # Row
            button = QtWidgets.QPushButton("Xóa")   
            button.clicked.connect(self.remove_draw)
            self.tableWidget_DrawList.setCellWidget(r + n, 0, button)

            for m, item in enumerate(data[key]):
                self.tableWidget_DrawList.setItem(r + n, m + 1, QtWidgets.QTableWidgetItem(str(item)))
                
    def handle_item_clicked(self, event):
        items = self.scene.items()
        for item in items:
            if (type(item).__name__  == "QGraphicsRectItem"):
                self.scene.removeItem(item)
            
            if (type(item).__name__  == "QGraphicsTextItem"):
                self.scene.removeItem(item)

        selected_index = self.tableWidget_DrawList.selectedIndexes()
        selected_index = [i.row() for i in selected_index]
        
        param_items = []
        value_items = []
        for idx, val in enumerate(pa.MODEL_CONFIG["drawList"]):
            if (idx not in selected_index):
                continue
            
            configs = val['config']
            for i in range(len(configs)):
                param_items.append(list(configs.keys())[i])
                value_items.append(list(configs.values())[i])
        
        selected_items = self.tableWidget_DrawList.selectedItems() 
        pos = selected_items[1].text()
        pos = eval(pos)
        x, y, width, height = pos['x'], pos['y'], pos['width'], pos['height']
        rect_item = QGraphicsRectItem(QRectF(x, y, width, height))
        rect_item.setPen(QPen(Qt.red, 4, Qt.SolidLine))
        self.scene.addItem(rect_item) 

        # Add screw/conn position text
        text = QGraphicsTextItem(str(selected_index[0]+1))
        text.setFont(QFont("Segoe UI", 40))
        text.setPos(x-50, y-50)
        text.setDefaultTextColor(QColor("Red"))
        self.scene.addItem(text) 

    def resizeEvent(self, event):
        self.Window_resized_signal.emit()
        return super(SetupGUI, self).resizeEvent(event)

    def start(self):
        try:
            self.load_model()
            self.show()
            self.exec_()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))

    def finish(self):
        pa.DRAW_COORDINATE = None
        self.close()

    def save_config(self):
        pa.MODEL_CONFIG['createdTime'] = str(datetime.now())
        with open(self.path_file_label, "w", encoding="utf-8") as f:
            json.dump(pa.MODEL_CONFIG, f, ensure_ascii=False, indent=4)
            QtWidgets.QMessageBox.information(self, "Thông báo", "Lưu thành công !")
    
        
    def load_model(self):
        self.show_image_by_filename("GUI/images/backgroud-placeholder.png")
            

    def config_model(self):
        self.groupBox_Config.setEnabled(True)
        if pa.MODEL_CONFIG is None or pa.MODEL_CONFIG["imagePath"].strip() == "":
            self.enable_not_select_template(False)

    def img_cv_2_qt(self, img_cv):
        height, width, channel = img_cv.shape
        bytes_per_line = channel * width
        img_qt = QtGui.QImage(img_cv, width, height, bytes_per_line, QtGui.QImage.Format_RGB888).rgbSwapped()
        return QtGui.QPixmap.fromImage(img_qt)

    def createModel(self,path_file_label):
        if not os.path.exists(path_file_label):
            data = {}
            data['imagePath'] = ''
            data['drawList'] = []
            data['createdTime'] = str(datetime.now())
            with open(path_file_label, 'w') as outfile:
                json.dump(data, outfile, indent=4)

    def read_file_config(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            pa.MODEL_CONFIG = data

    def browser_file(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            path_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Lựa chọn ảnh template.", "", "Images/Video (*.png *.jpg *.bmp *.mp4 *.avi *.mov)", options=options)
            if path_file:
                file_extension = os.path.splitext(path_file)[1]
                self.path_file_label = os.path.splitext(path_file)[0] +'.json'
                if file_extension in ['.png',  '.jpg',  '.bmp']:
                    image = cv2.imread(path_file)
                else:
                    camera = cv2.VideoCapture(path_file)
                    ret, frame = camera.read()
                    if ret:
                        ret, image = camera.read()
                    else:
                        QtWidgets.QMessageBox.critical(self, "Lỗi", "Video không đúng định dạng")
                self.lineEdit_ImagePath.setText(path_file)
                self.createModel(self.path_file_label)
                self.read_file_config(self.path_file_label)
                data = {}
                for idx, val in enumerate(pa.MODEL_CONFIG["drawList"]):
                    data[f"col_{idx}"] = [val["type"], val["xy"]]
                self.tableWidget_DrawList.clear() 
                self.tableWidget_DrawList_signal.emit(data, "clear")
                self.img = self.img_cv_2_qt(image)
                pa.IMAGE_PIXMAP = self.img
                self.label_Image.update()
                self.view = self.label_Image
                self.scene = QGraphicsScene()
                self.scene.addPixmap(self.img)
                self.view.setScene(self.scene)
                self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
                self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
                self.newImage()
                self.label_Image.update()
                self.enable_not_select_template(True)
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
    

    def confirm_draw(self):
        if pa.DRAW_COORDINATE:
            temp = {}
            if int(pa.DRAW_COORDINATE["width"]) < 0:
                temp["x"] = int(pa.DRAW_COORDINATE["x"]) + int(pa.DRAW_COORDINATE["width"])
                temp["width"] = - int(pa.DRAW_COORDINATE["width"])
            else:
                temp["x"] = int(pa.DRAW_COORDINATE["x"])
                temp["width"] = int(pa.DRAW_COORDINATE["width"])

            if  int(pa.DRAW_COORDINATE["height"]) < 0:
                temp["y"] = int(pa.DRAW_COORDINATE["y"]) +  int(pa.DRAW_COORDINATE["height"])
                temp["height"] = - int(pa.DRAW_COORDINATE["height"])
            else:
                temp["y"] = int(pa.DRAW_COORDINATE["y"])
                temp["height"] = int(pa.DRAW_COORDINATE["height"])

            item = {"type":"box", "xy": temp}
            
            data = {f"col_x": ["box" , temp]}
            pa.MODEL_CONFIG["drawList"].append(item)
            self.tableWidget_DrawList_signal.emit(data, "append")


    def window_resize(self):
        if pa.IMAGE_PIXMAP:
            pass
        
    def remove_draw(self):
        button = self.sender()
        if button:  
            row = self.tableWidget_DrawList.currentRow()
            if (row<0):
                return 
            draw_type = self.tableWidget_DrawList.item(row, 1).text()
            xy = json.loads(str(self.tableWidget_DrawList.item(row, 2).text()).replace("\'", "\""))
            del pa.MODEL_CONFIG["drawList"][row]  
            self.tableWidget_DrawList.removeRow(row)
            #
                
    def check_draw(self):
        if pa.IMAGE_PIXMAP:
            items = self.scene.items()
            for item in items:
                if (type(item).__name__  == "QGraphicsRectItem"):
                    self.scene.removeItem(item)
                
                if (type(item).__name__  == "QGraphicsTextItem"):
                    self.scene.removeItem(item)
                    
            n_row = self.tableWidget_DrawList.rowCount()
            COL_IDX = 2
            for row_idx in range(n_row):
                item = self.tableWidget_DrawList.item(row_idx, COL_IDX)
                pos = item.text()
                pos = eval(pos)
                x, y, width, height = pos['x'], pos['y'], pos['width'], pos['height']
                        
                rect_item = QGraphicsRectItem(QRectF(x, y, width, height))
                rect_item.setPen(QPen(Qt.red, 4, Qt.SolidLine)) 
                self.scene.addItem(rect_item) 
            
                text = QGraphicsTextItem(str(row_idx+1))
                text.setFont(QFont("Segoe UI", 40))
                text.setPos(x-50, y-50)
                text.setDefaultTextColor(QColor("Red"))
                self.scene.addItem(text) 
        else:
            QtWidgets.QMessageBox.critical(self, "Thông báo", "Lỗi ảnh !")

    def newImage(self):
        self.getScreenRes()
        self.imgw = self.img.width()
        self.imgh = self.img.height()
        if self.imgw > self.screenw or self.imgh > self.screenh:
            self.resize(self.screenw, self.screenh)
            self.show()
            self.resetScroll()
            self.fitView()
        else:
            self.resize(self.imgw + 2, self.imgh + 2)
            self.show()
            self.resetScroll()
            self.fitView()
                   
    def zoomIn(self):
        self.zoom *= 1.1
        self.updateView()

    def zoomOut(self):
        self.zoom /= 1.1
        self.updateView()
               
    def fitView(self):
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatioByExpanding)  
        self.zoom = self.view.transform().m11()
             
    def updateView(self):
        self.view.setTransform(QTransform().scale(self.zoom, self.zoom))
                     
    def resetScroll(self):
        self.view.verticalScrollBar().setValue(0)
        self.view.horizontalScrollBar().setValue(0)
            
    def getScreenRes(self):
        app = QtWidgets.QApplication.instance()
        self.screen_res = app.desktop().availableGeometry() 
        self.screenw = self.screen_res.width()
        self.screenh = self.screen_res.height()
        self.activateWindow

    
    def enableZoomButton(self, enable=True):
        self.pushButton_ZoomIn.setEnabled(enable)
        self.pushButton_ZoomOut.setEnabled(enable)
        self.pushButton_FitView.setEnabled(enable)
        
    def enable_not_select_template(self, enable=False):
        self.pushButton_ConfirmDraw.setEnabled(enable)
        self.tableWidget_DrawList.setEnabled(enable)
        self.pushButton_CheckDraw.setEnabled(enable)
        self.pushButton_SaveModel.setEnabled(enable)
        
    def show_image_by_filename(self, im_path):
        if not os.path.isfile(im_path):
            return
        self.img = QPixmap(im_path)
        self.view = self.label_Image
        self.scene = QGraphicsScene()
        self.scene.addPixmap(self.img)
        self.view.setScene(self.scene)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.fitView()