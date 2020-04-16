import cv2
import os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QImage, QPixmap, QPicture, QTransform
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QRect, QSize, Qt
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QRubberBand

'''	Image Display that supports zooming, panning, and drag-n-drop selection
	Requires cv2, QtWidgets.(QGraphicsPixmapItem, QGraphicsScene, QGraphicsView), 
	QtGui.(QPixmap, QPicture, QImage, QTransform), QtCore.(QEvent, QRect, QSize)
'''
class ImageDisplay(QGraphicsView):
	#emitted when an image is set; contains the image path
	image_added = pyqtSignal(str)

	#emitted when a user drags a selection recangle; contains the corners
	rectangleCaptured = pyqtSignal(tuple)

	#emitted when a user right clicks the image
	clearSelection = pyqtSignal()

	#emitted when the widget is resized
	resized = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)

		#track parent:
		self.parent = parent

		#initialize variables:
		self.image = None
		self.rubberBand = None
		self.zoom = 1
		self.imsize = None
		self.setObjectName('img')

	#sets the currently visible image to image and emits self.image_added
	def setImage(self, image):
		self.setImageNoSignal(image)
		self.image_added.emit(image)

	#sets the currently visible image to image; doesn't emit self.image_added
	def setImageNoSignal(self, image):
		#when passed a file, remove the border around the widget
		if not os.path.isfile(image):
			self.setStyleSheet('#img { border: 1px solid #787878; }')
			return
		else:
			self.setStyleSheet('#img { }')

		#keep track of what image is set
		self.file = image

		#detect image dimensions via opencv
		img = cv2.imread(image)
		h, w, _ = img.shape
		self.imsize = (w, h)

		#create QImage and store it
		self.image = QImage(image).scaled(QSize(w, h))

		#create graphics scene from current QImage scaled to current size
		graphic = QGraphicsPixmapItem(QPixmap.fromImage(self.image).scaled(self.size(), Qt.KeepAspectRatio))
		scene = QGraphicsScene()
		scene.addItem(graphic)
		self.setScene(scene)

	#return the currently visible image file
	def getImage(self):
		return self.file

	def getImageSize(self):
		return self.imsize

	#OVERRIDEN EVENT HANDLERS:
	def wheelEvent(self, event):
		#for a normal scroll, pass to super for panning
		if event.modifiers() != Qt.ControlModifier:
			super().wheelEvent(event)
			return

		#for ctrl+scroll zoom 10% in or out based on wheel direction
		if event.angleDelta().y() > 0:
			self.zoom = 1.1 * self.zoom
		else:
			self.zoom = (10 / 11) * self.zoom
			if self.zoom <= 1:
				self.zoom = 1

		#if just returning to default, reset image to avoid small amount of cutoff
		if self.zoom == 1:
			self.setImage(self.getImage())
			return

		#create QTransform to perform scaling to new self.zoom value
		transform = QTransform()
		transform.scale(self.zoom, self.zoom)

		#recreate graphics scene with current image scaled as above
		graphic = QGraphicsPixmapItem(QPixmap.fromImage(self.image).scaled(self.size(), Qt.KeepAspectRatio).transformed(transform))
		scene = QGraphicsScene()
		scene.addItem(graphic)
		self.setScene(scene)

	def resizeEvent(self, event):
		super().resizeEvent(event)
		if self.image == None:
			return
		#recreate graphics scene with current image scaled
		graphic = QGraphicsPixmapItem(QPixmap.fromImage(self.image).scaled(self.size(), Qt.KeepAspectRatio))
		scene = QGraphicsScene()
		scene.addItem(graphic)
		self.setScene(scene)

	def mousePressEvent(self, event):
		#on click start drawing selection box
		if event.button() == Qt.RightButton:
			self.clearSelection.emit()
			return
		self.origin = event.pos()
		self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
		self.rubberBand.setGeometry(QRect(self.origin, QSize()))
		self.rubberBand.show()

	def mouseMoveEvent(self, event):
		#if currently clicking and dragging adjust size of selection box
		if event.button() == Qt.RightButton or self.rubberBand == None:
			return
		self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

	def mouseReleaseEvent(self, event):
		#if previously drawing selection box, now stop and emit signal with its dimensions
		if event.button() == Qt.RightButton or self.rubberBand == None:
			return
		self.rubberBand.hide()
		coordinates = (self.origin, event.pos())
		self.rectangleCaptured.emit(coordinates)