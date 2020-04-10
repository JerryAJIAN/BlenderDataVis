bl_info = {
    'name': 'Data Vis',
    'author': 'Zdenek Dolezal',
    'description': '',
    'blender': (2, 80, 0),
    'version': (1, 1, 0),
    'location': 'Object -> Add Mesh',
    'warning': '',
    'category': 'Generic'
}

import bpy
import bpy.utils.previews
import os
import subprocess
import sys

from .operators.data_load import FILE_OT_DVLoadFile
from .operators.bar_chart import OBJECT_OT_BarChart
from .operators.line_chart import OBJECT_OT_LineChart
from .operators.pie_chart import OBJECT_OT_PieChart
from .operators.point_chart import OBJECT_OT_PointChart
from .operators.surface_chart import OBJECT_OT_SurfaceChart
from .general import DV_LabelPropertyGroup, DV_ColorPropertyGroup, DV_AxisPropertyGroup
from .data_manager import DataManager


class DV_Preferences(bpy.types.AddonPreferences):
    '''Preferences for data visualisation addon'''
    bl_idname = 'data_vis'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.scale_y = 2.0
        try:
            import scipy
            import numpy
            row.label(text='Dependencies already installed...')
        except ImportError:
            row.operator('object.install_modules')
            row = layout.row()
            version = '{}.{}'.format(bpy.app.version[0], bpy.app.version[1])
            row.label(text='Or use pip to install scipy into python which Blender uses!')
            row = layout.row()
            row.label(text='Blender has to be restarted after this process!')


class OBJECT_OT_InstallModules(bpy.types.Operator):
    '''Operator that tries to install scipy and numpy using pip into blender python'''
    bl_label = 'Install addon dependencies'
    bl_idname = 'object.install_modules'
    bl_options = {'REGISTER'}

    def execute(self, context):
        version = '{}.{}'.format(bpy.app.version[0], bpy.app.version[1])

        python_path = os.path.join(os.getcwd(), version, 'python', 'bin', 'python')
        try:
            self.install(python_path)
        except Exception as e:
            self.report({'ERROR'}, 'Error ocurred, try to install dependencies manually. \n Exception: {}'.format(str(e)))
        return {'FINISHED'}

    def install(self, python_path):
        import platform

        info = ''
        bp_pip = -1
        bp_res = -1

        p_pip = -1
        p_res = -1

        p3_pip = -1
        p3_res = -1
        try:
            bp_pip = subprocess.check_call([python_path, '-m', 'ensurepip', '--user'])
            bp_res = subprocess.check_call([python_path, '-m', 'pip', 'install', '--user', 'scipy'])
        except OSError as e:
            info = 'Python in blender folder failed: ' + str(e) + '\n'

        if bp_pip != 0 or bp_res != 0:
            if platform.system() == 'Linux':
                try:
                    p_pip = subprocess.check_call(['python', '-m', 'ensurepip', '--user'])
                    p_res = subprocess.check_call(['python', '-m', 'pip', 'install', '--user', 'scipy'])
                except OSError as e:
                    info += 'Python in PATH failed: ' + str(e) + '\n'

                if p_pip != 0 or p_res != 0:  
                    try:
                        # python3
                        p3_pip = subprocess.check_call(['python3', '-m', 'ensurepip', '--user'])
                        p3_res = subprocess.check_call(['python3', '-m', 'pip', 'install', '--user', 'scipy'])
                    except OSError as e:
                        info += 'Python3 in PATH failed: ' + str(e) + '\n'

        # if one approach worked
        if (bp_pip == 0 and bp_res == 0) or (p_pip == 0 and p_res == 0) or (p3_pip == 0 and p3_res == 0):
            self.report({'INFO'}, 'Scipy module should be succesfully installed, restart Blender now please! (Best effort approach)')
        else:
            raise Exception('Failed to install pip or scipy into blender python:\n' + str(info))


class DV_AddonPanel(bpy.types.Panel):
    '''
    Menu panel used for loading data and managing addon settings
    '''
    bl_label = 'DataVis'
    bl_idname = 'OBJECT_PT_dv'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DataVis'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('ui.dv_load_data')

        box = layout.box()
        box.label(icon='WORLD_DATA', text='Data Information:')
        box.label(text='File: ' + str(data_manager.get_filename()))
        box.label(text='Dims: ' + str(data_manager.dimensions))
        box.label(text='Labels: ' + str(data_manager.has_labels))
        box.label(text='Type: ' + str(data_manager.predicted_data_type))


class OBJECT_OT_AddChart(bpy.types.Menu):
    '''
    Menu panel grouping chart related operators in Blender AddObject panel
    '''
    bl_idname = 'OBJECT_MT_Add_Chart'
    bl_label = 'Chart'

    def draw(self, context):
        layout = self.layout
        main_icons = preview_collections['main']
        layout.operator(OBJECT_OT_BarChart.bl_idname, icon_value=main_icons['bar_chart'].icon_id)
        layout.operator(OBJECT_OT_LineChart.bl_idname, icon_value=main_icons['line_chart'].icon_id)
        layout.operator(OBJECT_OT_PieChart.bl_idname, icon_value=main_icons['pie_chart'].icon_id)
        layout.operator(OBJECT_OT_PointChart.bl_idname, icon_value=main_icons['point_chart'].icon_id)
        layout.operator(OBJECT_OT_SurfaceChart.bl_idname, icon_value=main_icons['surface_chart'].icon_id)


preview_collections = {}
data_manager = DataManager()


def chart_ops(self, context):
    icon = preview_collections['main']['addon_icon']
    self.layout.menu(OBJECT_OT_AddChart.bl_idname, icon_value=icon.icon_id)


def load_icons():
    pcoll = bpy.utils.previews.new()

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    for icon in os.listdir(icons_dir):
        name, ext = icon.split('.')
        if ext == 'png':
            pcoll.load(name, os.path.join(icons_dir, icon), 'IMAGE')

    preview_collections['main'] = pcoll


def remove_icons():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


classes = [
    DV_Preferences,
    OBJECT_OT_InstallModules,
    DV_LabelPropertyGroup,
    DV_ColorPropertyGroup,
    DV_AxisPropertyGroup,
    OBJECT_OT_AddChart,
    OBJECT_OT_BarChart,
    OBJECT_OT_PieChart,
    OBJECT_OT_PointChart,
    OBJECT_OT_LineChart,
    OBJECT_OT_SurfaceChart,
    FILE_OT_DVLoadFile,
    DV_AddonPanel,
]


def reload():
    unregister()
    register()


def register():
    load_icons()
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_add.append(chart_ops)


def unregister():
    remove_icons()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    bpy.types.VIEW3D_MT_add.remove(chart_ops)


if __name__ == '__main__':
    register()
