# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\gui\mono_plot_orient_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(726, 409)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(380, 380, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.tableWidget = QtWidgets.QTableWidget(Dialog)
        self.tableWidget.setGeometry(QtCore.QRect(10, 40, 461, 271))
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, item)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(500, 10, 200, 190))
        self.groupBox.setMinimumSize(QtCore.QSize(200, 190))
        self.groupBox.setMaximumSize(QtCore.QSize(200, 190))
        self.groupBox.setObjectName("groupBox")
        self.layoutWidget = QtWidgets.QWidget(self.groupBox)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 10, 171, 86))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.layoutWidget)
        self.label_2.setLineWidth(0)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.line_prc_x = QtWidgets.QLineEdit(self.layoutWidget)
        self.line_prc_x.setEnabled(True)
        self.line_prc_x.setMinimumSize(QtCore.QSize(100, 0))
        self.line_prc_x.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_prc_x.setReadOnly(True)
        self.line_prc_x.setObjectName("line_prc_x")
        self.horizontalLayout_2.addWidget(self.line_prc_x)
        self.label_11 = QtWidgets.QLabel(self.layoutWidget)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_2.addWidget(self.label_11)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.layoutWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.line_prc_y = QtWidgets.QLineEdit(self.layoutWidget)
        self.line_prc_y.setMinimumSize(QtCore.QSize(100, 0))
        self.line_prc_y.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_prc_y.setReadOnly(True)
        self.line_prc_y.setObjectName("line_prc_y")
        self.horizontalLayout_3.addWidget(self.line_prc_y)
        self.label_12 = QtWidgets.QLabel(self.layoutWidget)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_3.addWidget(self.label_12)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(self.layoutWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem3)
        self.line_prc_z = QtWidgets.QLineEdit(self.layoutWidget)
        self.line_prc_z.setMinimumSize(QtCore.QSize(100, 0))
        self.line_prc_z.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_prc_z.setReadOnly(True)
        self.line_prc_z.setObjectName("line_prc_z")
        self.horizontalLayout_4.addWidget(self.line_prc_z)
        self.label_13 = QtWidgets.QLabel(self.layoutWidget)
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_4.addWidget(self.label_13)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.layoutWidget1 = QtWidgets.QWidget(self.groupBox)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 100, 171, 80))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        spacerItem4 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem4)
        self.line_alpha = QtWidgets.QLineEdit(self.layoutWidget1)
        self.line_alpha.setMinimumSize(QtCore.QSize(100, 0))
        self.line_alpha.setMaximumSize(QtCore.QSize(100, 16777214))
        self.line_alpha.setReadOnly(True)
        self.line_alpha.setObjectName("line_alpha")
        self.horizontalLayout_5.addWidget(self.line_alpha)
        self.label_14 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_5.addWidget(self.label_14)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_6 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_6.addWidget(self.label_6)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem5)
        self.line_zeta = QtWidgets.QLineEdit(self.layoutWidget1)
        self.line_zeta.setMinimumSize(QtCore.QSize(100, 0))
        self.line_zeta.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_zeta.setReadOnly(True)
        self.line_zeta.setObjectName("line_zeta")
        self.horizontalLayout_6.addWidget(self.line_zeta)
        self.label_15 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_15.setObjectName("label_15")
        self.horizontalLayout_6.addWidget(self.label_15)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_7 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_7.addWidget(self.label_7)
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem6)
        self.line_kappa = QtWidgets.QLineEdit(self.layoutWidget1)
        self.line_kappa.setMinimumSize(QtCore.QSize(100, 0))
        self.line_kappa.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_kappa.setReadOnly(True)
        self.line_kappa.setObjectName("line_kappa")
        self.horizontalLayout_7.addWidget(self.line_kappa)
        self.label_16 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_16.setObjectName("label_16")
        self.horizontalLayout_7.addWidget(self.label_16)
        self.verticalLayout_3.addLayout(self.horizontalLayout_7)
        spacerItem7 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem7)
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setGeometry(QtCore.QRect(500, 200, 200, 110))
        self.groupBox_2.setMinimumSize(QtCore.QSize(200, 110))
        self.groupBox_2.setMaximumSize(QtCore.QSize(200, 110))
        self.groupBox_2.setFlat(False)
        self.groupBox_2.setObjectName("groupBox_2")
        self.layoutWidget2 = QtWidgets.QWidget(self.groupBox_2)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 20, 181, 80))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget2)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem8 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem8)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_8 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_8.addWidget(self.label_8)
        spacerItem9 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem9)
        self.line_x0 = QtWidgets.QLineEdit(self.layoutWidget2)
        self.line_x0.setMinimumSize(QtCore.QSize(100, 0))
        self.line_x0.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_x0.setReadOnly(True)
        self.line_x0.setObjectName("line_x0")
        self.horizontalLayout_8.addWidget(self.line_x0)
        self.label_17 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_17.setObjectName("label_17")
        self.horizontalLayout_8.addWidget(self.label_17)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_9 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_9.addWidget(self.label_9)
        spacerItem10 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem10)
        self.line_y0 = QtWidgets.QLineEdit(self.layoutWidget2)
        self.line_y0.setMinimumSize(QtCore.QSize(100, 0))
        self.line_y0.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_y0.setReadOnly(True)
        self.line_y0.setObjectName("line_y0")
        self.horizontalLayout_9.addWidget(self.line_y0)
        self.label_18 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_18.setObjectName("label_18")
        self.horizontalLayout_9.addWidget(self.label_18)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_10 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_10.addWidget(self.label_10)
        spacerItem11 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem11)
        self.line_f = QtWidgets.QLineEdit(self.layoutWidget2)
        self.line_f.setMinimumSize(QtCore.QSize(100, 0))
        self.line_f.setMaximumSize(QtCore.QSize(100, 16777215))
        self.line_f.setReadOnly(True)
        self.line_f.setObjectName("line_f")
        self.horizontalLayout_10.addWidget(self.line_f)
        self.label_19 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_19.setObjectName("label_19")
        self.horizontalLayout_10.addWidget(self.label_19)
        self.verticalLayout.addLayout(self.horizontalLayout_10)
        spacerItem12 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem12)
        self.layoutWidget3 = QtWidgets.QWidget(Dialog)
        self.layoutWidget3.setGeometry(QtCore.QRect(10, 10, 461, 22))
        self.layoutWidget3.setObjectName("layoutWidget3")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.layoutWidget3)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.combo_raster_lyrs = QtWidgets.QComboBox(self.layoutWidget3)
        self.combo_raster_lyrs.setMinimumSize(QtCore.QSize(250, 0))
        self.combo_raster_lyrs.setMaximumSize(QtCore.QSize(250, 16777215))
        self.combo_raster_lyrs.setObjectName("combo_raster_lyrs")
        self.horizontalLayout.addWidget(self.combo_raster_lyrs)
        spacerItem13 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem13)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "gid"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "X"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Dialog", "Y"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Dialog", "Z"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Dialog", "x"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("Dialog", "y"))
        self.groupBox.setTitle(_translate("Dialog", "EOR"))
        self.label_2.setText(_translate("Dialog", "X:"))
        self.label_11.setText(_translate("Dialog", "[m]"))
        self.label_3.setText(_translate("Dialog", "Y:"))
        self.label_12.setText(_translate("Dialog", "[m]"))
        self.label_4.setText(_translate("Dialog", "Z:"))
        self.label_13.setText(_translate("Dialog", "[m]"))
        self.label_5.setText(_translate("Dialog", "Alpha:"))
        self.label_14.setText(_translate("Dialog", "[°]"))
        self.label_6.setText(_translate("Dialog", "Zeta:"))
        self.label_15.setText(_translate("Dialog", "[°]"))
        self.label_7.setText(_translate("Dialog", "Kappa:"))
        self.label_16.setText(_translate("Dialog", "[°]"))
        self.groupBox_2.setTitle(_translate("Dialog", "IOR"))
        self.label_8.setText(_translate("Dialog", "x0:"))
        self.label_17.setText(_translate("Dialog", "[px]"))
        self.label_9.setText(_translate("Dialog", "y0:"))
        self.label_18.setText(_translate("Dialog", "[px]"))
        self.label_10.setText(_translate("Dialog", "f:"))
        self.label_19.setText(_translate("Dialog", "[px]"))
        self.label.setText(_translate("Dialog", "DTM/DSM:"))