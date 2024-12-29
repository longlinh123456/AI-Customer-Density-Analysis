import sys
import math
import json
import traceback
import cv2
import numpy as np
import time

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtCore, uic
from src import Parameter as pa

FREE_STATE = 1
BUILDING_SQUARE = 2
BEGIN_SIDE_EDIT = 3
END_SIDE_EDIT = 4
TOP_SIDE_EDIT = 5
DOWN_SIDE_EDIT = 6

CURSOR_ON_BEGIN_SIDE = 1
CURSOR_ON_END_SIDE = 2
CURSOR_ON_TOP_SIDE = 3
CURSOR_ON_DOWN_SIDE = 4

def generate_mask(src_mask="GUI/icons/mask.png", size_w=200, size_h=120):
    mask = cv2.imread(src_mask, cv2.IMREAD_GRAYSCALE)
    mask = cv2.threshold(cv2.resize(mask, (size_w, size_h)), 128, 255, cv2.THRESH_BINARY)[1]
    mask = cv2.bitwise_not(mask)
    qimage = QImage(mask, size_w, size_h, QImage.Format_Grayscale8)
    return qimage

class drawer(QGraphicsView):
# class drawer():
    """ This class is to handle all events and make drawing on the image area.
    """
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.begin = QPoint()
        self.end = QPoint()
        self.state = FREE_STATE
        self.setMouseTracking(True)
        self.free_cursor_on_side = 0
        self.brush = QBrush(QColor(255, 255, 0, 50))
        self.pen_1 = QPen(Qt.red, 2) 
        self.pen_2 = QPen(Qt.yellow, 4, Qt.DashLine)
        self.pen_3 = QPen(Qt.green, 2, Qt.DashLine)
        self.SetupGUI = parent 
        self.qpainter = None
        self.mask = generate_mask()
        
    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction('Zoom in     +, e', self.SetupGUI.zoomIn)
        menu.addAction('Zoom out    -, d', self.SetupGUI.zoomOut)
        menu.addAction('Fit view    F', self.SetupGUI.fitView)
        menu.exec_(event.globalPos())
        
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:     
        super().paintEvent(event)
        if pa.SUB_IMAGE is not None:
            im_gray, x, y, mask, size_w, size_h = pa.SUB_IMAGE
            im_gray = QPixmap.fromImage(im_gray)
            im_gray.setMask(mask)
            qpainter = QPainter(self.viewport())
            qpainter.drawPixmap(x, y, im_gray)
            qpainter.setPen(Qt.red)
            qpainter.drawRoundedRect(x, y, size_w, size_h, 12, 12)
        return 

    def mousePressEvent(self, event):
        if not pa.IMAGE_PIXMAP:
            return
        side = self.cursor_on_side(event.pos())
        if side == CURSOR_ON_BEGIN_SIDE:
            self.state = BEGIN_SIDE_EDIT
        elif side == CURSOR_ON_END_SIDE:
            self.state = END_SIDE_EDIT
        elif side == CURSOR_ON_TOP_SIDE:
            self.state = TOP_SIDE_EDIT
        elif side == CURSOR_ON_DOWN_SIDE:
            self.state = DOWN_SIDE_EDIT
        else:
            self.state = BUILDING_SQUARE
            self.begin = event.pos()
            self.end = event.pos()
        
        return super().mousePressEvent(event)
      
    def update_drawed_rect(self):
        rect_xy1 = self.SetupGUI.view.mapToScene(self.begin)
        rect_x1, rect_y1 = rect_xy1.x(), rect_xy1.y()
        rect_xy3 = self.SetupGUI.view.mapToScene(self.end)
        rect_x3, rect_y3 = rect_xy3.x(), rect_xy3.y()
        rect_x1, rect_y1, rect_x3, rect_y3 = int(rect_x1), int(rect_y1), int(rect_x3), int(rect_y3)
        rect_w = rect_x3 - rect_x1
        rect_h = rect_y3 - rect_y1
        rect_item = QGraphicsRectItem(QRectF(rect_x1, rect_y1, rect_w, rect_h))
        rect_item.setPen(QPen(Qt.red, 4, Qt.DashLine))        
        items = self.SetupGUI.scene.items()
        for item in items:
            if (type(item).__name__  == "QGraphicsRectItem"):
                self.SetupGUI.scene.removeItem(item)
            if (type(item).__name__  == "QGraphicsTextItem"):
                self.SetupGUI.scene.removeItem(item)

        self.SetupGUI.scene.addItem(rect_item)   
        
    def mouseMoveEvent(self, event):
        if not pa.IMAGE_PIXMAP:
            return
        if self.state == FREE_STATE:
            self.free_cursor_on_side = self.cursor_on_side(event.pos())
            if self.free_cursor_on_side in (CURSOR_ON_BEGIN_SIDE, CURSOR_ON_END_SIDE):
                self.setCursor(Qt.SizeHorCursor)
            elif self.free_cursor_on_side in (CURSOR_ON_TOP_SIDE, CURSOR_ON_DOWN_SIDE):
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.unsetCursor()
            self.update()
        else:
            self.applye_event(event)
            self.update_drawed_rect()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if pa.IMAGE_PIXMAP:
            self.applye_event(event)
            self.state = FREE_STATE
            if self.begin.x() < 0:
                self.begin.setX(0)
            elif self.begin.x() > self.width():
                self.begin.setX(self.width())
            if self.begin.y() < 0:
                self.begin.setY(0)
            elif self.begin.y() > self.height():
                self.begin.setY(self.height())
            if self.end.x() < 0:
                self.end.setX(0)
            elif self.end.x() > self.width():
                self.end.setX(self.width())
            if self.end.y() < 0:
                self.end.setY(0)
            elif self.end.y() > self.height():
                self.end.setY(self.height())
                
        rect_xy1 = self.SetupGUI.view.mapToScene(self.begin)
        rect_x1, rect_y1 = rect_xy1.x(), rect_xy1.y()
        rect_xy3 = self.SetupGUI.view.mapToScene(self.end)
        rect_x3, rect_y3 = rect_xy3.x(), rect_xy3.y()
        rect_x1, rect_y1, rect_x3, rect_y3 = int(rect_x1), int(rect_y1), int(rect_x3), int(rect_y3)
        rect_w = rect_x3 - rect_x1
        rect_h = rect_y3 - rect_y1
        pa.DRAW_COORDINATE = {"x": rect_x1, "y": rect_y1, "width": rect_w, "height": rect_h}
        
        self.update_drawed_rect()
        self.update()
        #
    
    def cursor_on_side(self, e_pos) -> int:
        if not self.begin.isNull() and not self.end.isNull():
            y1, y2 = sorted([self.begin.y(), self.end.y()])
            x1, x2 = sorted([self.begin.x(), self.end.x()])
            if y1 <= e_pos.y() <= y2:
                if abs(self.begin.x() - e_pos.x()) <= 5:
                    return CURSOR_ON_BEGIN_SIDE
                elif abs(self.end.x() - e_pos.x()) <= 5:
                    return CURSOR_ON_END_SIDE
            if x1 <= e_pos.x() <= x2:
                if abs(self.begin.y() - e_pos.y()) <= 5:
                    return CURSOR_ON_TOP_SIDE
                elif abs(self.end.y() - e_pos.y()) <= 5:
                    return CURSOR_ON_DOWN_SIDE
        return 0

    def applye_event(self, event):
        if self.state == BUILDING_SQUARE:
            self.end = event.pos()
        elif self.state == BEGIN_SIDE_EDIT:
            self.begin.setX(event.x())
        elif self.state == END_SIDE_EDIT:
            self.end.setX(event.x())
        elif self.state == TOP_SIDE_EDIT:
            self.begin.setY(event.y())
        elif self.state == DOWN_SIDE_EDIT:
            self.end.setY(event.y())
    