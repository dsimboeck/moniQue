from vispy.scene import SceneCanvas
from vispy.color import Color
from vispy.scene import XYZAxis
from vispy.scene.cameras import TurntableCamera
from vispy.scene.visuals import Markers, Box, Mesh
from vispy.visuals import transforms
from PyQt5.QtWidgets import QDialog, QVBoxLayout
import numpy as np

class Scene3D(QDialog):
    def __init__(self):
        super(Scene3D, self).__init__()
        # setting window title
        self.setWindowTitle("3D viewer")
        
        lay = QVBoxLayout()
        
        self.canvas_wrapper = CanvasWrapper()
        lay.addWidget(self.canvas_wrapper.canvas.native)
        
class CanvasWrapper:
    def __init__(self):
        self.canvas = SceneCanvas(keys='interactive', 
                                  bgcolor='white',
                                  size=(800, 600),
                                  show=True,
                                  create_native=True)
        
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'
        # self.view.camera.parent = self.view.scene
        # self.view.camera.center = (5, 0, 0)
        # self.view.camera.elevation = 90
        # self.view.camera.azimuth = 0
        # self.view.camera.distance = 5

        # z_marker = Markers(pos=np.array([[5, 0, 0.5]]), face_color=Color("#0063D2"))
        # self.view.add(z_marker)

        # x_marker = Markers(pos=np.array([[5.5, 0, 0]]), face_color=Color("#FF2929"))
        # self.view.add(x_marker)

        # y_marker = Markers(pos=np.array([[5, 0.5, 0]]), face_color=Color("#00A302"))
        # self.view.add(y_marker)

        # axis = XYZAxis()
        # axis_transform = transforms.MatrixTransform()
        # axis_transform.translate((5, 0, 0))
        # axis.transform = axis_transform
        # self.view.add(axis)

        # color = Color("#E8E8E8")
        # cube = Box(1, 1, 1, color=color, edge_color="black",
        #                         parent=self.view.scene)
        # cube_transform = transforms.MatrixTransform()
        # cube_transform.translate((5, 0, 0))
        # cube.transform = cube_transform
        # self.view.add(cube)

        self.canvas.events.mouse_press.connect(self.on_mouse_press)

    def add_mesh(self, faces, verts):
        
        verts = verts - np.min(verts, axis=0)
        
        self.view.camera.center = np.mean(verts, axis=0)
        
        mesh = Mesh(verts, faces, shading="smooth", color="white")
        self.view.add(mesh)
        self.view.scene.update()
        
    # @self.canvas.events.mouse_press.connect
    def on_mouse_press(self, event):
        if event.button == 1:
            
            mouse_x = event.pos[0]
            mouse_y = event.pos[1]
            
            self.view.camera.set_state({"elevation":90})
            
            print(mouse_x, mouse_y)