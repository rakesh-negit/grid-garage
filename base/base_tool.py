# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 10:48:26 2016

@author: byed
"""
from __future__ import print_function
from utils import static_vars, make_tuple, is_local_gdb
from sys import exc_info
from traceback import format_exception
from os import environ, makedirs
from os.path import join, exists
from contextlib import contextmanager
from functools import wraps
import arcpy
import logging
from collections import OrderedDict
from base.results import GgResult
from datetime import datetime


def time_stamp(fmt='%Y%m%d_%H%M%S'):

    return datetime.now().strftime(fmt)


debug = print  # updated to logger.debug after logging is configured


@contextmanager
def error_trap(context):
    """ A context manager that traps and logs exception in its block.
        Usage:
        with error_trapping('optional description'):
            might_raise_exception()
        this_will_always_be_called()
    """
    # try:
    idx = context.__name__
    # except AttributeError:
    #     idx = inspect.getframeinfo(inspect.currentframe())[2]

    # in_msg = "IN context= " + idx
    # out_msg = "OUT context= " + idx

    try:

        debug("IN: " + idx)

        yield

        debug("OUT: " + idx)

    except Exception as e:

        debug(repr(format_exception(*exc_info())))

        raise e

    return


def log_error(f):
    """ A decorator to trap and log exceptions """

    @wraps(f)
    def log_wrap(*args, **kwargs):
        with error_trap(f):
            return f(*args, **kwargs)

    return log_wrap


class ArcStreamHandler(logging.StreamHandler):
    """ Logging handler to log messages to ArcGIS """

    def __init__(self, messages):

        logging.StreamHandler.__init__(self)

        self.messages = messages

    def emit(self, record):
        """ Emit the record to the ArcGIS messages object

        Args:
            record (): The message record

        Returns:

        """

        msg = self.format(record)
        msg = msg.replace("\n", ", ").replace("\t", " ").replace("  ", " ")
        lvl = record.levelno

        if self.messages:
            if lvl in [logging.ERROR, logging.CRITICAL]:
                self.messages.addErrorMessage(msg)

            elif lvl == logging.WARNING:
                self.messages.addWarningMessage(msg)

            else:
                self.messages.addMessage(msg)

        self.flush()

        return


class BaseTool(object):

    def __init__(self, settings):
        print("BaseTool.__init__")

        self.appdata_path = join(environ["USERPROFILE"], "AppData", "Local", "GridGarage")
        self.tool_name = type(self).__name__
        self.time_stamp = time_stamp()
        self.run_id = "{0}_{1}".format(self.tool_name, self.time_stamp)

        self.log_file = join(self.appdata_path, self.tool_name + ".log")
        self.logger = None
        self.debug = None
        self.info = None
        self.warn = None
        self.error = None

        self.label = settings.get("label", "label not set")
        self.description = settings.get("description", "description not set")
        self.canRunInBackground = settings.get("can_run_background", False)
        self.category = settings.get("category", False)

        self.parameters = None
        self.messages = None
        self.execution_list = []

        self.result = GgResult()

        return

    def configure_logging(self):

        print("BaseTool.configure_logging")

        if not self.messages:
            return
            print("Initialising logging...")
        else:
            self.messages.addMessage("Initialising logging...")

        logger = logging.getLogger(self.tool_name)

        self.debug = logger.debug
        self.info = logger.info
        self.warn = logger.warn
        self.error = logger.error

        global debug
        debug = self.debug

        logger.handlers = []  # be rid of ones from other tools
        logger.setLevel(logging.DEBUG)

        ah = ArcStreamHandler(self.messages)
        ah.setLevel(logging.INFO)
        logger.addHandler(ah)
        logger.info("ArcMap stream handler configured")

        if not exists(self.log_file):

            if not exists(self.appdata_path):
                logger.info("Creating app data path {}".format(self.appdata_path))
                makedirs(self.appdata_path)

            logger.info("Creating log file {}".format(self.log_file))
            open(self.log_file, 'a').close()

        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d %(levelname)s %(module)s %(funcName)s %(lineno)s %(message)s", datefmt="%Y%m%d %H%M%S")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info("File stream handler configured")

        self.logger = logger

        logger.info("Debugging log file is located at '{}'".format(self.log_file))

        return

    def get_parameter(self, param_name, raise_not_found_error=False, parameters=None):

        if not parameters:
            parameters = self.parameters

        try:
            param = self.get_parameter_dict(leave_as_object=param_name, parameters=parameters)[param_name]
        except KeyError:
            if raise_not_found_error:
                raise ValueError("Parameter '{}' not found".format(param_name))
            else:
                return None

        return param

    def getParameterInfo(self):

        return []

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        try:
            # ps = [(i, p.name) for i, p in enumerate(parameters)]
            # self.debug("BaseTool.updateParameters {}".format(ps))

            # set default result table name

            out_tbl_par = None
            for p in parameters:
                if p.name == "result_table_name":
                    out_tbl_par = p
                    break

            if out_tbl_par and out_tbl_par.value == "#run_id#":
                out_tbl_par.value = self.run_id

            # validate workspace and raster format

            out_ws_par = self.get_parameter("output_workspace", raise_not_found_error=False)
            ras_fmt_par = self.get_parameter("raster_format", raise_not_found_error=False)

            if out_ws_par and ras_fmt_par:

                out_ws_par.clearMessage()
                ras_fmt_par.clearMessage()

                if out_ws_par.altered or ras_fmt_par.altered:

                    ws = out_ws_par.value
                    fmt = ras_fmt_par.value

                    if is_local_gdb(ws) and fmt != "Esri Grid":
                        ras_fmt_par.setErrorMessage("Invalid raster format for workspace type")
        except:
            pass

        return

    def updateMessages(self, parameters):

        debug("updateMessages exposure code")
        # out_ws_par = None
        # for p in parameters:
        #     if p.name == "output_workspace":
        #         out_ws_par = p
        #         break
        #
        # ras_fmt_par = None
        # for p in parameters:
        #     if p.name == "raster_format":
        #         ras_fmt_par = p
        #         break
        #
        # if out_ws_par and ras_fmt_par:
        #
        #     out_ws_par.clearMessage()
        #     ras_fmt_par.clearMessage()
        #     # self.debug("messages cleared")
        #
        #     if out_ws_par.altered or ras_fmt_par.altered:
        #         # self.debug("out_ws_par.altered or out_rasfmt_par.altered")
        #
        #         ws = out_ws_par.value
        #         fmt = ras_fmt_par.value
        #         # self.debug("ws={} fmt={}".format(ws, fmt))
        #         if base.utils.is_local_gdb(ws) and fmt != "Esri Grid":
        #             ras_fmt_par.setErrorMessage("Invalid raster format for workspace type")
        # try:
        #     # self.debug("updateMessages")
        #
        #     out_ws_par = self.get_parameter_by_name("output_workspace")  # None
        #     out_rasfmt_par = self.get_parameter_by_name("raster_format")  # None
        #
        #     if out_ws_par and out_rasfmt_par:
        #         # self.debug("out_ws_par and out_rasfmt_par")
        #
        #         out_ws_par.clearMessage()
        #         out_rasfmt_par.clearMessage()
        #         # self.debug("messages cleared")
        #
        #         if out_ws_par.altered or out_rasfmt_par.altered:
        #             # self.debug("out_ws_par.altered or out_rasfmt_par.altered")
        #
        #             ws = out_ws_par.value
        #             fmt = out_rasfmt_par.value
        #             # self.debug("ws={} fmt={}".format(ws, fmt))
        #             if base.utils.is_local_gdb(ws) and fmt != "Esri Grid":
        #                 out_rasfmt_par.setErrorMessage("Invalid raster format for workspace type")
        # except Exception as e:
        #     # self.debug("updateMessages error : {}".format(e))
        #     print str(e)

        # BaseTool.updateMessages(self, parameters)
        # stretch = parameters[2].value == 'STRETCH'
        # if stretch and not parameters[3].valueAsText:
        #     parameters[3].setIDMessage("ERROR", 735, parameters[3].displayName)
        # if stretch and not parameters[4].valueAsText:
        #     parameters[4].setIDMessage("ERROR", 735, parameters[4].displayName)

        return

    @log_error
    def execute(self, parameters, messages):

        if not self.execution_list:
            raise ValueError("Tool execution list is empty")

        self.parameters = parameters
        self.messages = messages

        self.configure_logging()

        if not self.messages:  # stop ide errors during dev
            return

        # parameter_dictionary = OrderedDict([(p.name, p.valueAsText) for p in self.parameters])
        # parameter_dictionary = OrderedDict([(p.DisplayName, p.valueAsText) for p in self.parameters])
        # parameter_summary = ", ".join(["{}: {}".format(k, v) for k, v in parameter_dictionary.iteritems()])
        self.info("Parameter summary: {}".format(["{} ({}): {}".format(p.DisplayName, p.name, p.valueAsText) for p in self.parameters]))

        for k, v in self.get_parameter_dict().iteritems():
            setattr(self, k, v)

        self.debug("Tool attributes set {}".format(self.__dict__))

        try:
            self.result.initialise(self.get_parameter("result_table"), self.get_parameter("fail_table"), self.get_parameter("output_workspace").value, self.get_parameter("result_table_name").value, self.logger)

        except AttributeError:
            pass

        try:
            if self.output_file_workspace in [None, "", "#"]:
                self.output_file_workspace = self.result.output_workspace

        except Exception:
            pass

        for f in self.execution_list:
            f = log_error(f)
            f()

        try:
            self.result.write()

        except TypeError:
            pass

        return

    def get_parameter_dict(self, leave_as_object=(), parameters=()):
        """ Create a dictionary of parameters

        Args:
            leave_as_object (): A list of parameter names to leave as objects rather than return strings

        Returns: A dictionary of parameters - strings or parameter objects

        """

        # create the dict
        # TODO make multivalue parameters a list
        # TODO see what binning the bloody '#' does to tools
        if not parameters:
            parameters = self.parameters

        pd = {}
        for p in parameters:
            name = p.name
            if name in leave_as_object:
                pd[name] = p
            elif p.datatype == "Boolean":
                pd[name] = [False, True][p.valueAsText == "true"]
            elif p.datatype == "Double":
                pd[name] = float(p.valueAsText) if p.valueAsText else None
            elif p.datatype == "Long":
                pd[name] = int(float(p.valueAsText)) if p.valueAsText else None
            else:
                pd[name] = p.valueAsText or "#"

        # now fix some specific parameters
        x = pd.get("raster_format", None)
        if x:
            pd["raster_format"] = "" if x.lower() == "esri grid" else '.' + x

        def set_hash_to_empty(p):
            v = pd.get(p, None)
            if v:
                pd[p] = "" if v == "#" else v
            return

        set_hash_to_empty("output_filename_prefix")
        set_hash_to_empty("output_filename_suffix")

        return pd

    def iterate_function_on_tableview(self, func, parameter_name="", nonkey_names=[], return_to_results=False):
        """ Runs a function over the values in a tableview parameter - a common tool scenario

        Args:
            func (): Function to run
            parameter_name (): Parameter to run on
            key_names (): Fields in the rows to provide

        Returns:

        """
        self.debug("locals = {}".format(locals()))

        param = self.get_parameter(parameter_name) if parameter_name else self.parameters[0]

        if param.datatype != "Table View":
            raise ValueError("That parameter is not a table or table view ({0})".format(param.name))

        multi_val = getattr(param, "multiValue", False)
        if multi_val:
            raise ValueError("Multi-value tableview iteration is not yet implemented")

        if arcpy.Exists(param.name):
            arcpy.Delete_management(param.name)

        arcpy.MakeTableView_management(param.valueAsText, param.name)

        f_alias = [p.name for i, p in enumerate(self.parameters[1:]) if 0 in p.parameterDependencies]
        f_name = [self.get_parameter(f_name).valueAsText for f_name in f_alias]
        alias_name = {k: v for k, v in dict(zip(f_alias, f_name)).iteritems() if v not in [None, "NONE"]}

        if nonkey_names:
            alias_name.update({v: v for v in nonkey_names})  # this is a list at the mo

        rows = [r for r in arcpy.da.SearchCursor(param.name, alias_name.values())]

        # iterate

        self.do_iteration(func, rows, alias_name, return_to_results)

        return

    def iterate_function_on_parameter(self, func, parameter_name, key_names, return_to_results=False):
        """ Runs a function over the values in a parameter - a less common tool scenario

        Args:
            func (): Function to run
            parameter_name (): Parameter to run on
            key_names (): Fields in the rows to provide

        Returns:

        """

        param = self.get_parameter(parameter_name)
        multi_val = getattr(param, "multiValue", False)
        self.debug("multiValue attribute is {}".format(multi_val))

        if param.datatype == "Table View":
            raise ValueError("No, use 'iterate_function_on_tableview'")

        self.debug("param.valueAsText =  {}".format(param.valueAsText))
        self.debug("param.valueAsText.split(';' =  {}".format(param.valueAsText.split(";")))
        rows = param.valueAsText.split(";") if multi_val else [param.valueAsText]

        self.debug("Processing rows will be {}".format(rows))

        key_names = {v: v for v in key_names}

        # iterate

        self.do_iteration(func, rows, key_names, return_to_results)

        return

    def do_iteration(self, func, rows, name_vals, return_to_results):

        if not rows:
            raise ValueError("No values or records to process.")

        fname = func.__name__

        rows = [{k: v for k, v in zip(name_vals.keys(), make_tuple(row))} for row in rows]
        total_rows = len(rows)

        self.info("{} items to process".format(total_rows))

        for row_num, row in enumerate(rows, start=1):
            try:
                self.info("{} > Processing row {} of {}".format(time_stamp("%H:%M:%S%f")[:-3], row_num, total_rows))
                self.debug("Running {} with row={}".format(fname, row))
                res = func(row)
                if return_to_results:
                    try:
                        self.result.add_pass(res)
                    except AttributeError:
                        raise ValueError("No result attribute for result record")

            except Exception as e:

                self.error("error executing {}: {}".format(fname, str(e)))

                try:
                    self.result.add_fail(row)
                except AttributeError:
                    pass

        return
