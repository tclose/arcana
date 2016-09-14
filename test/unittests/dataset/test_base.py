import os.path
import shutil
from unittest import TestCase
from nipype.pipeline import engine as pe
from nianalysis.base import Scan
from nianalysis.formats import nifti_gz_format
from nianalysis.requirements import mrtrix3_req
from nianalysis.dataset.base import Dataset, _create_component_dict
from nianalysis.interfaces.mrtrix import MRConvert, MRCat, MRMath
from nianalysis.archive.local import (
    LocalArchive, LocalSubjectSink, LocalProjectSink, SUBJECT_SUMMARY_NAME,
    PROJECT_SUMMARY_NAME)
from nianalysis.testing import test_data_dir
import logging

logger = logging.getLogger('NiAnalysis')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class DummyDataset(Dataset):

    def pipeline1(self):
        pipeline = self._create_pipeline(
            name='pipeline1',
            inputs=['start'],
            outputs=['pipeline1_1', 'pipeline1_2'],
            description="A dummy pipeline used to test 'run_pipeline' method",
            options={},
            requirements=[mrtrix3_req],
            citations=[],
            approx_runtime=1)
        mrconvert = pe.Node(MRConvert(), name="convert1")
        mrconvert2 = pe.Node(MRConvert(), name="convert2")
        # Connect inputs
        pipeline.connect_input('start', mrconvert, 'in_file')
        pipeline.connect_input('start', mrconvert2, 'in_file')
        # Connect outputs
        pipeline.connect_output('pipeline1_1', mrconvert, 'out_file')
        pipeline.connect_output('pipeline1_2', mrconvert2, 'out_file')
        # Check inputs/outputs are connected
        pipeline.assert_connected()
        return pipeline

    def pipeline2(self):
        pipeline = self._create_pipeline(
            name='pipeline2',
            inputs=['start', 'pipeline1_1'],
            outputs=['pipeline2'],
            description="A dummy pipeline used to test 'run_pipeline' method",
            options={},
            requirements=[mrtrix3_req],
            citations=[],
            approx_runtime=1)
        mrmath = pe.Node(MRCat(), name="mrcat")
        mrmath.inputs.axis = 0
        # Connect inputs
        pipeline.connect_input('start', mrmath, 'first_scan')
        pipeline.connect_input('pipeline1_1', mrmath, 'second_scan')
        # Connect outputs
        pipeline.connect_output('pipeline2', mrmath, 'out_file')
        # Check inputs/outputs are connected
        pipeline.assert_connected()
        return pipeline

    def pipeline3(self):
        pipeline = self._create_pipeline(
            name='pipeline3',
            inputs=['pipeline2'],
            outputs=['pipeline3'],
            description="A dummy pipeline used to test 'run_pipeline' method",
            options={},
            requirements=[mrtrix3_req],
            citations=[],
            approx_runtime=1)
        mrconvert = pe.Node(MRConvert(), name="convert")
        # Connect inputs
        pipeline.connect_input('pipeline2', mrconvert, 'in_file')
        # Connect outputs
        pipeline.connect_output('pipeline3', mrconvert, 'out_file')
        # Check inputs/outputs are connected
        pipeline.assert_connected()
        return pipeline

    def pipeline4(self):
        pipeline = self._create_pipeline(
            name='pipeline4',
            inputs=['pipeline3'],
            outputs=['pipeline4'],
            description="A dummy pipeline used to test 'run_pipeline' method",
            options={},
            requirements=[mrtrix3_req],
            citations=[],
            approx_runtime=1)
        mrconvert = pe.Node(MRConvert(), name="convert")
        # Connect inputs
        pipeline.connect_input('pipeline3', mrconvert, 'in_file')
        # Connect outputs
        pipeline.connect_output('pipeline4', mrconvert, 'out_file')
        # Check inputs/outputs are connected
        pipeline.assert_connected()
        return pipeline

    def subject_summary_pipeline(self):
        pipeline = self._create_pipeline(
            name="subject_summary",
            inputs=['start'],
            outputs=["subject_summary"],
            description=("Test of project summary variables"),
            options={},
            requirements=[mrtrix3_req],
            citations=[],
            approx_runtime=1)
        mrmath = pe.JoinNode(MRMath(), joinsource='session',
                             joinfield=['in_files'], name='mrmath')
        mrmath.inputs.operation = 'sum'
        # Connect inputs
        pipeline.connect_input('start', mrmath, 'in_files')
        # Connect outputs
        pipeline.connect_output('subject_summary', mrmath, 'out_file')
        pipeline.assert_connected()
        return pipeline

    def project_summary_pipeline(self):
        pipeline = self._create_pipeline(
            name="project_summary",
            inputs=['start'],
            outputs=["project_summary"],
            description=("Test of project summary variables"),
            options={},
            requirements=[mrtrix3_req],
            citations=[],
            approx_runtime=1)
        mrmath = pe.JoinNode(MRMath(), joinsource='session',
                             joinfield=['in_files'], name='mrmath')
        mrmath.inputs.operation = 'sum'
        # Connect inputs
        pipeline.connect_input('start', mrmath, 'in_files')
        # Connect outputs
        pipeline.connect_output('project_summary', mrmath, 'out_file')
        pipeline.assert_connected()
        return pipeline

    _components = _create_component_dict(
        Scan('start', nifti_gz_format),
        Scan('pipeline1_1', nifti_gz_format, pipeline1),
        Scan('pipeline1_2', nifti_gz_format, pipeline1),
        Scan('pipeline2', nifti_gz_format, pipeline2),
        Scan('pipeline3', nifti_gz_format, pipeline3),
        Scan('pipeline4', nifti_gz_format, pipeline4),
        Scan('subject_summary', nifti_gz_format, subject_summary_pipeline,
             multiplicity='per_subject'),
        Scan('project_summary', nifti_gz_format, project_summary_pipeline,
             multiplicity='per_project'))


class TestRunPipeline(TestCase):

    PROJECT_ID = 'PROJECTID'
    SUBJECT_IDS = ['SUBJECTID1', 'SUBJECTID2']
    SESSION_IDS = ['SESSIONID1', 'SESSIONID2']
    TEST_IMAGE = os.path.abspath(os.path.join(test_data_dir,
                                              'test_image.nii.gz'))
    TEST_DIR = os.path.abspath(os.path.join(test_data_dir, 'dataset'))
    BASE_DIR = os.path.abspath(os.path.join(TEST_DIR, 'base_dir'))
    WORKFLOW_DIR = os.path.abspath(os.path.join(TEST_DIR, 'workflow_dir'))

    def setUp(self):
        # Create test data on DaRIS
        self._study_id = None
        # Make cache and working dirs
        shutil.rmtree(self.TEST_DIR, ignore_errors=True)
        os.makedirs(self.WORKFLOW_DIR)
        self.subject_paths = []
        self.session_paths = []
        for subject_id in self.SUBJECT_IDS:
            subject_path = os.path.join(self.BASE_DIR, self.PROJECT_ID,
                                        subject_id)
            self.subject_paths.append(subject_path)
            for session_id in self.SESSION_IDS:
                session_path = os.path.join(subject_path, session_id)
                self.session_paths.append(session_path)
                os.makedirs(session_path)
                shutil.copy(self.TEST_IMAGE,
                            os.path.join(session_path, 'start.nii.gz'))
        archive = LocalArchive(self.BASE_DIR)
        self.dataset = DummyDataset(
            'TestDummy', self.PROJECT_ID, archive,
            input_scans={'start': Scan('start', nifti_gz_format)})

    def tearDown(self):
        # Clean up working dirs
        shutil.rmtree(self.TEST_DIR, ignore_errors=True)

    def test_pipeline_prerequisites(self):
        self.dataset.pipeline4().run()
        for scan in DummyDataset.components():
            if scan.multiplicity == 'per_session':
                for session_path in self.session_paths:
                    self.assertTrue(
                        os.path.exists(os.path.join(
                            session_path, scan.name + scan.format.extension)))

    def test_subject_summary(self):
        self.dataset.subject_summary_pipeline().run()
        for subject_path in self.subject_paths:
            self.assertTrue(
                os.path.exists(os.path.join(
                    subject_path, SUBJECT_SUMMARY_NAME,
                    'project_summary.nii.gz')))

    def test_project_summary(self):
        self.dataset.project_summary_pipeline().run()
        self.assertTrue(
            os.path.exists(os.path.join(
                self.BASE_DIR, self.PROJECT_ID, PROJECT_SUMMARY_NAME,
                'project_summary.nii.gz')))
