from base.base_tool import BaseTool
from base.class_decorators import geodata, results
from base.method_decorators import input_output_table, input_tableview, parameter
from collections import OrderedDict
from arcpy import Describe
from base.geodata import DoesNotExistError, UnknownSrsError, UnmatchedSrsError


tool_settings = {"label": "Compare Extents",
                 "description": "Compare Extents...",
                 "can_run_background": "True",
                 "category": "Geodata"}


@geodata
@results
class CompareExtentsGeodataTool(BaseTool):
    def __init__(self):
        BaseTool.__init__(self, tool_settings)
        self.execution_list = [self.initialise, self.iterate]
        self.aoi_dataset = self.aoi_extent = self.aoi_srs_name = self.aoi_extent_string = None

    @input_tableview("geodata_table", "Table for Geodata", False, ["geodata:geodata:"])
    @parameter("aoi_dataset", "Dataset to compare with", ["DEFeatureClass", "DERasterDataset"], "Required", False, "Input", None, None, None, None)
    @input_output_table
    def getParameterInfo(self):
        return BaseTool.getParameterInfo(self)

    def initialise(self):
        # p = self.get_parameter_dict(leave_as_object=["aoi_layer"])
        p = self.get_parameter_dict()
        self.send_info(p)
        self.aoi_dataset = p['aoi_dataset']
        d = Describe(self.aoi_dataset)
        self.aoi_extent = Describe(self.aoi_dataset).extent  # self.aoi_layer.getExtent(False)
        self.aoi_srs_name = self.aoi_extent.spatialReference.name
        self.aoi_extent_string = "{0} {1}".format(self.aoi_extent, self.aoi_srs_name)

        self.send_info(self.aoi_extent)
        self.send_info(self.aoi_extent_string)

    def iterate(self):
        self.iterate_function_on_tableview(self.process, "geodata_table", ["geodata"])
        return

    def process(self, data):
        ds_in = data["geodata"]
        if not self.geodata.exists(ds_in):
            raise DoesNotExistError(ds_in)

        d = self.geodata.describe(ds_in)
        ds_srs = d.get("dataset_spatialReference", "Unknown")
        if not ds_srs or "unknown" in ds_srs.lower():
            raise UnknownSrsError(ds_in)

        if ds_srs != self.aoi_srs_name:  # hack!! needs doing properly
            raise UnmatchedSrsError(ds_srs, self.aoi_srs_name)

        try:
            ds_extent = Describe(ds_in).extent
        except:
            raise ValueError("Could not obtain extent from {0}".format(ds_in))

        # default results
        con = dis = ovr = equ = wit = tch = "Unknown"
        ds_extent_trx = "Unknown"
        ds_extent_raw = "{0} {1}".format(ds_extent, ds_extent.spatialReference.name)

        if ds_extent.spatialReference.name != "Unknown":
            x = ds_extent.projectAs(self.aoi_extent.spatialReference)
            con = x.contains(self.aoi_extent)
            dis = x.disjoint(self.aoi_extent)
            ovr = x.overlaps(self.aoi_extent)
            equ = x.equals(self.aoi_extent)
            wit = x.within(self.aoi_extent)
            tch = x.touches(self.aoi_extent)
            ds_extent_trx = "{0} {1}".format(x, x.spatialReference.name)

        r = OrderedDict((
            ("geodata", ds_in),
            ("extent_aoi", self.aoi_extent_string),
            ("extent_dataset_raw", ds_extent_raw),
            ("extent_dataset_trx", ds_extent_trx),
            ("contains_aoi", con), ("within_aoi", wit),
            ("disjoint_aoi", dis), ("overlaps_aoi", ovr),
            ("equals_aoi", equ), ("touches_aoi", tch)))

        self.results.add(r)
        return
