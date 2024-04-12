bl_info = {
    "name": "Saved",
    "author": "Gabriel Villar",
    "blender": (4, 0, 2),
    "version": (0, 1),
    "category": "Workflow",
}

import os
import bpy
import bpy.path
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty, IntProperty, FloatProperty, StringProperty, CollectionProperty
from datetime import datetime, timedelta

class SaveWithCopyOperator(Operator):
    bl_idname = "wm.save_with_copy"
    bl_description = "Save active file and save next copy."
    bl_label = "Save With Copy"

    def update_history_and_get_last(self, settings, new_filename):

        print("update_history_and_get_last")
        
        return_past = "" 

        copies_history = getattr(settings, 'copies_history', None)

        current_id = settings.current_copy_id
        assert current_id <= 10, "settings.current_id shouldn't be above 10"

        have_found_item = False

        for history_item in settings.history:
            
            if history_item.identifier == current_id:
                
                return_past = history_item.filename

                history_item.filename = new_filename

                have_found_item = True

        if not have_found_item:

            new_item = settings.history.add()

            new_item.identifier = current_id

            new_item.filename = new_filename

        return return_past



    def save(self, context):
    
        settings = context.scene.saved_settings

        newpath = bpy.path.abspath("//" + settings.subfolder_name)

        if not os.path.exists(newpath):

            os.makedirs(newpath)

        current_date = datetime.now()

        last_date = datetime.fromtimestamp(eval(settings.last_date))

        interval = current_date - last_date

        interval_threshold = timedelta(minutes=settings.interval_minutes)

        if interval <= interval_threshold:

            print("Interval running, skipping copy saving, time left: " + str(interval_threshold - interval))
            return {'CANCELLED'}

        if settings.current_copy_id > settings.copies_amout:

            settings.current_copy_id = 1

        print("Current ID: " + str(settings.current_copy_id))

        filename = bpy.path.basename(bpy.context.blend_data.filepath).replace('.blend', '')

        if settings.include_date:

            filename += "_" + current_date.strftime("%y%m%d%H%M")

        else:

            filename += "_" + str(settings.current_copy_id)

        filename += ".blend"
        
        last_copy = self.update_history_and_get_last(settings, filename)

        if last_copy != '' and os.path.exists(newpath + "\\" + last_copy):
            
            print("Deleting file" + newpath + "\\" + last_copy)

            os.remove(newpath + "\\" + last_copy)

        bpy.ops.wm.save_as_mainfile(
            filepath = newpath + "\\" + filename, 
            check_existing=True, copy=True
        )

        settings.last_date = repr(current_date.timestamp())

        settings.current_copy_id += 1

        return {'FINISHED'}


    def execute(self, context):

        settings = context.scene.saved_settings

        file_size_mb = os.stat(bpy.context.blend_data.filepath).st_size / ( 1024 * 1024 )

        if file_size_mb > settings.max_file_size:
               
            self.report(
                type={'OPERATOR', 'WARNING'}, 
                message=
                "SAVED ADDON WARNING:\n  Trying to save copy bigger than user defined limit. Copy saving skipped. \n  Limit(Mb): " + 
                str(settings.max_file_size) + 
                "\n  Current(Mb): " +
                str(file_size_mb)
            )

            return {'CANCELLED'}

        return self.save(context)


    def invoke(self, context, event):
        bpy.ops.wm.save_mainfile('INVOKE_DEFAULT')

        if len(bpy.context.blend_data.filepath) > 0:
            return self.execute(context)
        else:
            return {'CANCELLED'}


class SavedAddonPreferences(AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        settings = context.scene.saved_settings

        layout = self.layout

        layout.label(text="Subfolder Name")
        layout.prop(settings, "subfolder_name")

        layout.prop(settings, "include_date")

        layout.prop(settings, "copies_amout")

        layout.prop(settings, "interval_minutes")

        layout.prop(settings, "max_file_size")

        layout.operator("wm.save_with_copy")
        
        
# Assign a collection.
class SavedHistoryItem(bpy.types.PropertyGroup):
    filename: bpy.props.StringProperty(name="Filename", default="")
    identifier: bpy.props.IntProperty(name="ID", default=-1)


class SavedSettings(bpy.types.PropertyGroup):

    subfolder_name: StringProperty(
        name="Subfolder Name",
        default = "Copies",
    )

    include_date: BoolProperty(
        name="Include Date in File's Name",
        default = True,
    )

    copies_amout: IntProperty(
        name="Copies Amount",
        default = 3,
        min = 1,
        max = 10,
    )

    interval_minutes: IntProperty(
        name="Interval Between Each Save(Minutes)",
        min = 1,
        max = 60,
        default = 3,
    )

    max_file_size: IntProperty(
        name="Maximum File Size in Megabytes",
        default = 200,
        min = 10,
        max = 1000,
    )

    current_copy_id: IntProperty(
        name="Current Copy ID",
        default = 1,
    )

    history: CollectionProperty(type=SavedHistoryItem)
    
    last_date: StringProperty(name="Last Date",default = "0")




def menu_func(self, context):
    self.layout.operator(SaveWithCopyOperator.bl_idname, text=SaveWithCopyOperator.bl_label)


classes = (
    SavedHistoryItem, SavedSettings, SavedAddonPreferences, SaveWithCopyOperator, 
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_view.append(menu_func)

    bpy.types.Scene.saved_settings = bpy.props.PointerProperty(type=SavedSettings)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.saved_settings

if __name__ == "__main__":
    register()