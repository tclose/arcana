from arcana.testing import BaseTestCase as TestCase
import subprocess as sp
from arcana.requirement import Requirement
from arcana.interfaces.utils import Merge
from arcana.dataset import DatasetMatch, DatasetSpec
from nianalysis.data_format import mrtrix_format
from nianalysis.requirement import mrtrix3_req
from arcana.option import OptionSpec
from arcana.study.base import Study
from arcana.study.multi import (
    MultiStudy, SubStudySpec, MultiStudyMetaClass, StudyMetaClass)
from arcana.interfaces.mrtrix import MRMath
from arcana.option import Option
from arcana.node import ArcanaNodeMixin  # @IgnorePep8
from arcana.exception import ArcanaModulesNotInstalledException  # @IgnorePep8


class StudyA(Study):

    __metaclass__ = StudyMetaClass

    add_data_specs = [
        DatasetSpec('x', mrtrix_format),
        DatasetSpec('y', mrtrix_format),
        DatasetSpec('z', mrtrix_format, 'pipeline_alpha')]

    add_option_specs = [
        OptionSpec('o1', 1),
        OptionSpec('o2', '2'),
        OptionSpec('o3', 3.0)]

    def pipeline_alpha(self, **kwargs):  # @UnusedVariable
        pipeline = self.create_pipeline(
            name='pipeline_alpha',
            inputs=[DatasetSpec('x', mrtrix_format),
                    DatasetSpec('y', mrtrix_format)],
            outputs=[DatasetSpec('z', mrtrix_format)],
            desc="A dummy pipeline used to test MultiStudy class",
            version=1,
            citations=[],
            **kwargs)
        merge = pipeline.create_node(Merge(2), name="merge")
        mrmath = pipeline.create_node(MRMath(), name="mrmath",
                                      requirements=[mrtrix3_req])
        mrmath.inputs.operation = 'sum'
        # Connect inputs
        pipeline.connect_input('x', merge, 'in1')
        pipeline.connect_input('y', merge, 'in2')
        # Connect nodes
        pipeline.connect(merge, 'out', mrmath, 'in_files')
        # Connect outputs
        pipeline.connect_output('z', mrmath, 'out_file')
        return pipeline


class StudyB(Study):

    __metaclass__ = StudyMetaClass

    add_data_specs = [
        DatasetSpec('w', mrtrix_format),
        DatasetSpec('x', mrtrix_format),
        DatasetSpec('y', mrtrix_format, 'pipeline_beta'),
        DatasetSpec('z', mrtrix_format, 'pipeline_beta')]

    add_option_specs = [
        OptionSpec('o1', 10),
        OptionSpec('o2', '20'),
        OptionSpec('o3', 30.0),
        OptionSpec('product_op', 'not-specified')]  # Needs to be set to 'product' @IgnorePep8

    def pipeline_beta(self, **kwargs):  # @UnusedVariable
        pipeline = self.create_pipeline(
            name='pipeline_beta',
            inputs=[DatasetSpec('w', mrtrix_format),
                    DatasetSpec('x', mrtrix_format)],
            outputs=[DatasetSpec('y', mrtrix_format),
                     DatasetSpec('z', mrtrix_format)],
            desc="A dummy pipeline used to test MultiStudy class",
            version=1,
            citations=[],
            **kwargs)
        merge1 = pipeline.create_node(Merge(2), name='merge1')
        merge2 = pipeline.create_node(Merge(2), name='merge2')
        merge3 = pipeline.create_node(Merge(2), name='merge3')
        mrsum1 = pipeline.create_node(MRMath(), name="mrsum1",
                                      requirements=[mrtrix3_req])
        mrsum1.inputs.operation = 'sum'
        mrsum2 = pipeline.create_node(MRMath(), name="mrsum2",
                                      requirements=[mrtrix3_req])
        mrsum2.inputs.operation = 'sum'
        mrproduct = pipeline.create_node(MRMath(), name="mrproduct",
                                         requirements=[mrtrix3_req])
        mrproduct.inputs.operation = pipeline.option('product_op')
        # Connect inputs
        pipeline.connect_input('w', merge1, 'in1')
        pipeline.connect_input('x', merge1, 'in2')
        pipeline.connect_input('x', merge2, 'in1')
        # Connect nodes
        pipeline.connect(merge1, 'out', mrsum1, 'in_files')
        pipeline.connect(mrsum1, 'out_file', merge2, 'in2')
        pipeline.connect(merge2, 'out', mrsum2, 'in_files')
        pipeline.connect(mrsum1, 'out_file', merge3, 'in1')
        pipeline.connect(mrsum2, 'out_file', merge3, 'in2')
        pipeline.connect(merge3, 'out', mrproduct, 'in_files')
        # Connect outputs
        pipeline.connect_output('y', mrsum2, 'out_file')
        pipeline.connect_output('z', mrproduct, 'out_file')
        return pipeline


class FullMultiStudy(MultiStudy):

    __metaclass__ = MultiStudyMetaClass

    add_sub_study_specs = [
        SubStudySpec('ss1', StudyA,
                     {'a': 'x',
                      'b': 'y',
                      'd': 'z',
                      'p1': 'o1',
                      'p2': 'o2',
                      'p3': 'o3'}),
        SubStudySpec('ss2', StudyB,
                     {'b': 'w',
                      'c': 'x',
                      'e': 'y',
                      'f': 'z',
                      'q1': 'o1',
                      'q2': 'o2',
                      'p3': 'o3',
                      'required_op': 'product_op'})]

    add_data_specs = [
        DatasetSpec('a', mrtrix_format),
        DatasetSpec('b', mrtrix_format),
        DatasetSpec('c', mrtrix_format),
        DatasetSpec('d', mrtrix_format, 'pipeline_alpha_trans'),
        DatasetSpec('e', mrtrix_format, 'pipeline_beta_trans'),
        DatasetSpec('f', mrtrix_format, 'pipeline_beta_trans')]

    add_option_specs = [
        OptionSpec('p1', 100),
        OptionSpec('p2', '200'),
        OptionSpec('p3', 300.0),
        OptionSpec('q1', 150),
        OptionSpec('q2', '250'),
        OptionSpec('required_op', 'still-not-specified')]

    pipeline_alpha_trans = MultiStudy.translate(
        'ss1', 'pipeline_alpha')
    pipeline_beta_trans = MultiStudy.translate(
        'ss2', 'pipeline_beta')


class PartialMultiStudy(MultiStudy):

    __metaclass__ = MultiStudyMetaClass

    add_sub_study_specs = [
        SubStudySpec('ss1', StudyA,
                     {'a': 'x', 'b': 'y', 'p1': 'o1'}),
        SubStudySpec('ss2', StudyB,
                     {'b': 'w', 'c': 'x', 'p1': 'o1'})]

    add_data_specs = [
        DatasetSpec('a', mrtrix_format),
        DatasetSpec('b', mrtrix_format),
        DatasetSpec('c', mrtrix_format)]

    pipeline_alpha_trans = MultiStudy.translate(
        'ss1', 'pipeline_alpha')

    add_option_specs = [
        OptionSpec('p1', 1000)]


class MultiMultiStudy(MultiStudy):

    __metaclass__ = MultiStudyMetaClass

    add_sub_study_specs = [
        SubStudySpec('ss1', StudyA, {}),
        SubStudySpec('full', FullMultiStudy),
        SubStudySpec('partial', PartialMultiStudy)]

    add_data_specs = [
        DatasetSpec('g', mrtrix_format, 'combined_pipeline')]

    add_option_specs = [
        OptionSpec('combined_op', 'sum')]

    def combined_pipeline(self, **kwargs):
        pipeline = self.create_pipeline(
            name='combined',
            inputs=[DatasetSpec('ss1_z', mrtrix_format),
                    DatasetSpec('full_e', mrtrix_format),
                    DatasetSpec('partial_ss2_z', mrtrix_format)],
            outputs=[DatasetSpec('g', mrtrix_format)],
            desc=(
                "A dummy pipeline used to test MultiMultiStudy class"),
            version=1,
            citations=[],
            **kwargs)
        merge = pipeline.create_node(Merge(3), name="merge")
        mrmath = pipeline.create_node(MRMath(), name="mrmath",
                                      requirements=[mrtrix3_req])
        mrmath.inputs.operation = pipeline.option('combined_op')
        # Connect inputs
        pipeline.connect_input('ss1_z', merge, 'in1')
        pipeline.connect_input('full_e', merge, 'in2')
        pipeline.connect_input('partial_ss2_z', merge, 'in3')
        # Connect nodes
        pipeline.connect(merge, 'out', mrmath, 'in_files')
        # Connect outputs
        pipeline.connect_output('g', mrmath, 'out_file')
        return pipeline


class TestMulti(TestCase):

    def setUp(self):
        super(TestMulti, self).setUp()
        # Calculate MRtrix module required for 'mrstats' commands
        try:
            self.mrtrix_req = Requirement.best_requirement(
                [mrtrix3_req], ArcanaNodeMixin.available_modules(),
                ArcanaNodeMixin.preloaded_modules())
        except ArcanaModulesNotInstalledException:
            self.mrtrix_req = None

    def test_full_multi_study(self):
        study = self.create_study(
            FullMultiStudy, 'full',
            [DatasetMatch('a', mrtrix_format, 'ones'),
             DatasetMatch('b', mrtrix_format, 'ones'),
             DatasetMatch('c', mrtrix_format, 'ones')],
            options=[Option('required_op', 'product')])
        d = study.data('d', subject_id='SUBJECT', visit_id='VISIT')
        e = study.data('e')[0]
        f = study.data('f')[0]
        if self.mrtrix_req is not None:
            ArcanaNodeMixin.load_module(*self.mrtrix_req)
        try:
            d_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(d.path),
                shell=True))
            self.assertEqual(d_mean, 2.0)
            e_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(e.path),
                shell=True))
            self.assertEqual(e_mean, 3.0)
            f_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(f.path),
                shell=True))
            self.assertEqual(f_mean, 6.0)
        finally:
            if self.mrtrix_req is not None:
                ArcanaNodeMixin.unload_module(*self.mrtrix_req)
        # Test option values in MultiStudy
        self.assertEqual(study._get_option('p1').value, 100)
        self.assertEqual(study._get_option('p2').value, '200')
        self.assertEqual(study._get_option('p3').value, 300.0)
        self.assertEqual(study._get_option('q1').value, 150)
        self.assertEqual(study._get_option('q2').value, '250')
        self.assertEqual(study._get_option('required_op').value, 'product')
        # Test option values in SubStudy
        ss1 = study.sub_study('ss1')
        self.assertEqual(ss1._get_option('o1').value, 100)
        self.assertEqual(ss1._get_option('o2').value, '200')
        self.assertEqual(ss1._get_option('o3').value, 300.0)
        ss2 = study.sub_study('ss2')
        self.assertEqual(ss2._get_option('o1').value, 150)
        self.assertEqual(ss2._get_option('o2').value, '250')
        self.assertEqual(ss2._get_option('o3').value, 300.0)
        self.assertEqual(ss2._get_option('product_op').value, 'product')

    def test_partial_multi_study(self):
        study = self.create_study(
            PartialMultiStudy, 'partial',
            [DatasetMatch('a', mrtrix_format, 'ones'),
             DatasetMatch('b', mrtrix_format, 'ones'),
             DatasetMatch('c', mrtrix_format, 'ones')],
            options=[Option('ss2_product_op', 'product')])
        ss1_z = study.data('ss1_z')[0]
        ss2_y = study.data('ss2_y')[0]
        ss2_z = study.data('ss2_z')[0]
        if self.mrtrix_req is not None:
            ArcanaNodeMixin.load_module(*self.mrtrix_req)
        try:
            ss1_z_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(ss1_z.path),
                shell=True))
            self.assertEqual(ss1_z_mean, 2.0)
            ss2_y_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(ss2_y.path),
                shell=True))
            self.assertEqual(ss2_y_mean, 3.0)
            ss2_z_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(ss2_z.path),
                shell=True))
            self.assertEqual(ss2_z_mean, 6.0)
        finally:
            if self.mrtrix_req is not None:
                ArcanaNodeMixin.unload_module(*self.mrtrix_req)
        # Test option values in MultiStudy
        self.assertEqual(study._get_option('p1').value, 1000)
        self.assertEqual(study._get_option('ss1_o2').value, '2')
        self.assertEqual(study._get_option('ss1_o3').value, 3.0)
        self.assertEqual(study._get_option('ss2_o2').value, '20')
        self.assertEqual(study._get_option('ss2_o3').value, 30.0)
        self.assertEqual(study._get_option('ss2_product_op').value, 'product')
        # Test option values in SubStudy
        ss1 = study.sub_study('ss1')
        self.assertEqual(ss1._get_option('o1').value, 1000)
        self.assertEqual(ss1._get_option('o2').value, '2')
        self.assertEqual(ss1._get_option('o3').value, 3.0)
        ss2 = study.sub_study('ss2')
        self.assertEqual(ss2._get_option('o1').value, 1000)
        self.assertEqual(ss2._get_option('o2').value, '20')
        self.assertEqual(ss2._get_option('o3').value, 30.0)
        self.assertEqual(ss2._get_option('product_op').value, 'product')

    def test_multi_multi_study(self):
        study = self.create_study(
            MultiMultiStudy, 'multi_multi',
            [DatasetMatch('ss1_x', mrtrix_format, 'ones'),
             DatasetMatch('ss1_y', mrtrix_format, 'ones'),
             DatasetMatch('full_a', mrtrix_format, 'ones'),
             DatasetMatch('full_b', mrtrix_format, 'ones'),
             DatasetMatch('full_c', mrtrix_format, 'ones'),
             DatasetMatch('partial_a', mrtrix_format, 'ones'),
             DatasetMatch('partial_b', mrtrix_format, 'ones'),
             DatasetMatch('partial_c', mrtrix_format, 'ones')],
            options=[Option('full_required_op', 'product'),
                     Option('partial_ss2_product_op', 'product')])
        g = study.data('g')[0]
        if self.mrtrix_req is not None:
            ArcanaNodeMixin.load_module(*self.mrtrix_req)
        try:
            g_mean = float(sp.check_output(
                'mrstats {} -output mean'.format(g.path),
                shell=True))
            self.assertEqual(g_mean, 11.0)
        finally:
            if self.mrtrix_req is not None:
                ArcanaNodeMixin.unload_module(*self.mrtrix_req)
        # Test option values in MultiStudy
        self.assertEqual(study._get_option('full_p1').value, 100)
        self.assertEqual(study._get_option('full_p2').value, '200')
        self.assertEqual(study._get_option('full_p3').value, 300.0)
        self.assertEqual(study._get_option('full_q1').value, 150)
        self.assertEqual(study._get_option('full_q2').value, '250')
        self.assertEqual(study._get_option('full_required_op').value,
                         'product')
        # Test option values in SubStudy
        ss1 = study.sub_study('full').sub_study('ss1')
        self.assertEqual(ss1._get_option('o1').value, 100)
        self.assertEqual(ss1._get_option('o2').value, '200')
        self.assertEqual(ss1._get_option('o3').value, 300.0)
        ss2 = study.sub_study('full').sub_study('ss2')
        self.assertEqual(ss2._get_option('o1').value, 150)
        self.assertEqual(ss2._get_option('o2').value, '250')
        self.assertEqual(ss2._get_option('o3').value, 300.0)
        self.assertEqual(ss2._get_option('product_op').value, 'product')
        # Test option values in MultiStudy
        self.assertEqual(study._get_option('partial_p1').value, 1000)
        self.assertEqual(study._get_option('partial_ss1_o2').value, '2')
        self.assertEqual(study._get_option('partial_ss1_o3').value, 3.0)
        self.assertEqual(study._get_option('partial_ss2_o2').value, '20')
        self.assertEqual(study._get_option('partial_ss2_o3').value, 30.0)
        self.assertEqual(
            study._get_option('partial_ss2_product_op').value, 'product')
        # Test option values in SubStudy
        ss1 = study.sub_study('partial').sub_study('ss1')
        self.assertEqual(ss1._get_option('o1').value, 1000)
        self.assertEqual(ss1._get_option('o2').value, '2')
        self.assertEqual(ss1._get_option('o3').value, 3.0)
        ss2 = study.sub_study('partial').sub_study('ss2')
        self.assertEqual(ss2._get_option('o1').value, 1000)
        self.assertEqual(ss2._get_option('o2').value, '20')
        self.assertEqual(ss2._get_option('o3').value, 30.0)
        self.assertEqual(ss2._get_option('product_op').value, 'product')

    def test_missing_option(self):
        # Misses the required 'full_required_op' option, which sets
        # the operation of the second node in StudyB's pipeline to
        # 'product'
        missing_option_study = self.create_study(
            MultiMultiStudy, 'multi_multi',
            [DatasetMatch('ss1_x', mrtrix_format, 'ones'),
             DatasetMatch('ss1_y', mrtrix_format, 'ones'),
             DatasetMatch('full_a', mrtrix_format, 'ones'),
             DatasetMatch('full_b', mrtrix_format, 'ones'),
             DatasetMatch('full_c', mrtrix_format, 'ones'),
             DatasetMatch('partial_a', mrtrix_format, 'ones'),
             DatasetMatch('partial_b', mrtrix_format, 'ones'),
             DatasetMatch('partial_c', mrtrix_format, 'ones')],
            options=[Option('partial_ss2_product_op', 'product')])
        self.assertRaises(
            RuntimeError,
            missing_option_study.data,
            'g')
