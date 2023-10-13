# -*- coding: utf-8 -*-
"""
/***************************************************************************
moniQue - Monoplotting obliQue images with QGIS.
copyright            : (C) 2021 by Sebastian Mikolka-Flöry
email                : sebastian.floery@geo.tuwien.ac.at
***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication, QAction, QTreeWidgetItem, QFileDialog, QDialog, QMenu, QStyle, QDialogButtonBox

# Initialize Qt resources from file resources.py
from .resources import *
from .camera import Camera

# Import the code for the dialog
from .gui.mono_plot_dialog import MonoPlotDialog
from .gui.img_meta_dlg import MetaWindow
from .gui.orient3d_dlg import Scene3D

from .gui.mono_plot_create_dialog import Ui_Dialog as Ui_CreateDialog
from .gui.mono_plot_change_name_dialog import Ui_ChangeDialog 
from .gui.mono_plot_create_ortho_dialog import Ui_Dialog as Ui_CreateOrthoDialog

import os.path

from qgis.core import (
    Qgis,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsFeature,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsPoint,
    QgsPointXY,
    QgsVectorFileWriter,
    QgsJsonUtils
)

from qgis.gui import QgsMapToolPan, QgsMessageBar, QgsHighlight

from .tools.MonoMapTool import MonoMapTool
from .tools.SelectTool import SelectTool
from .tools.VertexTool import VertexTool

import urllib.request
import urllib.error
import ssl
import os
import json
import numpy as np
from osgeo import gdal
import open3d as o3d

try:
    import laspy
    write_las = True
except:
    print("laspy not available. Skipping import!")
    write_las = False

class MonoPlot:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        self.actions = []
        self.plugin_name = u"moniQue"
        self.toolbar = self.iface.addToolBar(self.plugin_name)
        self.toolbar.setObjectName(self.plugin_name)
        self.menu = self.tr(self.plugin_name)                
               
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        #tmp dir will store the downloaded images
        self.tmp_dir = os.path.join(self.plugin_dir, "tmp")
        if not os.path.exists(self.tmp_dir):
            os.mkdir(self.tmp_dir)
            
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MonoPlot_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = MonoPlotDialog(parent=self.iface.mainWindow())
        self.dlg.setWindowTitle(self.plugin_name)
        self.dlg.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.dlg.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
                
        #img_canvas is the canvas in the Plugin window where the terrestrial image is shown
        self.img_canvas = self.dlg.ImageCanvas
        self.msg_bar = QgsMessageBar(self.img_canvas)
        
        #map_canvas is the canvas of the QGIS main window
        self.map_canvas = iface.mapCanvas()
        
        #img_tree is the tree-like structure where the loaded images are shown in the plugin window
        self.img_tree = self.dlg.ImageTree
        self.img_tree.itemChanged.connect(self.tree_item_changed)
                
        self.meta_window = MetaWindow()
        # self.scene_3d = Scene3D()
        
        self.curr_img_lyr = None
        self.img_line_lyr = None
        self.map_line_lyr = None
        self.cam_lyr = None
        self.cam_hfov_lyr = None
        self.reg_lyr = None
        self.gpkg_path = None
        
        self.pan_tool = QgsMapToolPan(self.img_canvas)
        self.mono_tool = MonoMapTool(self.img_canvas, self.map_canvas, self.meta_window)
        self.select_tool = SelectTool(self.img_canvas, self.map_canvas)
        self.vertex_tool = VertexTool(self.img_canvas, self.map_canvas)
        
        self.dlg.btn_extent.clicked.connect(self.set_extent)
        
        self.dlg.btn_load_mono3d.clicked.connect(lambda: self.load_camera())

        self.dlg.btn_new.clicked.connect(self.create_project)
        self.dlg.btn_load.clicked.connect(self.load_project_dialog)
        
        self.dlg.btn_pan.clicked.connect(self.activate_panning)
        self.dlg.btn_monotool.clicked.connect(self.activate_plotting)
        self.dlg.btn_select.clicked.connect(self.activate_select)
        # self.dlg.btn_delete.clicked.connect(self.delete_selected_features)
        self.dlg.btn_vertex.clicked.connect(self.activate_edit_vertices)
        
        self.dlg.rejected.connect(self.clear)

        self.dlg.ImageTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dlg.ImageTree.customContextMenuRequested.connect(self.ImageTreeMenu)
        self.dlg.ImageTree.setFocusPolicy(Qt.NoFocus)
        
        ssl._create_default_https_context = ssl._create_unverified_context
        
        self.create_dlg_widget = QDialog(self.dlg)
        create_dlg = Ui_CreateDialog()
        create_dlg.setupUi(self.create_dlg_widget)
          
        create_dlg.btn_project_path.clicked.connect(self.new_project_path)
        create_dlg.btn_terrain_path.clicked.connect(self.get_terrain_path)
        
        create_dlg.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)
        
        create_dlg.line_project_path.textChanged.connect(self.create_changed)
        create_dlg.line_terrain_path.textChanged.connect(self.create_changed)
        create_dlg.sel_crs_widget.crsChanged.connect(self.create_changed)
        create_dlg.buttonBox.accepted.connect(self.create_project_file)
        self.create_dlg = create_dlg        

        #==================================
        # CHANGE NAME DIALOG
        #==================================
        self.change_name_widget = QDialog(self.dlg)
        change_name = Ui_ChangeDialog()
        change_name.setupUi(self.change_name_widget)
        change_name.buttonBox.accepted.connect(self.change_image_name)
        self.change_name_dlg = change_name
        
        #==================================
        # ORTHOPHOTO DIALOG
        #==================================
        self.create_ortho_widget = QDialog(self.dlg)
        create_ortho = Ui_CreateOrthoDialog()
        create_ortho.setupUi(self.create_ortho_widget)
        create_ortho.buttonBox.accepted.disconnect()
        create_ortho.buttonBox.accepted.connect(self.create_orthophoto)
        create_ortho.radio_tif.toggled.connect(self.set_tif_options)
        create_ortho.btn_out_path.clicked.connect(self.set_ortho_path)
        self.create_ortho_dlg = create_ortho
        
        self.project_name = None
        self.curr_region = None
        self.camera_collection = {}
        self.active_camera = None
        
        #placeholder for highlighting selected cameras
        self.cam_h = None 
        self.hfov_h = None
        self.vertex_markers = []
        
        self.highlight_color = QColor(Qt.red)
        self.highlight_color.setAlpha(50)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        #icon_path = ':/plugins/mono_plot/gfx/icon.png'
        icon_path = os.path.join(self.plugin_dir, "gfx/icon/icon.png")
        self.add_action(
            icon_path,
            text=self.tr(u'Run tool'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # self.add_action(
        #     None,
        #     text=self.tr(u"Intersect with DTM"),
        #     callback=self.intersect_dtm_widget,
        #     parent=self.iface.mainWindow(),
        #     add_to_toolbar=False)

    def onItemClicked(self, it, col):
        print(it, col, it.text(col))

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(self.plugin_name), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action
    
    def intersect_dtm_widget(self):
        print("Wohoo")
    
    def set_tif_options(self):
        if self.create_ortho_dlg.radio_tif.isChecked():
            self.create_ortho_dlg.label_res.setEnabled(True)
            self.create_ortho_dlg.line_res.setEnabled(True)
            self.create_ortho_dlg.check_toc.setEnabled(True)
            self.create_ortho_dlg.line_out_path.clear()
        else:
            self.create_ortho_dlg.label_res.setEnabled(False)
            self.create_ortho_dlg.line_res.setEnabled(False)
            self.create_ortho_dlg.check_toc.setEnabled(False)
            self.create_ortho_dlg.line_out_path.clear()
    
    def set_ortho_path(self):
        if self.create_ortho_dlg.radio_las.isChecked():
            path, _ = QFileDialog.getSaveFileName(None, 'Save Pointcloud as *.las', '', 'LAS Files (*.las)')
        elif self.create_ortho_dlg.radio_tif.isChecked():
            path, _ = QFileDialog.getSaveFileName(None, 'Save Orthophoto as *.tif', '', 'TIF Files (*.tif)')
        else:
            path = None

        self.create_ortho_dlg.line_out_path.setText(path)
        
    def create_changed(self):
        self.create_dlg.buttonBox.button(QDialogButtonBox.Save).setEnabled(bool(self.create_dlg.line_project_path.text()) and bool(self.create_dlg.line_terrain_path.text()) and bool(self.create_dlg.sel_crs_widget.crs().authid()))

    def remove_camera_from_project(self, cam_id):
        
        expression = "mtum_id = '%s'" % (cam_id)
        request = QgsFeatureRequest().setFilterExpression(expression)
        
        self.img_line_lyr.startEditing()
        self.map_line_lyr.startEditing()
        self.cam_lyr.startEditing()
        self.cam_hfov_lyr.startEditing()
        
        img_feats = self.img_line_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
        for feat in img_feats:
            self.img_line_lyr.deleteFeature(feat.id())
        
        map_feats = self.map_line_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
        for feat in map_feats:
            self.map_line_lyr.deleteFeature(feat.id())
        
        cam_feats = self.cam_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
        for feat in cam_feats:
            self.cam_lyr.deleteFeature(feat.id())
        
        cam_hfov_feats = self.cam_hfov_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
        for feat in cam_hfov_feats:
            self.cam_hfov_lyr.deleteFeature(feat.id())
        
        self.img_line_lyr.commitChanges()
        self.map_line_lyr.commitChanges()
        self.cam_lyr.commitChanges()
        self.cam_hfov_lyr.commitChanges()
        
        self.remove_item_from_tree(cam_id)

        if self.active_camera:
            if self.active_camera.id == cam_id:
                self.clear_highlighted_features()
                self.clear_meta_fiels()
                self.active_camera = None
                
                if self.curr_img_lyr is not None:
                    QgsProject.instance().removeMapLayer(self.curr_img_lyr.id())
                    self.img_canvas.refreshAllLayers()
                    self.curr_img_lyr = None
            else:
                pass
        else:
            pass
        
    def remove_item_from_tree(self, cam_id):
        root = self.img_tree.invisibleRootItem()
        item_to_delete = None
        
        for i in range(root.childCount()):
            item = root.child(i)
            item_id = item.text(0)
            
            if item_id == cam_id:
                item_to_delete = item
                break
        
        root.removeChild(item_to_delete)

        self.clear_highlighted_features()
        
    def show_change_name_dialog(self, cam_id):
        
        root = self.img_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_id = item.text(0)
            
            if item_id == cam_id:
                child_item = item.child(0)
                img_name = child_item.text(0)
        
        self.change_name_dlg.line_new.clear()
        
        self.change_name_dlg.line_cam_id.setText(cam_id)
        self.change_name_dlg.line_old.setText(img_name)
        
        self.change_name_widget.show()

    def show_create_ortho_dialog(self, cam_id):
        self.create_ortho_widget.setWindowTitle(cam_id)
        self.create_ortho_widget.show()
    
    def change_image_name(self):
        change_cam_id = self.change_name_dlg.line_cam_id.text()
        change_new_name = self.change_name_dlg.line_new.text()
        
        root = self.img_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_id = item.text(0)
            
            if item_id == change_cam_id:
                child_item = item.child(0)
                child_item.setText(0, change_new_name)

        
        expression = "mtum_id = '%s'" % (change_cam_id)
        request = QgsFeatureRequest().setFilterExpression(expression)
        hfov_feats = self.cam_hfov_lyr.getFeatures(request)
        hfov_name_ix = self.cam_hfov_lyr.fields().indexFromName("name")
        
        self.cam_hfov_lyr.startEditing()
        for feat in hfov_feats:
            self.cam_hfov_lyr.changeAttributeValue(feat.id(), hfov_name_ix, change_new_name)
        self.cam_hfov_lyr.commitChanges()
    
    def center_on_camera(self, cam_id):
        expression = "mtum_id = '%s'" % (cam_id)
        request = QgsFeatureRequest().setFilterExpression(expression)
            
        cam_feats = self.cam_hfov_lyr.getFeatures(request)
        for feat in cam_feats:
            self.map_canvas.zoomToFeatureExtent(feat.geometry().boundingBox())
    
    def check_for_update(self, cam_id):
        new_cam = Camera(img_id=cam_id)
        old_cam = self.camera_collection[cam_id]
        
        old_prc = old_cam.prc
        new_prc = new_cam.prc
        
        if np.allclose(old_prc, new_prc, atol=1*10**-3):
            return False
        else:
            return True
    
    def update_camera(self, cam_id):
        new_cam = Camera(img_id=cam_id)
        old_cam = self.camera_collection[cam_id]
        
        old_prc = old_cam.prc
        new_prc = new_cam.prc
        
        if np.allclose(old_prc, new_prc, atol=1*10**-3):
            self.msg_bar.pushMessage("Success.", "Camera is up-to-date.", level=Qgis.Success)

        else:
            
            #the image name might have been individually adjusted within the gpkg; in order to not loose this information
            #we overwrite the image name in the new camera object
            if old_cam.meta["name"] != new_cam.meta["name"]:
                new_cam.meta["name"] = old_cam.meta["name"]
            
            QApplication.instance().setOverrideCursor(Qt.WaitCursor)
            
            expression = "mtum_id = '%s'" % (cam_id)
            request = QgsFeatureRequest().setFilterExpression(expression)
            
            img_feats = list(self.img_line_lyr.getFeatures(request)) #show only those lines which correspond to the currently selected image
            
            if img_feats:
                
                self.map_line_lyr.startEditing()
                
                for feat in img_feats:
                    feat_fid = feat.id()
                    feat_geom = feat.geometry()
                                        
                    feat_rays = []
                    
                    for vertex in feat_geom.vertices():
                        v_x = vertex.x()
                        v_y = vertex.y()
                        v_ray = new_cam.ray(img_x = v_x, img_y = v_y)
                        feat_rays.append(v_ray)
                    
                    new_feat_coords = []
                    res = self.tree.intersect_rays(feat_rays, min_dist=0)
                    
                    for coord in res:
                        new_feat_coords.append(QgsPoint(coord[0], coord[1]))
                    
                    feat_upd_geom = QgsGeometry.fromPolyline(new_feat_coords)
                    self.map_line_lyr.changeGeometry(feat_fid, feat_upd_geom)
                
                self.map_line_lyr.commitChanges()
                self.map_line_lyr.triggerRepaint()
                
            
            else:
                pass
            
            self.camera_collection[cam_id] = new_cam
                        
            self.cam_lyr.startEditing()
            self.cam_hfov_lyr.startEditing()
                        
            cam_feats = self.cam_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
            for feat in cam_feats:
                self.cam_lyr.deleteFeature(feat.id())
            
            cam_hfov_feats = self.cam_hfov_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
            for feat in cam_hfov_feats:
                self.cam_hfov_lyr.deleteFeature(feat.id())
                     
            self.cam_lyr.commitChanges()
            self.cam_hfov_lyr.commitChanges()

            self.add_camera_to_lyr(new_cam)
            
            self.msg_bar.pushMessage("Success.", "Sucessfully updated %s." % (cam_id), level=Qgis.Success)
            
            root = self.img_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                item_id = item.text(0)
                
                if item_id == cam_id:
                    item.child(0).setIcon(0, QApplication.style().standardIcon(QStyle.SP_DialogApplyButton))      
            
            QApplication.instance().restoreOverrideCursor()
            
    def load_3dscene(self):
        self.scene_3d = Scene3D()
        
        v = np.array(self.terrain_mesh.vertices)
        f = np.array(self.terrain_mesh.triangles)
        
        self.scene_3d.canvas_wrapper.add_mesh(f, v)
        # self.scene_3d.show()
   
    def ImageTreeMenu(self, point):
        
        # Infos about the node selected.
        index = self.dlg.ImageTree.indexAt(point)

        if not index.isValid():
            return

        item = self.dlg.ImageTree.itemAt(point)
        
        if not item.parent(): #only add context menu for top level items
        
            name = item.text(0)  # The text of the node.
            
            img_menue = QMenu()
            action = img_menue.addAction(name)
            action.setEnabled(False)
            
            img_menue.addSeparator()
            
            action_load3d = img_menue.addAction("Orient image")
            action_load3d.triggered.connect(lambda: self.load_3dscene())
            img_menue.addSeparator()
            
            action_zoom = img_menue.addAction("Center canvas on camera")
            action_zoom.triggered.connect(lambda: self.center_on_camera(name))
            
            img_menue.addSeparator()
            
            action_update = img_menue.addAction("Update camera from Mono3D")
            action_update.triggered.connect(lambda: self.update_camera(name))
            
            action_change = img_menue.addAction("Change image name")
            action_change.triggered.connect(lambda: self.show_change_name_dialog(name))
            
            img_menue.addSeparator()
            
            action_ortho = img_menue.addAction("Create Orthophoto")
            action_ortho.triggered.connect(lambda: self.show_create_ortho_dialog(name))
            
            img_menue.addSeparator()
                         
            action_remove = img_menue.addAction("Remove camera from project")
            action_remove.triggered.connect(lambda: self.remove_camera_from_project(name))
            
            img_menue.exec_(self.dlg.ImageTree.mapToGlobal(point))
    
    def create_orthophoto(self):
        
        QApplication.instance().setOverrideCursor(Qt.WaitCursor)

        cam_id = self.create_ortho_widget.windowTitle()
        cam = self.camera_collection[cam_id]

        if self.create_ortho_dlg.radio_las.isChecked():
            ofmt = "las"
            ores_m = None
            add_toc = False
            
        elif self.create_ortho_dlg.radio_tif.isChecked():
            ofmt = "tif"
            ores_m = float(self.create_ortho_dlg.line_res.text().replace(",", "."))
            add_toc = True if self.create_ortho_dlg.check_toc.isChecked() else False
            
        out_path = self.create_ortho_dlg.line_out_path.text()
        
        img_path = os.path.join(self.tmp_dir, str(cam_id) + ".jpg")
        img_ds = gdal.Open(img_path)
        
        img_w = img_ds.RasterXSize
        img_h = img_ds.RasterYSize
        img_d = img_ds.RasterCount
        
        if img_d == 1:
            img_arr = np.array(img_ds.GetRasterBand(1).ReadAsArray())
            img_arr = np.dstack((img_arr, img_arr, img_arr))
        elif img_d == 3:
            img_b0 = np.array(img_ds.GetRasterBand(1).ReadAsArray())
            img_b1 = np.array(img_ds.GetRasterBand(2).ReadAsArray())
            img_b2 = np.array(img_ds.GetRasterBand(3).ReadAsArray())
            img_arr = np.dstack((img_b0, img_b1, img_b2))

        o3d_cam = cam.to_open3d()
        rays = self.ray_scene.create_rays_pinhole(intrinsic_matrix=o3d_cam.intrinsic.intrinsic_matrix,
                                                  extrinsic_matrix=o3d_cam.extrinsic,
                                                  width_px=cam.img_w,
                                                  height_px=cam.img_h)
        rays = rays.numpy().reshape(img_h*img_w, 6)
        
        try:
            line_min_dist = float(self.create_ortho_dlg.line_min_dist.text())
        except:
            print("Something went wrong...")
            return None
        if line_min_dist < 0:
            print("Not going to do that...")
            return None
        elif line_min_dist > 0:    
            rays[:, 0:3] = rays[:, 0:3] + rays[:, 3:]*line_min_dist
        else:
            pass
        
        rays = o3d.core.Tensor(rays)
        
        ans = self.ray_scene.cast_rays(rays)        
        ans_dist = ans["t_hit"].numpy()
        valid = np.isfinite(ans_dist).ravel()
        
        rays_orig = rays[:, :3].numpy()
        rays_ndir = rays[:, 3:].numpy()
        
        rays_coords = rays_orig[valid, :] + rays_ndir[valid, :]*ans_dist[valid].reshape(-1, 1)
        rays_colors = img_arr.reshape(img_h*img_w, 3)
        rays_colors = rays_colors[valid, :]

        if ofmt == "las":
            
            if write_las:
                header = laspy.LasHeader(point_format=2, version="1.4")
                header.offsets = np.min(rays_coords, axis=0)
                header.scales = np.array([0.01, 0.01, 0.01])

                las_file = laspy.LasData(header)
                las_file.x = rays_coords[:, 0]
                las_file.y = rays_coords[:, 1]
                las_file.z = rays_coords[:, 2]
                
                las_file.red = rays_colors[:, 0]*257
                las_file.green = rays_colors[:, 1]*257
                las_file.blue = rays_colors[:, 2]*257

                las_file.write(out_path)
            else:
                print("laspy not available. Skipping.")
                
        elif ofmt == "tif":
           
            pcl = o3d.geometry.PointCloud()
            rays_coords[:, 2] = 0
            pcl.points = o3d.utility.Vector3dVector(rays_coords)    
            pcl.colors = o3d.utility.Vector3dVector(rays_colors)
            
            pcl_vxl = pcl.voxel_down_sample(ores_m)    
            vxl_coords = np.asarray(pcl_vxl.points)[:, :2]
            vxl_colors = np.asarray(pcl_vxl.colors).astype(np.uint8)
            
            min_vxl_coords = np.min(vxl_coords, axis=0)
            max_vxl_coords = np.max(vxl_coords, axis=0)
            
            nr_cols = int((max_vxl_coords[0] - min_vxl_coords[0]) / ores_m)+1
            nr_rows = int((max_vxl_coords[1] - min_vxl_coords[1]) / ores_m)+1
                        
            vxl_arr = np.zeros((nr_rows, nr_cols, 3), dtype=np.uint8)
            
            vxl_gix = (vxl_coords - min_vxl_coords)/ores_m
            vxl_gix = vxl_gix.astype(np.uint16)
            
            vxl_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel(), 0] = vxl_colors[:, 0]
            vxl_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel(), 1] = vxl_colors[:, 1]
            vxl_arr[vxl_gix[:, 1].ravel(), vxl_gix[:, 0].ravel(), 2] = vxl_colors[:, 2]
            vxl_arr = np.flipud(vxl_arr)
                        
            driver = gdal.GetDriverByName("GTiff")
            outdata = driver.Create(out_path, nr_cols, nr_rows, 3, gdal.GDT_Byte)
            outdata.SetGeoTransform([min_vxl_coords[0]-ores_m/2., #tl x
                                     ores_m, #res x
                                     0, #rot x
                                     max_vxl_coords[1]+ores_m/2., #tl y
                                     0, #rot y
                                     ores_m*(-1)]) #res y

            outdata.SetProjection(self.crs.toWkt())
            outdata.GetRasterBand(1).WriteArray(vxl_arr[:, :, 0])
            outdata.GetRasterBand(2).WriteArray(vxl_arr[:, :, 1])
            outdata.GetRasterBand(3).WriteArray(vxl_arr[:, :, 2])
            outdata.GetRasterBand(1).SetNoDataValue(0)
            outdata.FlushCache()
            
            if add_toc:
                mp_lyr = QgsRasterLayer(out_path, os.path.basename(out_path).split(".")[0])
                QgsProject.instance().addMapLayer(mp_lyr, True) 
        
        QApplication.instance().restoreOverrideCursor()

    def load_terrain_model(self, mesh=None):
        
        if mesh is None:
            
            reg_feat = list(self.reg_lyr.getFeatures())[0]
            # mesh_path = reg_feat["path"] #! workaround for EGU23; can be changed again afterwards;
            mesh_path = os.path.join(self.tmp_dir, reg_feat["name"])
            terrain_mesh = o3d.io.read_triangle_mesh(mesh_path)
        else:
            terrain_mesh = mesh
        
        self.terrain_mesh = terrain_mesh
          
        terrain_mesh.compute_triangle_normals()
        terrain_mesh_leg = o3d.t.geometry.TriangleMesh.from_legacy(terrain_mesh)

        scene = o3d.t.geometry.RaycastingScene()
        scene.add_triangles(terrain_mesh_leg)
        
        self.ray_scene = scene
        self.mono_tool.set_scene(scene)
        self.vertex_tool.set_scene(scene)
        
    def create_project_file(self):
        
        QApplication.instance().setOverrideCursor(Qt.WaitCursor)
        transform_context = QgsProject.instance().transformContext() #necessary for writing
                
        gpkg_path = str(self.create_dlg.line_project_path.text())
        mesh_path = str(self.create_dlg.line_terrain_path.text())
        sel_crs = self.create_dlg.sel_crs_widget.crs().authid()
        
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        
        mesh_bbox = mesh.get_axis_aligned_bounding_box()
        mesh_centroid = mesh_bbox.get_center()
        mesh_cx = mesh_centroid[0]
        mesh_cy = mesh_centroid[1]
        
        mesh_half_extent = mesh_bbox.get_half_extent()
        mesh_dx = mesh_half_extent[0]
        mesh_dy = mesh_half_extent[1]

        mesh_tl = [mesh_cx - mesh_dx, mesh_cy+mesh_dy]
        mesh_tr = [mesh_cx + mesh_dx, mesh_cy+mesh_dy]
        mesh_br = [mesh_cx + mesh_dx, mesh_cy-mesh_dy]
        mesh_bl = [mesh_cx - mesh_dx, mesh_cy-mesh_dy]
        
        mesh_bbox = [QgsPointXY(mesh_tl[0], mesh_tl[1]),
                     QgsPointXY(mesh_tr[0], mesh_tr[1]),
                     QgsPointXY(mesh_br[0], mesh_br[1]),
                     QgsPointXY(mesh_bl[0], mesh_bl[1]),
                     QgsPointXY(mesh_tl[0], mesh_tl[1])]
            
        reg_lyr = QgsVectorLayer("Polygon?crs=%s" % (sel_crs), "region", "memory")
        pr = reg_lyr.dataProvider()
        pr.addAttributes([QgsField("name", QVariant.String)])
        pr.addAttributes([QgsField("path", QVariant.String)])
        reg_lyr.updateFields() 
            
        # add a feature
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPolygonXY([mesh_bbox]))
        fet.setAttributes([os.path.basename(mesh_path), mesh_path])
        pr.addFeatures([fet])

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        reg_lyr.updateExtents()
        
        #write region layer to geopackage
        lyr_options = QgsVectorFileWriter.SaveVectorOptions()
        lyr_options.layerName = reg_lyr.name()
        
        if hasattr(QgsVectorFileWriter, 'writeAsVectorFormatV3'): #for QGIS Version >3.20
            use_v3 = True
            _writer = QgsVectorFileWriter.writeAsVectorFormatV3(reg_lyr, gpkg_path, transform_context, lyr_options)
        elif hasattr(QgsVectorFileWriter, 'writeAsVectorFormatV2'): #for QGIS Version <3.20
            use_v3 = False
            _writer = QgsVectorFileWriter.writeAsVectorFormatV2(reg_lyr, gpkg_path, transform_context, lyr_options)
            
        if _writer[0] == QgsVectorFileWriter.NoError:
            pass
        else:
            self.msg_bar.pushMessage("Error", "Could not create project.", level=Qgis.Critical, duration=3)
            raise ValueError("Could not create project!")
                            
        #create additionally needed layers and add them to the geopackage as well
        cam_lyr = QgsVectorLayer("Point?crs=%s" % (sel_crs), "cameras", "memory")
        cam_pr = cam_lyr.dataProvider()
        cam_pr.addAttributes([QgsField("mtum_id", QVariant.String),
                                QgsField("s0", QVariant.Double, "double", 10, 1),
                                QgsField("x0", QVariant.Double, "double", 10, 1),
                                QgsField("y0", QVariant.Double, "double", 10, 1),
                                QgsField("f", QVariant.Double, "double", 10, 1),
                                QgsField("std_f", QVariant.Double, "double", 10, 1),
                                QgsField("E", QVariant.Double, "double", 10, 3),
                                QgsField("std_E", QVariant.Double, "double", 10, 3),
                                QgsField("N", QVariant.Double, "double", 10, 3),
                                QgsField("std_N", QVariant.Double, "double", 10, 3),
                                QgsField("H", QVariant.Double, "double", 10, 3),
                                QgsField("std_H", QVariant.Double, "double", 10, 3),
                                QgsField("alpha", QVariant.Double, "double", 10, 5),
                                QgsField("std_alpha", QVariant.Double, "double", 10, 3),
                                QgsField("zeta", QVariant.Double, "double", 10, 3),
                                QgsField("std_zeta", QVariant.Double, "double", 10, 5),
                                QgsField("kappa", QVariant.Double, "double", 10, 5),
                                QgsField("std_kappa", QVariant.Double, "double", 10, 3)])
        cam_lyr.updateFields() 
        
        cam_hfov_lyr = QgsVectorLayer("Polygon?crs=%s" % (sel_crs), "cameras_hfov", "memory")
        cam_hfov_pr = cam_hfov_lyr.dataProvider()
        cam_hfov_pr.addAttributes([QgsField("mtum_id", QVariant.String),
                                    QgsField("name", QVariant.String),
                                    QgsField("img_w", QVariant.Int),
                                    QgsField("img_h", QVariant.Int),
                                    QgsField("von", QVariant.String),
                                    QgsField("bis", QVariant.String),
                                    QgsField("hor_fov", QVariant.Double, "double", 6, 3),
                                    QgsField("ver_fov", QVariant.Double, "double", 6, 3),
                                    QgsField("archiv", QVariant.String),
                                    QgsField("bildtraeger", QVariant.String),
                                    QgsField("kanaele", QVariant.String),
                                    QgsField("blickfeld", QVariant.String),
                                    QgsField("bildinhalt", QVariant.String),
                                    QgsField("bemerkungen", QVariant.String),
                                    QgsField("photograph", QVariant.String),
                                    QgsField("copyright", QVariant.String),
                                    ])
        cam_hfov_lyr.updateFields() 
        
        map_line_lyr = QgsVectorLayer("LineString?crs=%s" % (sel_crs), "lines", "memory")
        map_line_pr = map_line_lyr.dataProvider()
        map_line_pr.addAttributes([QgsField("mtum_id", QVariant.String)])
        map_line_pr.addAttributes([QgsField("von", QVariant.String)])
        map_line_pr.addAttributes([QgsField("bis", QVariant.String)])
        map_line_pr.addAttributes([QgsField("type", QVariant.String)])
        map_line_pr.addAttributes([QgsField("comment", QVariant.String)])
        map_line_lyr.updateFields() 
        
        map_line_pnts_lyr = QgsVectorLayer("Point?crs=%s" % (sel_crs), "lines_vertices", "memory")
        
        img_line_lyr = QgsVectorLayer("LineString", "lines_img", "memory")
        img_line_pr = img_line_lyr.dataProvider()
        img_line_pr.addAttributes([QgsField("mtum_id", QVariant.String)])
        img_line_pr.addAttributes([QgsField("von", QVariant.String)])
        img_line_pr.addAttributes([QgsField("bis", QVariant.String)])
        img_line_pr.addAttributes([QgsField("type", QVariant.String)])
        img_line_pr.addAttributes([QgsField("comment", QVariant.String)])
        img_line_lyr.updateFields() 
        
        img_line_pnts_lyr = QgsVectorLayer("Point", "lines_img_vertices", "memory")
        
        lyrs = [cam_lyr, cam_hfov_lyr, map_line_lyr, map_line_pnts_lyr, img_line_lyr, img_line_pnts_lyr]              
        
        for lyr in lyrs:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer    
            options.layerName = lyr.name()
            
            if use_v3: #QGIS < 3.20
                _writer = QgsVectorFileWriter.writeAsVectorFormatV3(lyr, gpkg_path, transform_context, options)
            else:
                _writer = QgsVectorFileWriter.writeAsVectorFormatV2(lyr, gpkg_path, transform_context, options)
            
            if _writer[0] == QgsVectorFileWriter.NoError:
                pass
            else:
                self.msg_bar.pushMessage("Error", "Could not create project.", level=Qgis.Critical, duration=3)
                raise ValueError("Could not create project!")
        
        QApplication.instance().restoreOverrideCursor()

        self.load_project(gpkg_path, terrain=mesh)
                
    def new_project_path(self):
        path = QFileDialog.getSaveFileName(None, 'Create new monoplotting project', '', 'All Files (*.gpkg)')[0]
        if path != '':
            self.create_dlg.line_project_path.setText(path)
    
    def get_terrain_path(self):
        path = QFileDialog.getOpenFileName(None, 'Select terrain file.', '', 'All Files (*.ply)')[0]
        if path != '':
            self.create_dlg.line_terrain_path.setText(path)
                        
    def create_project(self):
        self.create_dlg_widget.show()
    
    def load_project_dialog(self):
        path = QFileDialog.getOpenFileName(None, 'Load existing monoplotting project', '', 'All Files (*.gpkg)')[0]
        if path:
            self.load_project(path, terrain=None)
    
    def load_project(self, path, terrain=None):
        
        self.clear() #clear is a custom function and clears all variables, layers,.....
        
        QApplication.instance().setOverrideCursor(Qt.WaitCursor)
        
        self.project_name = os.path.basename(path)[:-5]
        
        #paths to the styling files
        cam_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "camera.qml")
        cam_hfov_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "camera_hfov.qml")
        img_line_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "lines_img.qml")
        map_line_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "lines_map.qml")
        map_region_qml_path = os.path.join(self.plugin_dir, "gfx", "qml", "region_map.qml")
        
        #load layers from geopackage
        gpkg_reg_lyr = path + "|layername=region"
        reg_lyr = QgsVectorLayer(gpkg_reg_lyr, "region", "ogr")
        reg_lyr.loadNamedStyle(map_region_qml_path)
        self.reg_lyr = reg_lyr 
                
        gpkg_cam_lyr = path + "|layername=cameras"
        cam_lyr = QgsVectorLayer(gpkg_cam_lyr, "cameras", "ogr")           
        self.cam_lyr = cam_lyr
        self.cam_lyr.loadNamedStyle(cam_qml_path)
                
        gpkg_cam_hfov_lyr = path + "|layername=cameras_hfov"
        cam_hfov_lyr = QgsVectorLayer(gpkg_cam_hfov_lyr, "cameras_hfov", "ogr")
        
        #necessary as previous created files did not contain this attribute column
        necessary_fields = ["name", "img_w", "img_h", "von", "bis", "archiv", "bildtraeger", "kanaele", "blickfeld", "bildinhalt", "bemerkungen", "photograph", "copyright"]
        necessary_types = [QVariant.String, QVariant.Int, QVariant.Int, QVariant.String, QVariant.String, QVariant.String, QVariant.String, QVariant.String, QVariant.String, QVariant.String, QVariant.String, QVariant.String, QVariant.String]
        
        avail_fields = cam_hfov_lyr.fields().names()
        
        cam_hfov_lyr.startEditing()
        for ix, field in enumerate(necessary_fields):
            if field not in avail_fields:
                cam_hfov_lyr.addAttribute(QgsField(field, necessary_types[ix]))    
            
        cam_hfov_lyr.commitChanges()
        
        self.cam_hfov_lyr = cam_hfov_lyr
        self.cam_hfov_lyr.loadNamedStyle(cam_hfov_qml_path)
        
        # add cameras already present in the geopackage to the treeWidget
        for cam_feat in cam_lyr.getFeatures():
            cam_mtum_id = cam_feat["mtum_id"]
            # print(cam_mtum_id)
            self.load_camera(img_id=cam_mtum_id, from_gpkg=True)
        
        gpkg_map_lines_lyr = path + "|layername=lines"
        map_line_lyr = QgsVectorLayer(gpkg_map_lines_lyr, "lines", "ogr")
        self.map_line_lyr = map_line_lyr
        self.map_line_lyr.loadNamedStyle(map_line_qml_path)
       
        gpkg_img_lines_lyr = path + "|layername=lines_img"
        img_line_lyr = QgsVectorLayer(gpkg_img_lines_lyr, "lines_img", "ogr")
        self.img_line_lyr = img_line_lyr
        self.img_line_lyr.loadNamedStyle(img_line_qml_path)       

        QgsProject.instance().addMapLayer(self.img_line_lyr, False)
        QgsProject.instance().addMapLayer(self.map_line_lyr, False)
        QgsProject.instance().addMapLayer(self.cam_lyr, False)    
        QgsProject.instance().addMapLayer(self.cam_hfov_lyr, False) 
        QgsProject.instance().addMapLayer(self.reg_lyr, False)

        root = QgsProject.instance().layerTreeRoot()
        monoGroup = root.insertGroup(0, self.project_name)
        monoGroup.addLayer(self.map_line_lyr) 
        monoGroup.addLayer(self.cam_lyr) 
        monoGroup.addLayer(self.cam_hfov_lyr) 
        monoGroup.addLayer(self.img_line_lyr) 
        monoGroup.addLayer(self.reg_lyr)

        self.map_canvas.setExtent(self.reg_lyr.extent())
        self.map_canvas.refresh()
        
        self.dlg.setWindowTitle(self.project_name)
        
        self.activate_buttons()
               
        self.mono_tool.set_layers(self.img_line_lyr, self.map_line_lyr)
        self.select_tool.set_layers(self.img_line_lyr, self.map_line_lyr)
        self.vertex_tool.set_layers(self.img_line_lyr, self.map_line_lyr)
        
        self.gpkg_path = path
        
        self.load_terrain_model(mesh=terrain)
        
        self.crs = self.cam_lyr.crs()
        
        QApplication.instance().restoreOverrideCursor()
        
    def activate_buttons(self):
        self.dlg.btn_extent.setEnabled(True)
        self.dlg.btn_pan.setEnabled(True)
        self.dlg.btn_load_mono3d.setEnabled(True)
        self.dlg.line_id.setEnabled(True)
        
    def deactivate_buttons(self):
        self.dlg.btn_load_mono3d.setEnabled(False)
        
        self.dlg.btn_extent.setEnabled(False)
        self.dlg.btn_pan.setEnabled(False)
        
        self.dlg.btn_monotool.setEnabled(False)
        self.dlg.btn_monotool.setChecked(False)
        
        self.dlg.line_id.setEnabled(False)
        
        self.dlg.btn_select.setEnabled(False)
        self.dlg.btn_select.setChecked(False)
        
        self.dlg.btn_vertex.setEnabled(False)
        self.dlg.btn_vertex.setChecked(False)

    def save_project_as(self):
        _ = QFileDialog.getSaveFileName(None, 'Save current monoplotting project as...', '', 'All Files (*.gpkg)')
    
    def clear(self):
        
        root = QgsProject.instance().layerTreeRoot()
        monoGroup = root.findGroup(self.project_name)
        root.removeChildNode(monoGroup)
        
        self.clear_highlighted_features()    
        
        if self.curr_img_lyr is not None:
            QgsProject.instance().removeMapLayer(self.curr_img_lyr.id())
            self.curr_img_lyr = None
        
        if self.cam_lyr is not None:
            QgsProject.instance().removeMapLayer(self.cam_lyr.id())
            self.cam_lyr = None
            
        if self.cam_hfov_lyr is not None:
            QgsProject.instance().removeMapLayer(self.cam_hfov_lyr.id())
            self.cam_hfov_lyr = None
        
        if self.img_line_lyr is not None:
            QgsProject.instance().removeMapLayer(self.img_line_lyr.id())
            self.img_line_lyr = None
        
        if self.map_line_lyr is not None:
            QgsProject.instance().removeMapLayer(self.map_line_lyr.id())
            self.map_line_lyr = None
        
        if self.reg_lyr is not None:
            QgsProject.instance().removeMapLayer(self.reg_lyr.id())
            self.reg_lyr = None
        
        self.img_canvas.refresh()
        self.map_canvas.refresh()
        self.img_tree.clear()
        
        self.dlg.line_id.clear()
        self.deactivate_buttons()
        self.clear_meta_fiels()
        
        self.map_canvas.setMapTool(QgsMapToolPan(self.map_canvas))
        self.img_canvas.setMapTool(self.pan_tool)
        
        self.dlg.setWindowTitle("SEHAG")
        
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MonoPlot', message)

    def set_extent(self):
        self.img_canvas.setExtent(self.curr_img_lyr.extent())
        self.img_canvas.refresh()
        
    def load_terr_img(self, img_id):
        
        img_path = os.path.join(self.tmp_dir, str(img_id) + ".jpg")
        img_lyr = QgsRasterLayer(img_path, img_id)
                
        if not img_lyr.isValid():
            self.msg_bar.pushMessage("Error", "Could not load %s!" % (img_path), level=Qgis.Critical, duration=3)
        else:
            #remove old image layer
            if self.curr_img_lyr is not None:
                QgsProject.instance().removeMapLayer(self.curr_img_lyr.id())
                
            QgsProject.instance().addMapLayer(img_lyr, False) #False --> do not add layer to LayerTree --> not visible in qgis main canvas
            self.img_canvas.setExtent(img_lyr.extent())
            self.img_canvas.setLayers([self.img_line_lyr, img_lyr])
            self.curr_img_lyr = img_lyr
    
    def get_camera_dict(self, cam_id):
        cam_dict = dict.fromkeys(["sigma0", "img_id", "name", "eor", "ior", "gcps", "qvv", "cxx", "meta"])
        cam_dict["eor"] = dict.fromkeys(["prj_ctr", "rot"])
        # cam_dict["eor"]["prj_ctr"] = dict.fromkeys(["E", "std_E", "N", "std_N", "H", "std_H", "X", "Y", "Z"])
        # cam_dict["eor"]["rot"] = dict.fromkeys(["rot_mat_ecef", "rot_mat_utm", "alpha", "std_rot_a", "zeta", "std_rot_z", "kappa", "std_rot_k"])
        # cam_dict["ior"] = dict.fromkeys(["x0", "std_x0", "y0", "std_y0", "f0", "std_f0"])
        # cam_dict["meta"] = dict.fromkeys(["archiv", "name", "bildtraeger", "kanaele", "von", "bis", "blickfeld", "bildinhalt", "bemerkungen", "photograph", "copyright", "width", "height"])

        expression = "mtum_id = '%s'" % (cam_id)
        request = QgsFeatureRequest().setFilterExpression(expression)
        
        cam_feats = self.cam_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
        for feat in cam_feats:
            feat_json = json.loads(QgsJsonUtils.exportAttributes(feat))
        
        cam_dict["sigma0"] = feat_json["s0"]
        cam_dict["img_id"] = feat_json["mtum_id"]
        cam_dict["name"] = feat_json["mtum_id"]
        
        cam_dict["eor"]["prj_ctr"] = {"E":feat_json["E"],
                                      "std_E":feat_json["std_E"],
                                      "N":feat_json["N"],
                                      "std_N":feat_json["std_N"],
                                      "H":feat_json["H"],
                                      "std_H":feat_json["std_H"],
                                      "X":None,
                                      "Y":None,
                                      "Z":None}
        
        cam_dict["eor"]["rot"] = {"rot_mat_ecef":None,
                                  "rot_mat_utm":None,
                                  "alpha":feat_json["alpha"],
                                  "std_rot_a":feat_json["std_alpha"],
                                  "zeta":feat_json["zeta"],
                                  "std_rot_z":feat_json["std_zeta"],
                                  "kappa":feat_json["kappa"],
                                  "std_rot_k":feat_json["std_kappa"]}
        
        cam_dict["ior"] = {"x0":feat_json["x0"],
                           "std_x0":None,
                           "y0":feat_json["y0"],
                           "std_y0":None,
                           "f0":feat_json["f"],
                           "std_f0":feat_json["std_f"]}
                    
        cam_hfov_feats = self.cam_hfov_lyr.getFeatures(request) #show only those lines which correspond to the currently selected image
        for feat in cam_hfov_feats:
            feat_json = json.loads(QgsJsonUtils.exportAttributes(feat))
        
        cam_dict["meta"] = {"archiv":feat_json["archiv"],
                            "name": feat_json["name"],
                            "bildtraeger":feat_json["bildtraeger"],
                            "kanaele":feat_json["kanaele"],
                            "von":feat_json["von"],
                            "bis":feat_json["bis"],
                            "blickeld":feat_json["blickfeld"],
                            "bildinhalt":feat_json["bildinhalt"],
                            "bemerkungen":feat_json["bemerkungen"],
                            "photograph":feat_json["photograph"],
                            "copyright":feat_json["copyright"],
                            "width": feat_json["img_w"],
                            "height": feat_json["img_h"]}          
        return cam_dict       
        
    def load_camera(self, img_id=None, from_gpkg=False):
        
        #if camera is loaded from gpkg img_is passed as argument; if not, than the img_id is read from the input field
        if img_id is None:
            img_id = self.dlg.line_id.text()
        
        already_loaded = False
        
        root = self.img_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_id = item.text(0)
            
            if item_id == img_id:
                already_loaded = True
        
        self.dlg.line_id.clear()
        
        if not already_loaded:
            
            if from_gpkg: #camera has been loaded previously; therefore the camera object is created from the geopackakge
                
                cam_dict = self.get_camera_dict(img_id)
                cam = Camera()
                cam.from_dict(cam_dict)
                self.camera_collection[cam.id] = cam  
                self.add_camera_to_tree(cam)               
                
                img_path = os.path.join(self.tmp_dir, str(img_id) + ".jpg")
                if not os.path.exists(img_path): #check if images has already been downloaded previosly...
                    try:
                        urllib.request.urlretrieve("https://sehag.geo.tuwien.ac.at/fcgi-bin/iipsrv.fcgi?IIIF=%s.tif/full/full/0/native.jpg" % (str(img_id)), img_path)
                    except:
                        self.msg_bar.pushMessage("Error", "Could not download %s!" % (img_id), level=Qgis.Critical, duration=3)
            else:
                            
                cam = Camera(img_id=img_id)
                
                if cam.status == "ok":
                    
                    img_path = os.path.join(self.tmp_dir, str(img_id) + ".jpg")
                    print(img_path)
                    
                    if not os.path.exists(img_path): #check if images has already been downloaded previosly...
                        try:
                            urllib.request.urlretrieve("https://sehag.geo.tuwien.ac.at/fcgi-bin/iipsrv.fcgi?IIIF=%s.tif/full/full/0/native.jpg" % (str(img_id)), img_path)
                        except:
                            self.msg_bar.pushMessage("Error", "Could not download %s!" % (img_id), level=Qgis.Critical, duration=3)

                    self.camera_collection[cam.id] = cam    
                    self.add_camera_to_tree(cam)
                    self.add_camera_to_lyr(cam)          
            
                else:
                    self.msg_bar.pushMessage("Error", cam.status_msg, level=Qgis.Critical, duration=3)
                    
        else:
            self.msg_bar.pushMessage("Warning", "%s already loaded." % (img_id), level=Qgis.Warning, duration=3)
            self.dlg.line_id.clear()

    def activate_plotting(self):
        
        if not self.dlg.btn_monotool.isChecked(): #we check this if btn is already pressed;
            self.img_canvas.unsetMapTool(self.mono_tool)
            self.img_canvas.setMapTool(self.pan_tool)
            self.dlg.btn_pan.setChecked(True)
            
        else:
            self.img_canvas.setMapTool(self.mono_tool)
            self.mono_tool.reset()

            self.dlg.btn_pan.setChecked(False)
            
            self.dlg.btn_select.setChecked(False)
            self.clear_selected_features()
            
            self.dlg.btn_vertex.setChecked(False)
            self.clear_vertex_markers()
            
    def activate_select(self):
        
        if not self.dlg.btn_select.isChecked(): #we check this if btn is already pressed;
            
            self.clear_selected_features()
            
            self.img_canvas.unsetMapTool(self.select_tool)
            self.img_canvas.setMapTool(self.pan_tool)
            self.dlg.btn_pan.setChecked(True)
            
        else:
            self.img_canvas.setMapTool(self.select_tool)
            
            self.dlg.btn_monotool.setChecked(False)
            self.dlg.btn_pan.setChecked(False)
            self.dlg.btn_vertex.setChecked(False)
            self.clear_vertex_markers()
    
    def clear_vertex_markers(self):
        if len(self.vertex_markers) > 0:
            for m in self.vertex_markers:
                self.img_canvas.scene().removeItem(m)
    
    def activate_panning(self):
        self.img_canvas.setMapTool(self.pan_tool)
        self.dlg.btn_monotool.setChecked(False)
        self.dlg.btn_select.setChecked(False)
        self.dlg.btn_vertex.setChecked(False)            
    
    def activate_edit_vertices(self):
        if not self.dlg.btn_vertex.isChecked(): #we check this if btn is already pressed;
            self.img_canvas.unsetMapTool(self.vertex_tool)
            self.img_canvas.setMapTool(self.pan_tool)
            self.dlg.btn_pan.setChecked(True)
            self.clear_vertex_markers()
            
        else:
            self.img_canvas.setMapTool(self.vertex_tool)
            
            self.img_canvas.snappingUtils().toggleEnabled()

            
            self.dlg.btn_select.setChecked(False)
            self.clear_selected_features()
            
            self.dlg.btn_monotool.setChecked(False)
            self.dlg.btn_pan.setChecked(False)
                    
    def deactivate_plotting(self):
        self.img_canvas.unsetMapTool(self.mono_tool)
        self.img_canvas.setMapTool(self.pan_tool)
    
    def uncheck_items_in_tree(self, new_item):
        root = self.img_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.checkState(0) == Qt.Checked and item != new_item:
                item.setCheckState(0, Qt.Unchecked)

            if item != new_item:
                item.setSelected(False)
            
    def add_camera_to_lyr(self, camera):
        fet = QgsFeature(self.cam_lyr.fields())
        fet.setGeometry(QgsGeometry(QgsPoint(camera.prc[0], camera.prc[1], camera.prc[2])))
        
        fet["mtum_id"] = camera.id
        fet["s0"] = camera.s0
        fet["x0"] = float(camera.ior[0])
        fet["y0"] = float(camera.ior[1])
        fet["f"] = float(camera.ior[2])
        fet["std_f"] = float(camera.ior_std[2])
        fet["E"] = float(camera.prc[0])
        fet["std_E"] = float(camera.prc_std[0])
        fet["N"] = float(camera.prc[1])
        fet["std_N"] = float(camera.prc_std[1])
        fet["H"] = float(camera.prc[2])
        fet["std_H"] = float(camera.prc_std[2])
        fet["alpha"] = float(camera.alpha) #* 180 / math.pi
        fet["std_alpha"] = float(camera.euler_std[0])
        fet["zeta"] = float(camera.zeta) #* 180 / math.pi
        fet["std_zeta"] = float(camera.euler_std[1])
        fet["kappa"] = float(camera.kappa) #* 180 / math.pi
        fet["std_kappa"] = float(camera.euler_std[2])
                
        pr = self.cam_lyr.dataProvider()
        pr.addFeatures([fet])
        
        # Commit changes
        self.cam_lyr.commitChanges()
        self.cam_lyr.triggerRepaint()
        
        hfov_fet = QgsFeature(self.cam_hfov_lyr.fields())
        hfov_fet.setGeometry(QgsGeometry.fromWkt(camera.hfov_geom(dist=100)))
        hfov_fet["mtum_id"] = camera.id
        hfov_fet["hor_fov"] = float(camera.hfov)#* 180 / math.pi
        hfov_fet["ver_fov"] = float(camera.vfov)# * 180 / math.pi
        hfov_fet["von"] = camera.meta["von"]
        hfov_fet["bis"] = camera.meta["bis"]
        hfov_fet["name"] = camera.meta["name"]
        hfov_fet["img_w"] = camera.meta["width"]
        hfov_fet["img_h"] = camera.meta["height"]
        hfov_fet["archiv"] = camera.meta["archiv"]
        hfov_fet["bildtraeger"] = camera.meta["bildtraeger"]
        hfov_fet["kanaele"] = camera.meta["kanaele"]
        hfov_fet["blickfeld"] = camera.meta["blickfeld"]
        hfov_fet["bemerkungen"] = camera.meta["bemerkungen"]
        hfov_fet["photograph"] = camera.meta["photograph"]
        hfov_fet["copyright"] = camera.meta["copyright"]
        
        pr = self.cam_hfov_lyr.dataProvider()
        pr.addFeatures([hfov_fet])
        
        self.cam_hfov_lyr.commitChanges()
        self.cam_hfov_lyr.triggerRepaint()
                
        self.map_canvas.refresh()
        
    def add_camera_to_tree(self, camera):
                        
        l1 = QTreeWidgetItem([camera.id])
        l1.setCheckState(0, Qt.Unchecked)  
        l1.setFlags(l1.flags() & ~Qt.ItemIsSelectable)
        
        l1_child = QTreeWidgetItem([camera.meta["name"]])
        
        if self.check_for_update(camera.id):
            l1_child.setIcon(0, QApplication.style().standardIcon(QStyle.SP_BrowserReload))  
        else:
            l1_child.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DialogApplyButton))      
        
        l1_child.setFlags(l1.flags() & ~Qt.ItemIsSelectable) #child showing image name is no selectable
        l1.addChild(l1_child)
    
        self.img_tree.addTopLevelItem(l1)
        self.img_tree.expandItem(l1)
           
    def clear_meta_fiels(self):
        self.dlg.line_cam_e.clear()
        self.dlg.line_cam_n.clear()
        self.dlg.line_cam_h.clear()
        self.dlg.line_cam_dh.clear()
        self.dlg.line_cam_a.clear()
        self.dlg.line_cam_z.clear()
        self.dlg.line_cam_k.clear()
        
    def fill_meta_fields(self, camera):
        self.dlg.line_cam_e.setText("%.2f" % (camera.prc[0]))
        self.dlg.line_cam_n.setText("%.2f" % (camera.prc[1]))
        self.dlg.line_cam_h.setText("%.2f" % (camera.prc[2]))
        self.dlg.line_cam_dh.setText("-1")
        self.dlg.line_cam_a.setText("%.3f" % (camera.euler[0]*180/np.pi))
        self.dlg.line_cam_z.setText("%.3f" % (camera.euler[1]*180/np.pi))
        self.dlg.line_cam_k.setText("%.3f" % (camera.euler[2]*180/np.pi))
    
    def clear_highlighted_features(self):
        if self.cam_h is not None:
            self.map_canvas.scene().removeItem(self.cam_h)
            
        if self.hfov_h is not None:
            self.map_canvas.scene().removeItem(self.hfov_h)

        if self.map_line_lyr is not None:
            self.map_line_lyr.removeSelection()
    
    def clear_selected_features(self):
        self.img_line_lyr.removeSelection()
        self.map_line_lyr.removeSelection()
    
    def delete_selected_features(self):
        self.map_line_lyr.startEditing()
        self.img_line_lyr.startEditing()
        
        self.map_line_lyr.deleteSelectedFeatures()
        self.img_line_lyr.deleteSelectedFeatures()
        
        self.map_line_lyr.commitChanges()
        self.img_line_lyr.commitChanges()
    
    def tree_item_changed(self, item, column):
        
        #if the name of the image in the treewidget is changed this signal is also emitted; as we only want to run this
        #function if the main item (img_id) was checked or not checked we look for the parent. for the main item the parent is None
        #whereas when the image name changes the parent is not None.
        if not item.parent():
        
            # Get his status when the check status changes.
            if item.checkState(column) == Qt.Checked:
                
                item.setSelected(True)            
                mtum_id = item.text(column)
                
                self.uncheck_items_in_tree(item)
                self.load_terr_img(mtum_id)
                self.active_camera = self.camera_collection[mtum_id]
                
                self.fill_meta_fields(self.active_camera)
                
                #highlight currently selected camera
                #clear previously highlighter cameras
                self.clear_highlighted_features()
                self.clear_vertex_markers()
                
                expression = "mtum_id = '%s'" % (mtum_id)
                request = QgsFeatureRequest ().setFilterExpression(expression)

                cam_feat = list(self.cam_lyr.getFeatures(request))[0]
                self.cam_h = QgsHighlight(self.map_canvas, cam_feat, self.cam_lyr)
                self.cam_h.setColor(self.highlight_color)
                self.cam_h.setFillColor(self.highlight_color)
                self.cam_h.show()
                    
                cam_hfov_feat = list(self.cam_hfov_lyr.getFeatures(request))[0]
                self.hfov_h = QgsHighlight(self.map_canvas, cam_hfov_feat, self.cam_hfov_lyr)
                self.hfov_h.setColor(self.highlight_color)
                self.hfov_h.setFillColor(self.highlight_color)
                self.hfov_h.show()
                
                self.img_line_lyr.setSubsetString(expression) #show only those lines which correspond to the currently selected image
                
                self.mono_tool.set_camera(self.active_camera)
                self.vertex_tool.set_camera(self.active_camera)
                
                self.dlg.btn_monotool.setEnabled(True)
                self.dlg.btn_select.setEnabled(True)
                # self.dlg.btn_delete.setEnabled(True)
                self.dlg.btn_vertex.setEnabled(True)
                
            if item.checkState(column) == Qt.Unchecked:
                item.setSelected(False)
                QgsProject.instance().removeMapLayer(self.curr_img_lyr.id())
                
                self.img_canvas.refresh()
                self.active_camera = None
                self.curr_img_lyr = None
                
                self.dlg.btn_monotool.setEnabled(False)
                self.dlg.btn_monotool.setChecked(False)
                self.deactivate_plotting()
                
                self.dlg.btn_select.setEnabled(False)
                self.dlg.btn_select.setChecked(False)
                
                self.dlg.btn_vertex.setEnabled(False)
                self.dlg.btn_vertex.setChecked(False)
                
                # self.dlg.btn_delete.setEnabled(False)
                            
                self.clear_highlighted_features()
                
                self.clear_meta_fiels()

                #use a filter which is not available to not show any lines in img canvas if no image is currently selected
                expression = "mtum_id = 'sth_not_existing'"
                self.img_line_lyr.setSubsetString(expression) #show only those lines which correspond to the currently selected image
                
    def run(self):
        """Run method that performs all the real work"""
        
        # QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(25832))
        # self.map_canvas.setDestinationCrs(QgsCoordinateReferenceSystem(25832))
        
        self.img_canvas.setMapTool(self.pan_tool)
        
        self.dlg.btn_pan.setChecked(True)
        self.dlg.show()