"""

"""
from base.base_tool import BaseTool
from base import utils
from base.decorators import input_tableview, input_output_table, parameter, raster_formats
from arcpy.sa import SetNull


tool_settings = {"label": "Set Value to Null",
                 "description": "Sets...",
                 "can_run_background": "True",
                 "category": "Raster"}


class SetValueToNullRasterTool(BaseTool):
    """
    """

    def __init__(self):
        """

        Returns:

        """

        BaseTool.__init__(self, tool_settings)

        self.execution_list = [self.iterate]

        return

    @input_tableview(data_type="raster")
    @parameter("val_to_null", "Value to Set Null", "GPDouble", "Required", False, "Input", None, None, None, None)
    @parameter("raster_format", "Format for output rasters", "GPString", "Required", False, "Input", raster_formats, None, None, "Esri Grid")
    @input_output_table(affixing=True)
    def getParameterInfo(self):
        """

        Returns:

        """

        return BaseTool.getParameterInfo(self)

    def iterate(self):
        """

        Returns:

        """

        self.iterate_function_on_tableview(self.set_null, return_to_results=True)

        return

    def set_null(self, data):
        """

        Args:
            data:

        Returns:

        """

        r_in = data['raster']

        utils.validate_geodata(r_in, raster=True)

        r_out = utils.make_raster_name(r_in, self.output_file_workspace, self.raster_format, self.output_filename_prefix, self.output_filename_suffix)

        self.info("Setting values of {0} to Null in {1} -> {2}".format(self.val_to_null, r_in, r_out))

        out_ras = SetNull(r_in, r_in, 'VALUE = {0}'.format(self.val_to_null))

        out_ras.save(r_out)

        return {"raster": r_out, "source_geodata": r_in}


