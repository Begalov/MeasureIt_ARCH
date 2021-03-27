import bpy

from bpy.props import (
    CollectionProperty,
    FloatVectorProperty,
    IntProperty,
    BoolProperty,
    FloatProperty,
    PointerProperty)

from bpy.types import PropertyGroup, Panel, Operator, UIList, Collection


class HatchProperties(PropertyGroup):

    visible: BoolProperty(
        name="Visibility",
        description="how/hide",
        default=False)

    pattern: PointerProperty(name='Hatch Pattern', type=Collection)

    patternWeight: FloatProperty(
        name="Pattern Weight",
        description="Lineweight",
        default=1,
        soft_min=1.0,
        step=25,
        min=0)

    patternSize: FloatProperty(
        name="Pattern Size",
        description="Lineweight",
        default=1,
        soft_min=1.0,
        step=25,
        min=0)

    patternRot: FloatProperty(
        name="Pattern Rotation",
        description="Rotation",
        default=0,
        soft_min=0,
        step=25,
        subtype='ANGLE')

    patternOpacity: FloatProperty(
        name="Pattern Opacity",
        description="Pattern Opacity",
        default=1.0,
        min=0.0,
        max=1.0,
        step=1,)

    fill_color: FloatVectorProperty(
        name="Color",
        description="Color for the Item",
        default=(0.0, 0.0, 0.0, 1.0),
        min=0,
        max=1,
        subtype='COLOR',
        size=4,)

    line_color: FloatVectorProperty(
        name="Color",
        description="Color for the Item",
        default=(0.0, 0.0, 0.0, 1.0),
        min=0,
        max=1,
        subtype='COLOR',
        size=4,)

    lineWeight: FloatProperty(
        name="Line Weight",
        description="Lineweight",
        default=1,
        soft_min=1.0,
        step=25,
        min=0)

class MATERIAL_PT_UIHatch(Panel):
    """ A Panel in the Material properties window """
    #bl_parent_id = 'MATERIAL_PT_Panel'
    bl_label = "Hatch"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"


    def draw_header(self, context):
        layout = self.layout
        row = layout.row()
        hatch = context.material.Hatch
        row.prop(hatch, "visible", text="",)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        hatch = context.material.Hatch
        main_col = layout.column()
        col = main_col.column()

        main_col.enabled = hatch.visible
        col = main_col.column()
        col.prop(hatch, 'fill_color', text="Fill Color",)
        col.prop(hatch, 'line_color', text="Line Color",)
        col.prop(hatch, 'lineWeight', text="Line Weight",)
        col = main_col.column()
        col.prop(hatch, 'pattern', text="Pattern",)
        col.prop(hatch, 'patternWeight', text="Pattern Weight",)
        col.prop(hatch, 'patternSize', text="Pattern Size",)
        col.prop(hatch, 'patternRot', text="Pattern Rotation",)
        col.prop(hatch, 'patternOpacity', text="Pattern Opacity",)

