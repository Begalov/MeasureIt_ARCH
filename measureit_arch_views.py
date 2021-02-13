import bpy
import os

from bpy.props import (
    CollectionProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty
)
from bpy.types import PropertyGroup, Panel, Operator, UIList
from datetime import datetime

from .measureit_arch_render import render_main
from .measureit_arch_baseclass import TextField


PAPER_SIZES = (
    ('Custom',  (None,     None)),
    ('A0',      ('84.1cm', '118.9cm')),
    ('A1',      ('59.4cm', '84.1cm')),
    ('A2',      ('42cm',   '59.4cm')),
    ('A3',      ('29.7cm', '42cm')),
    ('A4',      ('21cm',   '29.7cm')),
    ('Letter',  ('8.5in',  '11in')),
    ('Legal',   ('8.5in',  '14in')),
    ('Tabloid', ('11in',   '17in')),
    ('Arch A',  ('9in',    '12in')),
    ('Arch B',  ('12in',   '18in')),
    ('Arch C',  ('18in',   '24in')),
    ('Arch D',  ('24in',   '36in')),
    ('Arch E',  ('36in',   '48in')),
    ('Arch E1', ('30in',   '42in')),
    ('Arch E2', ('26in',   '38in')),
    ('Arch E3', ('27in',   '39in')),
)


def scene_text_update_flag(self, context):
    scene = context.scene
    scene.MeasureItArchProps.text_updated = True
    update(self, context)


def update(self, context):
    if context is None:
        context = bpy.context
    scene = context.scene
    ViewGen = scene.ViewGenerator
    view = ViewGen.views[ViewGen.active_index]
    camera = view.camera.data
    if camera is not None:
        camera.type = view.cameraType

    if view.end_frame < view.start_frame:
        view.end_frame = view.start_frame
    scene.frame_end = view.end_frame
    scene.frame_start = view.start_frame
    # scene.frame_current = view.start_frame

    if view.res_type == 'res_type_paper':
        update_camera(scene, camera)
    else:
        update_camera_px(scene, camera)

    if view.view_layer != "":
        vl = context.scene.view_layers[view.view_layer]
        context.window.view_layer = vl

    render = scene.render
    if view.output_path is not "":
        filenameStr = view.name
        render.filepath = os.path.join(view.output_path, filenameStr)
        if view.date_folder:
            today = datetime.now()
            renderpath = bpy.path.abspath(view.output_path)
            datepath = os.path.join(renderpath, today.strftime('%Y%m%d'))
            if not os.path.exists(datepath):
                os.mkdir(renderpath + today.strftime('%Y%m%d'))
            render.filepath = os.path.join(datepath, filenameStr)


def update_paper_size(self, context):
    if self.paper_size == 'Custom':
        return

    for name, (width, height) in PAPER_SIZES:
        if name == self.paper_size:
            break

    if self.paper_orientation == 'LANDSCAPE':
        width, height = height, width

    unit_system = context.scene.unit_settings.system
    self.width = bpy.utils.units.to_value(unit_system, "LENGTH", width)
    self.height = bpy.utils.units.to_value(unit_system, "LENGTH", height)


def update_camera(scene, camera):
    render = scene.render
    ViewGen = scene.ViewGenerator
    view = ViewGen.views[ViewGen.active_index]
    width = view.width
    height = view.height
    modelScale = view.model_scale
    paperScale = view.paper_scale

    ppi = view.res

    render.resolution_percentage = 100
    render.resolution_x = width * ppi * 39.3701
    render.resolution_y = height * ppi * 39.3701

    if width > height:
        camera.ortho_scale = (
            render.resolution_x / ppi / 39.3701) * (modelScale / paperScale)
    else:
        camera.ortho_scale = (
            render.resolution_y / ppi / 39.3701) * (modelScale / paperScale)


def update_camera_px(scene, camera):
    render = scene.render
    ViewGen = scene.ViewGenerator
    view = ViewGen.views[ViewGen.active_index]
    width_px = view.width_px
    height_px = view.height_px
    modelScale = view.model_scale
    pixelScale = view.pixel_scale
    percentScale = view.percent_scale

    render.resolution_x = width_px
    render.resolution_y = height_px
    render.resolution_percentage = percentScale

    if width_px > height_px:
        camera.ortho_scale = (render.resolution_x) * (modelScale / (pixelScale * (percentScale / 100)))
    else:
        camera.ortho_scale = (render.resolution_y) * (modelScale / (pixelScale * (percentScale / 100)))


def change_scene_camera(self, context):
    scene = context.scene
    ViewGen = scene.ViewGenerator
    view = ViewGen.views[ViewGen.active_index]
    camera = view.camera
    update(self, context)
    if camera != None:
        scene.camera = camera
        scene.frame_current = view.start_frame
        scene_text_update_flag(self, context)


def camera_poll(self, object):
    return object.type == 'CAMERA'


class ViewProperties(PropertyGroup):

    textFields: CollectionProperty(type=TextField)

    camera: PointerProperty(
        type=bpy.types.Object,
        poll=camera_poll)

    cameraType: EnumProperty(
        items=[
            ('PERSP', 'Perspective', ''),
            ('ORTHO', 'Ortho', '')
        ],
        name="Camera Type",
        description="Camera Type",
        default='ORTHO',
        update=update)

    width: FloatProperty(
        name="Width",
        description="Camera Width in Units",
        unit='LENGTH',
        default=0.43,
        min=0.0,
        update=update)

    height: FloatProperty(
        name="Height",
        description="Camera Height in Units",
        unit='LENGTH',
        default=0.28,
        min=0.0,
        update=update)

    # Width_px Property
    width_px: IntProperty(
        name="X",
        description="Camera Width in Pixels",
        subtype='PIXEL',
        default=1920,
        min=4,
        update=update,
        step=100)

    # Width_px Property
    height_px: IntProperty(
        name="Y",
        description="Camera Height in Pixels",
        subtype='PIXEL',
        default=1080,
        min=4,
        update=update,
        step=100)

    # Percent Scale Property
    percent_scale: IntProperty(
        name="Percent Scale",
        description="Percentage scale for render resolution",
        subtype='PERCENTAGE',
        default=50,
        min=1,
        max=100,
        update=update,
        step=100)

    # PPI Property
    res: IntProperty(
        name="res_prop",
        description="Resolution in Pixels Per Inch",
        subtype='FACTOR',
        default=150,
        min=1,
        soft_max=600,
        soft_min=50,
        update=scene_text_update_flag,
        step=1)

    # Model Length
    model_scale: IntProperty(
        name="model_scale",
        description="Unit on Model",
        default=25,
        min=1,
        update=update)

    # Paper Length
    paper_scale: IntProperty(
        name="paper_scale",
        description="Length on Paper",
        default=1, min=1,
        update=update
    )

    # Pixel Length
    pixel_scale: IntProperty(
        name="Pixel Scale",
        subtype='PIXEL',
        default=10000,
        min=1,
        update=update
    )

    # Resolution Type
    res_type: EnumProperty(
        items=[
            ('res_type_paper', 'Paper',
             'Define Resolution by Paper Size and Pixels Per Inch'),
            ('res_type_pixels', 'Pixels',
             'Blender Standard, Define Resolution in Pixels')
        ],
        name="Resolution Type",
        description='Method For Defining Render Size',
        default='res_type_paper',
        update=update)

    paper_size: EnumProperty(
        items=map(lambda o: (o[0], o[0], ''), PAPER_SIZES),
        name="Paper size",
        description="Paper size used for rendering",
        default='Custom',
        update=update_paper_size)

    paper_orientation: EnumProperty(
        items=(
            ('PORTRAIT', 'Portrait', ''),
            ('LANDSCAPE', 'Landscape', ''),
        ),
        name="Paper orientation",
        description="Paper orientation used for rendering",
        default='PORTRAIT',
        update=update_paper_size)

    date_folder: BoolProperty(
        name="Date Folder",
        description="Adds a Folder with todays date to the end of the output path",
        default=False)

    output_path: StringProperty(
        name="Output Path",
        description="Render Output Path for this View",
        subtype='FILE_PATH',
        default="",
        update=update)

    view_layer: StringProperty(
        name="View Layer",
        description="View Layer to use with this view",
        default="",
        update=update)

    titleBlock: StringProperty(
        name="Title Block",
        description="TitleBlock to use with this view layer",
        default="",
        update=update)

    start_frame: IntProperty(
        name="Start Frame",
        default=1,
        update=update)

    end_frame: IntProperty(
        name="End Frame",
        default=1,
        update=update)



class ViewContainer(PropertyGroup):
    active_index: IntProperty(
        name='Active View Index', min=0, max=1000, default=0,
        description='Index of the current View',
        update=change_scene_camera)

    show_settings: BoolProperty(name='Show View Settings', default=False)
    show_text_fields: BoolProperty(name='Show Text Fields', default=False)

    # Array of views
    views: CollectionProperty(type=ViewProperties)



class DeleteViewButton(Operator):
    bl_idname = "measureit_arch.deleteviewbutton"
    bl_label = "Delete View"
    bl_description = "Delete a View"
    bl_category = 'MeasureitArch'
    bl_options = {'REGISTER'}
    tag: IntProperty()

    def execute(self, context):
        # Add properties

        Generator = context.scene.ViewGenerator
        Generator.views.remove(Generator.active_index)

        return {'FINISHED'}


class DuplicateViewButton(Operator):
    bl_idname = "measureit_arch.duplicateviewbutton"
    bl_label = "Delete View"
    bl_description = "Delete a View"
    bl_category = 'MeasureitArch'
    bl_options = {'REGISTER'}
    tag: IntProperty()

    @classmethod
    def poll(cls, context):
        Generator = context.scene.ViewGenerator
        try:
            Generator.views[Generator.active_index]
        except:
            return False
        return True

    def execute(self, context):
        # Add properties

        Generator = context.scene.ViewGenerator
        ActiveView = Generator.views[Generator.active_index]
        newView = Generator.views.add()
        newView.name = ActiveView.name + ' copy'

        # Get props to loop through
        for key in Generator.views[Generator.active_index].__annotations__.keys():
            try:
                newView[key] = ActiveView[key]
            except:
                pass

        return {'FINISHED'}


class M_ARCH_UL_Views_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        scene = bpy.context.scene

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            view = item
            layout.use_property_decorate = False
            row = layout.row(align=True)
            subrow = row.row()
            subrow.prop(view, "name", text="", emboss=False)
            row.prop(view, 'camera', text="", icon='CAMERA_DATA')

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MESH_CUBE')


class SCENE_PT_Views(Panel):
    """ A panel in the Object properties window """
    bl_parent_id = 'SCENE_PT_Panel'
    bl_label = "Views"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw_header(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="", icon='DOCUMENTS')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        ViewGen = scene.ViewGenerator

        row = layout.row()

        # Draw The UI List
        row.template_list("M_ARCH_UL_Views_list", "", ViewGen,
                          "views", ViewGen, "active_index", rows=2, type='DEFAULT')

        # Operators Next to List
        col = row.column(align=True)
        col.operator("measureit_arch.addviewbutton", icon='ADD', text="")
        op = col.operator("measureit_arch.deleteviewbutton", text="", icon="X")
        op.tag = ViewGen.active_index  # saves internal data

        col.separator()
        col.menu("SCENE_MT_Views_menu", icon='DOWNARROW_HLT', text="")


        if len(ViewGen.views) > 0 and ViewGen.active_index < len(ViewGen.views):
            view = ViewGen.views[ViewGen.active_index]

            # Settings Below List
            if ViewGen.show_settings:
                settingsIcon = 'DISCLOSURE_TRI_DOWN'
            else:
                settingsIcon = 'DISCLOSURE_TRI_RIGHT'

            box = layout.box()
            col = box.column()
            row = col.row()
            row.prop(ViewGen, 'show_settings', text="",
                     icon=settingsIcon, emboss=False)

            row.label(text=view.name + ' Settings:')

            if ViewGen.show_settings:
                col = box.column()
                if view.camera is not None:
                    col.prop(view, "cameraType", text="Camera Type")
                    col.prop_search(view, 'view_layer', context.scene,
                                    'view_layers', text='View Layer')
                    col.prop_search(view, 'titleBlock', bpy.data,
                                    'scenes', text='Title Block')
                    col.prop(view, "output_path")
                    col.prop(view, "date_folder", text="Date Folder")

                    col.row().prop(view, 'res_type', expand=True)

                    if view.res_type == 'res_type_paper':

                        col = box.column(align=True)
                        split = box.split(factor=0.4)
                        col = split.column()
                        col.alignment = 'RIGHT'
                        row = split.row(align=True)

                        col = box.column(align=True)
                        col.enabled = True
                        col.prop(view, 'paper_size', text='Paper size:')

                        if view.paper_size == 'Custom':
                            col = box.column(align=True)
                            col.enabled = False
                            col.row().prop(view, 'paper_orientation', expand=True)
                            col = box.column(align=True)
                            col.enabled = True
                        else:
                            col = box.column(align=True)
                            col.enabled = True
                            col.row().prop(view, 'paper_orientation', expand=True)
                            col = box.column(align=True)
                            col.enabled = False


                        col.prop(view, 'width', text='Width:')
                        col.prop(view, 'height', text='Height:')
                        #col.prop(view, 'paper_orientation', text='Paper orientation:')
                        col = box.column(align=True)
                        col.enabled = True
                        col.prop(view, 'res', text='Resolution (PPI):')

                    else:
                        col = box.column(align=True)
                        split = box.split(factor=0.4)
                        col = split.column()
                        col.alignment = 'RIGHT'
                        row = split.row(align=True)

                        # row.menu(CAMERA_PX_Presets.__name__, text=CAMERA_PX_Presets.bl_label)
                        # row.operator(AddPixelResPreset.bl_idname, text="", icon='ADD')
                        # row.operator(AddPixelResPreset.bl_idname, text="", icon='REMOVE').remove_active = True

                        col = box.column(align=True)
                        col.prop(view, 'width_px', text="Resolution X")
                        col.prop(view, 'height_px')
                        col.prop(view, 'percent_scale', text="%")

                    # Scale Settings
                    col = box.column(align=True)
                    col.active = view.camera.data.type == 'ORTHO'
                    if view.res_type == 'res_type_paper':
                        # row = col.row(align=True)
                        # row.menu(CAMERA_PAPER_SCALE_Presets.__name__, text=CAMERA_PAPER_SCALE_Presets.bl_label)
                        # row.operator(AddPaperScalePreset.bl_idname, text="", icon='ADD')
                        # row.operator(AddPaperScalePreset.bl_idname, text="", icon='REMOVE').remove_active = True

                        row = col.row(align=True)
                        row.prop(view, 'paper_scale', text="Scale")
                        row.prop(view, 'model_scale', text=":")

                    else:

                        # row = col.row(align=True)
                        # row.menu(CAMERA_PX_SCALE_Presets.__name__, text=CAMERA_PX_SCALE_Presets.bl_label)
                        # row.operator(AddPixelScalePreset.bl_idname, text="", icon='ADD')
                        # row.operator(AddPixelScalePreset.bl_idname, text="", icon='REMOVE').remove_active = True

                        row = col.row(align=True)
                        row.prop(view, 'pixel_scale', text="Scale")
                        row.prop(view, 'model_scale', text=":")

                    # A quick Test, If BlenderBIM is available, add its view specific properties here too
                    # try:
                    #    col = box.column(align=True)
                    #    col.prop(camera.BIMCameraProperties,'diagram_scale', text= 'BlenderBIM Scale')
                    #    col.operator('bim.cut_section')
                    # except:
                    #    pass

                    col = box.column(align=True)
                    row = col.row(align=True)
                    row.prop(view, 'start_frame', text="Frame Range")
                    row.prop(view, 'end_frame', text="")


            # Notes below Settings
            if ViewGen.show_text_fields:
                fieldsIcon = 'DISCLOSURE_TRI_DOWN'
            else:
                fieldsIcon = 'DISCLOSURE_TRI_RIGHT'

            box = layout.box()
            col = box.column()
            row = col.row(align=True)
            row.prop(ViewGen, 'show_text_fields',
                        text="", icon=fieldsIcon, emboss=False)
            row.label(text=view.name + ' Notes:')

            row.emboss = 'PULLDOWN_MENU'
            txtAddOp = row.operator(
                "measureit_arch.addtextfield", text="", icon="ADD")
            txtAddOp.propPath = 'bpy.context.scene.ViewGenerator.views[bpy.context.scene.ViewGenerator.active_index].textFields'
            txtAddOp.idx = ViewGen.active_index
            txtAddOp.add = True

            txtRemoveOp = row.operator(
                "measureit_arch.addtextfield", text="", icon="REMOVE")
            txtRemoveOp.propPath = 'bpy.context.scene.ViewGenerator.views[bpy.context.scene.ViewGenerator.active_index].textFields'
            txtRemoveOp.idx = ViewGen.active_index
            txtRemoveOp.add = False

            if ViewGen.show_text_fields:

                col = box.column(align=True)
                idx = 0
                for textField in view.textFields:
                    col = box.column(align=True)

                    row = col.row(align=True)

                    split = row.split(factor=0.2)
                    split.label(text='Text Field ' + str(idx + 1))

                    row = split.row(align=True)
                    row.prop(textField, 'autoFillText',
                                text="", icon="FILE_TEXT")

                    if textField.autoFillText:
                        row.prop(textField, 'textSource', text="")
                    else:
                        row.prop(textField, 'text', text="")

                    if textField.textSource == 'RNAPROP' and textField.autoFillText:
                        row.prop(textField, 'rnaProp', text="")

                    row.emboss = 'PULLDOWN_MENU'
                    op = row.operator(
                        'measureit_arch.moveitem', text="", icon='TRIA_DOWN')
                    op.propPath = 'bpy.context.scene.ViewGenerator.views[bpy.context.scene.ViewGenerator.active_index].textFields'
                    op.upDown = False
                    op.idx = idx

                    op = row.operator(
                        'measureit_arch.moveitem', text="", icon='TRIA_UP')
                    op.propPath = 'bpy.context.scene.ViewGenerator.views[bpy.context.scene.ViewGenerator.active_index].textFields'
                    op.upDown = True
                    op.idx = idx
                    idx += 1



class SCENE_MT_Views_menu(bpy.types.Menu):
    bl_label = "Custom Menu"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        op = layout.operator('measureit_arch.duplicateviewbutton',
                             text="Duplicate Selected View", icon='DUPLICATE')


class AddViewButton(Operator):
    bl_idname = "measureit_arch.addviewbutton"
    bl_label = "Add"
    bl_description = "Create A New View"
    bl_category = 'MeasureitArch'

    def execute(self, context):
        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    # Add properties

                    scene = context.scene
                    ViewGen = scene.ViewGenerator

                    newView = ViewGen.views.add()
                    newView.name = 'View ' + str(len(ViewGen.views))

                    context.area.tag_redraw()
                    return {'FINISHED'}
        return {'FINISHED'}


class M_ARCH_OP_Render_Preview(Operator):
    bl_idname = "measureit_arch.renderpreviewbutton"
    bl_label = "Render Preview"
    bl_description = "Create A Preview Render of this view to be used in sheet layouts.\n" \
                     "The Results can also be accessed in the Image Editor"
    bl_category = 'MeasureitArch'
    tag: IntProperty()

    def execute(self, context):
        scene = context.scene
        ViewGen = scene.ViewGenerator
        view = ViewGen.views[ViewGen.active_index]

        msg = "New image created with measures. Open it in UV/image editor"
        camera_msg = "Unable to render. No camera found"

        # Check camera
        if scene.camera is None:
            self.report({'ERROR'}, camera_msg)
            return {'FINISHED'}

        # Use default render
        print("MeasureIt_ARCH: Rendering image")
        # bpy.ops.render.render()
        render_results = render_main(self, context)
        if render_results[0]:
            self.report({'INFO'}, msg)
            if 'preview' in view:
                del view['preview']
            view['preview'] = render_results[1]
        del render_results

        return {'FINISHED'}
