# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


# ----------------------------------------------------------
# File: measureit_arch_annotations.py
# Main panel for different MeasureitArch general actions
# Author:  Kevan Cress
#
# ----------------------------------------------------------
import bpy
import blf
import bgl
import gpu

from bpy.types import PropertyGroup, Panel, Object, Operator, SpaceView3D, Scene

from bpy.props import (
        CollectionProperty,
        FloatVectorProperty,
        IntProperty,
        BoolProperty,
        StringProperty,
        FloatProperty,
        EnumProperty,
        PointerProperty
        )


from .measureit_arch_baseclass import BaseProp, BaseWithText
from .measureit_arch_main import get_smart_selected, get_selected_vertex

import math


def update_custom_props(self,context):
    ignoredProps = ['AnnotationGenerator','MeasureGenerator','LineGenerator','_RNA_UI','cycles','cycles_visibility']
    annotationGen = context.object.AnnotationGenerator[0]
    idx = 0 
    for key in context.object.keys():
        if key not in ignoredProps:
            if key not in annotationGen.customProperties:
                annotationGen.customProperties.add().name = key
    for prop in annotationGen.customProperties:
        if prop.name not in context.object.keys():
            annotationGen.customProperties.remove(idx)
        idx += 1


class CustomProperties(PropertyGroup):
    name: StringProperty(name='Custom Properties')

bpy.utils.register_class(CustomProperties)


class AnnotationProperties(BaseWithText,PropertyGroup):
    annotationRotation:FloatVectorProperty(name='annotationOffset',
                            description='Rotation for Annotation',
                            default= (0.0,0.0,0.0),
                            subtype= 'EULER')

    annotationOffset: FloatVectorProperty(name='annotationOffset',
                            description='Offset for Annotation',
                            default= (1.0,1.0,1.0),
                            subtype= 'TRANSLATION')
    
    annotationTextSource: StringProperty(name='annotationTextSource',
                            description="Text Source",
                            update=update_custom_props)

    annotationAnchor: IntProperty(name="annotationAnchor",
                            description="Index of Vertex that the annotation is Anchored to")
    
    
# Register
bpy.utils.register_class(AnnotationProperties)



# ------------------------------------------------------------------
# Define object class (container of annotations)
# MeasureitArch
# ------------------------------------------------------------------
class AnnotationContainer(PropertyGroup):
    num_annotations: IntProperty(name='Number of Annotations', min=0, max=1000, default=0,
                                description='Number total of Annotations')
    # Array of segments
    annotations: CollectionProperty(type=AnnotationProperties)
    customProperties: CollectionProperty(type=CustomProperties)

bpy.utils.register_class(AnnotationContainer)
Object.AnnotationGenerator = CollectionProperty(type=AnnotationContainer)

class AddAnnotationButton(Operator):
    bl_idname = "measureit_arch.addannotationbutton"
    bl_label = "Add"
    bl_description = "(EDITMODE only) Add a new measure label (select 1 vertex)"
    bl_category = 'MeasureitArch'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            mainobject = context.object
            mylist = get_selected_vertex(mainobject)
            if len(mylist) == 1:
                if 'AnnotationGenerator' not in mainobject:
                    mainobject.AnnotationGenerator.add()
                
                annotationGen = mainobject.AnnotationGenerator[0] 
                annotationGen.num_annotations +=1
                newAnnotation = annotationGen.annotations.add()

                # Set values
                newAnnotation.text = ("Annotation " + str(annotationGen.num_annotations))

                tex_buffer = bgl.Buffer(bgl.GL_INT, 1)
                bgl.glGenTextures(1, tex_buffer)
                newAnnotation['tex_buffer'] = tex_buffer.to_list()

                newAnnotation.annotationAnchor = mylist[0]
                newAnnotation.annotationLineWeight = (2)
                newAnnotation.color = (0,0,0,1)
                context.area.tag_redraw()  
                update_custom_props(newAnnotation,context)
                
                
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt-ARCH: Select one vertex for creating measure label")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},   
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


class MeasureitArchAnnotationsPanel(Panel):
    bl_idname = "annotations"
    bl_label = "Annotations"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        if 'AnnotationGenerator' in bpy.context.object:
            return True
        else:
            return False


    def draw(self, context):
         if context.object is not None:
            if 'AnnotationGenerator' in context.object:
                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False
                # -----------------
                # loop
                # -----------------
                
                annotationGen = context.object.AnnotationGenerator[0]
                if annotationGen.num_annotations> 0:
                    #row = layout.row(align = True)
                    #row.operator("measureit_arch.expandallsegmentbutton", text="Expand all", icon="ADD")
                    #row.operator("measureit_arch.collapseallsegmentbutton", text="Collapse all", icon="REMOVE")
                    for idx in range(0, annotationGen.num_annotations):
                        add_annotation_item(layout, idx, annotationGen.annotations[idx],annotationGen)

                    #row = layout.row()
                    #row.operator("measureit_arch.deleteallsegmentbutton", text="Delete all", icon="X")
    
# -----------------------------------------------------
# Add annotation options to the panel.
# -----------------------------------------------------
def add_annotation_item(layout, idx, annotation, annotationGen):
    if annotation.settings is True:
        box = layout.box()
        row = box.row(align=True)
    else:
        row = layout.row(align=True)

    row.prop(annotation, 'visible', text="", toggle=True, icon='FONT_DATA')
    row.prop(annotation, 'settings', text="",toggle=True, icon='PREFERENCES')
    row.prop(annotation, 'color', text="" )
    row.prop(annotation, 'text', text="")
    op = row.operator("measureit_arch.deleteannotationbutton", text="", icon="X")
    op.tag = idx  # saves internal data
    
    if annotation.settings is True:
        
        col = box.column()
        col.template_ID(annotation, "font", open="font.open", unlink="font.unlink")
        col = box.column()
        col.prop_search(annotation,'annotationTextSource', annotationGen ,'customProperties',text="Text Source")
        col.prop(annotation, 'lineWeight', text="Line Weight" )
        col.prop(annotation, 'textResolution', text="Resolution")
        col.prop(annotation, 'fontSize', text="Size")
        col.prop(annotation, 'annotationOffset', text='Offset')
        col.prop(annotation, 'annotationRotation', text='Rotation')
        col.prop(annotation, 'textAlignment', text='Alignment')
        col.prop(annotation, 'textPosition', text='Position')

class DeleteAnnotationButton(Operator):

    bl_idname = "measureit_arch.deleteannotationbutton"
    bl_label = "Delete Line"
    bl_description = "Delete an Annotation"
    bl_category = 'MeasureitArch'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        # Add properties
        mainObj = context.object
        annotationGen = mainObj.AnnotationGenerator[0]
        annotation = annotationGen.annotations[self.tag]
        annotation.lineFree = True
        # Delete element
        annotationGen.annotations.remove(self.tag)
        annotationGen.num_annotations -= 1
        # redraw
        context.area.tag_redraw()

        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    context.area.tag_redraw()
                    return {'FINISHED'}
                
        return {'FINISHED'}


