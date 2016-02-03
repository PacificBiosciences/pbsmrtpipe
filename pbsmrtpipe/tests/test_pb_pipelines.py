import getpass
import logging
import os
import shutil
import tempfile
import unittest
import pprint

import pbsmrtpipe.mock as M

import pbsmrtpipe.loader

REGISTERED_TASKS, REGISTERED_FILE_TYPES, REGISTERED_CHUNK_OPERATORS, REGISTERED_PIPELINES = pbsmrtpipe.loader.load_all()

import pbsmrtpipe.graph.bgraph as B
import pbsmrtpipe.cluster as C
import pbsmrtpipe.pb_io as IO

from pbsmrtpipe.schema_opt_utils import to_opt_id
from pbsmrtpipe.constants import to_pipeline_ns

from base import TEST_DATA_DIR, get_temp_file


INSTALLED_CLUSTER_TEMPLATES = C.load_installed_cluster_templates()

log = logging.getLogger(__name__)

DEEP_DEBUG = True


class _TestBase(unittest.TestCase):
    NTASKS = 10
    NFILES = 12
    EPOINTS = 1
    PB_PIPELINE_ID = to_pipeline_ns("rs_fetch_1")
    # this will be created from EPOINTS_NAMES in class setup
    EPOINTS_D = {}
    EPOINTS_NAMES = {'eid_input_xml': "_entry_point.xml"}
    TASK_OPTIONS = {to_opt_id('filter_artifact_score'): -7,
                    to_opt_id('filter_max_read_length'): 10000,
                    to_opt_id('filter_min_read_length'): 1000}

    # this object could create manually
    PRESET_XML = 'cli_preset_01.xml'

    @classmethod
    def setUpClass(cls):
        pipeline = REGISTERED_PIPELINES[cls.PB_PIPELINE_ID]
        log.debug(pipeline)

        cls.bindings = pipeline.all_bindings
        cls.EPOINTS_D = {k: get_temp_file(v) for k, v in cls.EPOINTS_NAMES.iteritems()}

        log.debug(pprint.pformat(cls.bindings, indent=4))
        log.debug("Number of registered tasks {n}".format(n=len(REGISTERED_TASKS)))

        cls.bgraph = B.binding_strs_to_binding_graph(REGISTERED_TASKS, cls.bindings)
        d = os.path.expanduser('~/scratch/tmp_pbsmrtpipe') if getpass.getuser() == 'mkocher' else None
        cls.output_dir = tempfile.mkdtemp(prefix='job_test_', dir=d)

        preset_record = IO.parse_pipeline_preset_xml(os.path.join(TEST_DATA_DIR, cls.PRESET_XML))
        cls.workflow_options = preset_record.to_workflow_level_opt()

        # leave this for now
        cls.envs = []
        cls.cluster_engine = C.load_installed_cluster_templates_by_name("sge")

    @classmethod
    def tearDownClass(cls):
        if not DEEP_DEBUG:
            if hasattr(cls, 'output_dir'):
                if os.path.exists(cls.output_dir):
                    shutil.rmtree(cls.output_dir)

    def test_validate_bindings_graph(self):
        emsg = "Invalid workflow with id '{x}'".format(x=self.PB_PIPELINE_ID)
        self.assertTrue(B.validate_binding_graph_integrity(self.bgraph), emsg)

    def test_number_of_entry_point_nodes(self):
        """Basic running test"""
        n = len(self.bgraph.entry_point_nodes())
        self.assertEqual(self.EPOINTS, n)

    def test_number_of_tasks(self):

        n = len(self.bgraph.task_nodes())
        self.assertEqual(self.NTASKS, n)

    def test_is_validate_binding_graph(self):
        self.assertTrue(B.validate_binding_graph_integrity(self.bgraph))

    def test_is_validate_binding_types(self):
        self.assertTrue(B.validate_compatible_binding_file_types(self.bgraph))

    def test_n_files(self):
        self.assertEqual(self.NFILES, len(self.bgraph.file_nodes()))

    @unittest.skip
    def test_mock_runner(self):
        B.resolve_entry_points(self.bgraph, self.EPOINTS_D)
        state = M.mock_workflow_runner(self.bgraph, {},
                                       self.output_dir,
                                       self.workflow_options,
                                       self.TASK_OPTIONS,
                                       REGISTERED_FILE_TYPES,
                                       self.cluster_engine, self.envs)

        _ = B.get_tasks_by_state(self.bgraph, B.TaskStates.SUCCESSFUL)

        if state is False:
            log.debug(B.to_binding_graph_summary(self.bgraph))

        self.assertTrue(state)


# class TestRSFetch(_TestBase):
#     NTASKS = 4
#     NFILES = 8
#     EPOINTS = 1
#     PB_PIPELINE_ID = to_pipeline_ns("rs_fetch_1")
#
#
# class TestRSFilter(_TestBase):
#     NTASKS = 11
#     NFILES = 28
#     EPOINTS = 1
#     PB_PIPELINE_ID = to_pipeline_ns("rs_filter_1")
#
#
# class TestRSMapping(_TestBase):
#     NTASKS = 22
#     NFILES = 59
#     PB_PIPELINE_ID = to_pipeline_ns("rs_mapping_1")
#     EPOINTS = 2
#     EPOINTS_NAMES = {'eid_input_xml': '_entry-point_01.xml',
#                      'eid_ref_fasta': "_reference_sequence.fasta"}
#
#
# class TestRSResquencing(_TestBase):
#     NTASKS = 29
#     NFILES = 84
#     EPOINTS = 2
#     PB_PIPELINE_ID = to_pipeline_ns("rs_resequencing_1")
#     EPOINTS_NAMES = {'eid_input_xml': '_entry-point_01.xml',
#                      'eid_ref_fasta': "_reference_sequence.fasta"}
#
#
# class TestResequencingBarcode(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_resequencing_barcode_1")
#
#     NFILES = 94
#     EPOINTS = 3
#     NTASKS = 33
#
#
# class TestReadOfInsert(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_roi_1")
#
#     NFILES = 14
#     EPOINTS = 1
#     NTASKS = 6
#
#
# class TestReadOfInsertMapping(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_roi_mapping_1")
#
#     NFILES = 34
#     EPOINTS = 2
#     NTASKS = 14
#
#
# class TestSiteAcceptanceTest(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_sat_1")
#
#     NFILES = 88
#     EPOINTS = 2
#     NTASKS = 30
#
#
# class TestBridgeMapper(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_bridge_mapper_1")
#
#     NFILES = 63
#     EPOINTS = 2
#     NTASKS = 23
#
#
# class TestModificationDetection(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_modification_detection_1")
#
#     NFILES = 93
#     EPOINTS = 2
#     NTASKS = 31
#
#
# class TestModificationAndMotif(_TestBase):
#     PB_PIPELINE_ID = to_pipeline_ns("rs_modification_motif_analysis_1")
#
#     NFILES = 105
#     EPOINTS = 2
#     NTASKS = 34
