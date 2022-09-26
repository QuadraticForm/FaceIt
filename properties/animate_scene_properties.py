

import bpy
from bpy.props import (BoolProperty, CollectionProperty, IntProperty,
                       StringProperty, EnumProperty)
from bpy.types import PropertyGroup, Scene

from ..core import faceit_utils as futils
from ..core import shape_key_utils

# --------------- CLASSES --------------------
# | - Property Groups (Collection-/PointerProperty)
# ----------------------------------------------

PROCEDURAL_EXPRESSION_ITEMS = (
    ('NONE', 'None', 'Not a procedural expression'),
    ('EYEBLINKS', 'EyeBlinks', 'Eye blink expressions (can affect L R or N)'),
    ('MOUTHCLOSE', 'MouthClose', 'Jaw open, mouth closed')
)


class Anim_Properties(PropertyGroup):
    '''Properties stored in each expression item'''
    name: StringProperty(
        options=set(),
    )
    side: StringProperty(
        options=set(),
    )
    frame: IntProperty(
        options=set(),
    )
    index: IntProperty(
        options=set(),
    )
    mirror_name: StringProperty(
        options=set(),
    )
    corr_shape_key: BoolProperty(
        name='Shape Key',
        description='Corrective Shape Key active on this expression',
        default=False
    )
    procedural: EnumProperty(
        name='Procedural Expression',
        items=PROCEDURAL_EXPRESSION_ITEMS,
    )


# --------------- FUNCTIONS --------------------
# | - Update/Getter/Setter
# ----------------------------------------------


def update_expression_list_index(self, context):
    scene = self

    if scene.faceit_expression_list:

        new_expression = scene.faceit_expression_list[scene.faceit_expression_list_index]

        rig = futils.get_faceit_armature()
        if rig:
            actions_disabled = rig.hide_viewport is True or scene.faceit_shapes_generated
        else:
            actions_disabled = scene.faceit_shapes_generated

        if actions_disabled:
            if scene.faceit_sync_shapes_index:
                if new_expression:
                    bpy.ops.faceit.set_active_shape_key_index(
                        'EXEC_DEFAULT', shape_name=new_expression.name, get_active_target_shapes=False)
        else:
            use_mirror = new_expression.mirror_name == ''

            scene.frame_current = new_expression.frame

            if rig and scene.faceit_use_auto_mirror_x:
                rig.pose.use_mirror_x = use_mirror
            if context.scene.faceit_try_mirror_corrective_shapes:
                for obj in futils.get_faceit_objects_list():
                    obj.data.use_mirror_x = use_mirror

            # Get corrective shape on new index
            if scene.faceit_use_corrective_shapes and new_expression.corr_shape_key:
                corr_sk_name = 'faceit_cc_' + new_expression.name
                for obj in futils.get_faceit_objects_list():
                    if shape_key_utils.has_shape_keys(obj):
                        shape_keys = obj.data.shape_keys.key_blocks
                        if corr_sk_name in shape_keys:
                            obj.active_shape_key_index = shape_keys.find(corr_sk_name)


def update_corrective_shape_key_values(self, context):
    '''Update function for '''
    use_corr = self.faceit_use_corrective_shapes
    faceit_objects = futils.get_faceit_objects_list()
    for obj in faceit_objects:
        if shape_key_utils.has_shape_keys(obj):
            for sk in obj.data.shape_keys.key_blocks:
                if sk.name.startswith('faceit_cc_'):
                    sk.mute = not use_corr


def update_auto_mirror_x(self, context):
    rig = futils.get_faceit_armature()
    expression = self.faceit_expression_list[self.faceit_expression_list_index]
    use_mirror = expression.mirror_name == ''
    name = expression.name
    if rig is not None:
        rig.pose.use_mirror_x = use_mirror

    if expression.corr_shape_key and context.scene.faceit_try_mirror_corrective_shapes:
        for obj in futils.get_faceit_objects_list():
            obj.data.use_mirror_x = use_mirror


# --------------- REGISTER/UNREGISTER --------------------
# |
# --------------------------------------------------------


def register():

    Scene.faceit_expression_list_index = IntProperty(
        default=0,
        update=update_expression_list_index,
        options=set(),
    )

    Scene.faceit_expression_list = CollectionProperty(
        name='animation property collection',
        description='holds all expressions',
        type=Anim_Properties,
        options=set(),
    )

    Scene.faceit_use_corrective_shapes = BoolProperty(
        name='Use Corrective Shape Keys',
        description='Add Corrective Shape Keys to all generated Expressions. Shows options to add corrective shape for active object. (Prefix: "faceit_cc_")',
        default=True, update=update_corrective_shape_key_values,)

    Scene.faceit_try_mirror_corrective_shapes = BoolProperty(
        name='Mirror Corrective Shapes',
        description='Try to mirror the Corrective Shape Key for mirrored Expressions. all registered objects. (Prefix: "faceit_cc_")',
        default=True, update=update_corrective_shape_key_values,)

    Scene.faceit_corrective_sk_mirror_method = EnumProperty(
        name='Mirror Method',
        items=(
            ('NORMAL', 'Normal', 'Default Blender Shape Key Mirror'),
            ('TOPOLOGY', 'Topology', 'Topology Blender Shape Key Mirror'),
            ('FORCE', 'Force', 'Force Mirror with a kdtree Find Method'),
        ),
        default='NORMAL',
    )

    Scene.faceit_corrective_sk_mirror_affect_only_selected_objects = BoolProperty(
        name='Mirror Selected Objects Only',
        default=False,
        description='Mirrors only corrective shape keys on selected objects.',
    )

    Scene.faceit_use_auto_mirror_x = BoolProperty(
        name='Auto Mirror X',
        default=True,
        description='Automatically enable mirrorX pose option on expression change',
        update=update_auto_mirror_x,
    )


def unregister():
    del Scene.faceit_expression_list_index
    del Scene.faceit_expression_list
    del Scene.faceit_use_corrective_shapes
    del Scene.faceit_try_mirror_corrective_shapes
    del Scene.faceit_use_auto_mirror_x
