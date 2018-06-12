from arcana.testing import BaseTestCase, TestMath
from arcana.interfaces.utils import Merge
from arcana.dataset import DatasetMatch, DatasetSpec
from arcana.file_format import text_format
from arcana.parameter import ParameterSpec
from arcana.study.base import Study
from arcana.study.multi import (
    MultiStudy, SubStudySpec, MultiStudyMetaClass, StudyMetaClass)
from arcana.parameter import Parameter
from future.utils import with_metaclass


class StudyA(with_metaclass(StudyMetaClass, Study)):

    add_data_specs = [
        DatasetSpec('x', text_format),
        DatasetSpec('y', text_format),
        DatasetSpec('z', text_format, 'pipeline_alpha')]

    add_parameter_specs = [
        ParameterSpec('o1', 1),
        ParameterSpec('o2', '2'),
        ParameterSpec('o3', 3.0)]

    def pipeline_alpha(self, **kwargs):  # @UnusedVariable
        pipeline = self.create_pipeline(
            name='pipeline_alpha',
            inputs=[DatasetSpec('x', text_format),
                    DatasetSpec('y', text_format)],
            outputs=[DatasetSpec('z', text_format)],
            desc="A dummy pipeline used to test MultiStudy class",
            version=1,
            citations=[],
            **kwargs)
        math = pipeline.create_node(TestMath(), name="math")
        math.inputs.op = 'add'
        math.inputs.as_file = True
        # Connect inputs
        pipeline.connect_input('x', math, 'x')
        pipeline.connect_input('y', math, 'y')
        # Connect outputs
        pipeline.connect_output('z', math, 'z')
        return pipeline


class StudyB(with_metaclass(StudyMetaClass, Study)):

    add_data_specs = [
        DatasetSpec('w', text_format),
        DatasetSpec('x', text_format),
        DatasetSpec('y', text_format, 'pipeline_beta'),
        DatasetSpec('z', text_format, 'pipeline_beta')]

    add_parameter_specs = [
        ParameterSpec('o1', 10),
        ParameterSpec('o2', '20'),
        ParameterSpec('o3', 30.0),
        ParameterSpec('product_op', 'not-specified')]  # Needs to be set to 'product' @IgnorePep8

    def pipeline_beta(self, **kwargs):  # @UnusedVariable
        pipeline = self.create_pipeline(
            name='pipeline_beta',
            inputs=[DatasetSpec('w', text_format),
                    DatasetSpec('x', text_format)],
            outputs=[DatasetSpec('y', text_format),
                     DatasetSpec('z', text_format)],
            desc="A dummy pipeline used to test MultiStudy class",
            version=1,
            citations=[],
            **kwargs)
        add1 = pipeline.create_node(TestMath(), name="add1")
        add2 = pipeline.create_node(TestMath(), name="add2")
        prod = pipeline.create_node(TestMath(), name="product")
        add1.inputs.op = 'add'
        add2.inputs.op = 'add'
        prod.inputs.op = pipeline.parameter('product_op')
        add1.inputs.as_file = True
        add2.inputs.as_file = True
        prod.inputs.as_file = True
        # Connect inputs
        pipeline.connect_input('w', add1, 'x')
        pipeline.connect_input('x', add1, 'y')
        pipeline.connect_input('x', add2, 'x')
        # Connect nodes
        pipeline.connect(add1, 'z', add2, 'y')
        pipeline.connect(add1, 'z', prod, 'x')
        pipeline.connect(add2, 'z', prod, 'y')
        # Connect outputs
        pipeline.connect_output('y', add2, 'z')
        pipeline.connect_output('z', prod, 'z')
        return pipeline


class FullMultiStudy(with_metaclass(MultiStudyMetaClass, MultiStudy)):

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
        DatasetSpec('a', text_format),
        DatasetSpec('b', text_format),
        DatasetSpec('c', text_format),
        DatasetSpec('d', text_format, 'pipeline_alpha_trans'),
        DatasetSpec('e', text_format, 'pipeline_beta_trans'),
        DatasetSpec('f', text_format, 'pipeline_beta_trans')]

    add_parameter_specs = [
        ParameterSpec('p1', 100),
        ParameterSpec('p2', '200'),
        ParameterSpec('p3', 300.0),
        ParameterSpec('q1', 150),
        ParameterSpec('q2', '250'),
        ParameterSpec('required_op', 'still-not-specified')]

    pipeline_alpha_trans = MultiStudy.translate(
        'ss1', 'pipeline_alpha')
    pipeline_beta_trans = MultiStudy.translate(
        'ss2', 'pipeline_beta')


class PartialMultiStudy(with_metaclass(MultiStudyMetaClass, MultiStudy)):

    add_sub_study_specs = [
        SubStudySpec('ss1', StudyA,
                     {'a': 'x', 'b': 'y', 'p1': 'o1'}),
        SubStudySpec('ss2', StudyB,
                     {'b': 'w', 'c': 'x', 'p1': 'o1'})]

    add_data_specs = [
        DatasetSpec('a', text_format),
        DatasetSpec('b', text_format),
        DatasetSpec('c', text_format)]

    pipeline_alpha_trans = MultiStudy.translate(
        'ss1', 'pipeline_alpha')

    add_parameter_specs = [
        ParameterSpec('p1', 1000)]


class MultiMultiStudy(with_metaclass(MultiStudyMetaClass, MultiStudy)):

    add_sub_study_specs = [
        SubStudySpec('ss1', StudyA, {}),
        SubStudySpec('full', FullMultiStudy),
        SubStudySpec('partial', PartialMultiStudy)]

    add_data_specs = [
        DatasetSpec('g', text_format, 'combined_pipeline')]

    add_parameter_specs = [
        ParameterSpec('combined_op', 'add')]

    def combined_pipeline(self, **kwargs):
        pipeline = self.create_pipeline(
            name='combined',
            inputs=[DatasetSpec('ss1_z', text_format),
                    DatasetSpec('full_e', text_format),
                    DatasetSpec('partial_ss2_z', text_format)],
            outputs=[DatasetSpec('g', text_format)],
            desc=(
                "A dummy pipeline used to test MultiMultiStudy class"),
            version=1,
            citations=[],
            **kwargs)
        merge = pipeline.create_node(Merge(3), name="merge")
        math = pipeline.create_node(TestMath(), name="math")
        math.inputs.op = pipeline.parameter('combined_op')
        math.inputs.as_file = True
        # Connect inputs
        pipeline.connect_input('ss1_z', merge, 'in1')
        pipeline.connect_input('full_e', merge, 'in2')
        pipeline.connect_input('partial_ss2_z', merge, 'in3')
        # Connect nodes
        pipeline.connect(merge, 'out', math, 'x')
        # Connect outputs
        pipeline.connect_output('g', math, 'z')
        return pipeline


class TestMulti(BaseTestCase):

    INPUT_DATASETS = {'ones': '1'}

    def test_full_multi_study(self):
        study = self.create_study(
            FullMultiStudy, 'full',
            [DatasetMatch('a', text_format, 'ones'),
             DatasetMatch('b', text_format, 'ones'),
             DatasetMatch('c', text_format, 'ones')],
            parameters=[Parameter('required_op', 'mul')])
        d, e, f = study.data(('d', 'e', 'f'),
                             subject_id='SUBJECT', visit_id='VISIT')
        self.assertContentsEqual(d, 2.0)
        self.assertContentsEqual(e, 3.0)
        self.assertContentsEqual(f, 6.0)
        # Test parameter values in MultiStudy
        self.assertEqual(study._get_parameter('p1').value, 100)
        self.assertEqual(study._get_parameter('p2').value, '200')
        self.assertEqual(study._get_parameter('p3').value, 300.0)
        self.assertEqual(study._get_parameter('q1').value, 150)
        self.assertEqual(study._get_parameter('q2').value, '250')
        self.assertEqual(study._get_parameter('required_op').value, 'mul')
        # Test parameter values in SubStudy
        ss1 = study.sub_study('ss1')
        self.assertEqual(ss1._get_parameter('o1').value, 100)
        self.assertEqual(ss1._get_parameter('o2').value, '200')
        self.assertEqual(ss1._get_parameter('o3').value, 300.0)
        ss2 = study.sub_study('ss2')
        self.assertEqual(ss2._get_parameter('o1').value, 150)
        self.assertEqual(ss2._get_parameter('o2').value, '250')
        self.assertEqual(ss2._get_parameter('o3').value, 300.0)
        self.assertEqual(ss2._get_parameter('product_op').value, 'mul')

    def test_partial_multi_study(self):
        study = self.create_study(
            PartialMultiStudy, 'partial',
            [DatasetMatch('a', text_format, 'ones'),
             DatasetMatch('b', text_format, 'ones'),
             DatasetMatch('c', text_format, 'ones')],
            parameters=[Parameter('ss2_product_op', 'mul')])
        ss1_z = study.data('ss1_z',
                           subject_id='SUBJECT', visit_id='VISIT')
        ss2_y = study.data('ss2_y')[0]
        ss2_z = study.data('ss2_z')[0]
        self.assertContentsEqual(ss1_z, 2.0)
        self.assertContentsEqual(ss2_y, 3.0)
        self.assertContentsEqual(ss2_z, 6.0)
        # Test parameter values in MultiStudy
        self.assertEqual(study._get_parameter('p1').value, 1000)
        self.assertEqual(study._get_parameter('ss1_o2').value, '2')
        self.assertEqual(study._get_parameter('ss1_o3').value, 3.0)
        self.assertEqual(study._get_parameter('ss2_o2').value, '20')
        self.assertEqual(study._get_parameter('ss2_o3').value, 30.0)
        self.assertEqual(study._get_parameter('ss2_product_op').value, 'mul')
        # Test parameter values in SubStudy
        ss1 = study.sub_study('ss1')
        self.assertEqual(ss1._get_parameter('o1').value, 1000)
        self.assertEqual(ss1._get_parameter('o2').value, '2')
        self.assertEqual(ss1._get_parameter('o3').value, 3.0)
        ss2 = study.sub_study('ss2')
        self.assertEqual(ss2._get_parameter('o1').value, 1000)
        self.assertEqual(ss2._get_parameter('o2').value, '20')
        self.assertEqual(ss2._get_parameter('o3').value, 30.0)
        self.assertEqual(ss2._get_parameter('product_op').value, 'mul')

    def test_multi_multi_study(self):
        study = self.create_study(
            MultiMultiStudy, 'multi_multi',
            [DatasetMatch('ss1_x', text_format, 'ones'),
             DatasetMatch('ss1_y', text_format, 'ones'),
             DatasetMatch('full_a', text_format, 'ones'),
             DatasetMatch('full_b', text_format, 'ones'),
             DatasetMatch('full_c', text_format, 'ones'),
             DatasetMatch('partial_a', text_format, 'ones'),
             DatasetMatch('partial_b', text_format, 'ones'),
             DatasetMatch('partial_c', text_format, 'ones')],
            parameters=[Parameter('full_required_op', 'mul'),
                     Parameter('partial_ss2_product_op', 'mul')])
        g = study.data('g')[0]
        self.assertContentsEqual(g, 11.0)
        # Test parameter values in MultiStudy
        self.assertEqual(study._get_parameter('full_p1').value, 100)
        self.assertEqual(study._get_parameter('full_p2').value, '200')
        self.assertEqual(study._get_parameter('full_p3').value, 300.0)
        self.assertEqual(study._get_parameter('full_q1').value, 150)
        self.assertEqual(study._get_parameter('full_q2').value, '250')
        self.assertEqual(study._get_parameter('full_required_op').value,
                         'mul')
        # Test parameter values in SubStudy
        ss1 = study.sub_study('full').sub_study('ss1')
        self.assertEqual(ss1._get_parameter('o1').value, 100)
        self.assertEqual(ss1._get_parameter('o2').value, '200')
        self.assertEqual(ss1._get_parameter('o3').value, 300.0)
        ss2 = study.sub_study('full').sub_study('ss2')
        self.assertEqual(ss2._get_parameter('o1').value, 150)
        self.assertEqual(ss2._get_parameter('o2').value, '250')
        self.assertEqual(ss2._get_parameter('o3').value, 300.0)
        self.assertEqual(ss2._get_parameter('product_op').value, 'mul')
        # Test parameter values in MultiStudy
        self.assertEqual(study._get_parameter('partial_p1').value, 1000)
        self.assertEqual(study._get_parameter('partial_ss1_o2').value, '2')
        self.assertEqual(study._get_parameter('partial_ss1_o3').value, 3.0)
        self.assertEqual(study._get_parameter('partial_ss2_o2').value, '20')
        self.assertEqual(study._get_parameter('partial_ss2_o3').value, 30.0)
        self.assertEqual(
            study._get_parameter('partial_ss2_product_op').value, 'mul')
        # Test parameter values in SubStudy
        ss1 = study.sub_study('partial').sub_study('ss1')
        self.assertEqual(ss1._get_parameter('o1').value, 1000)
        self.assertEqual(ss1._get_parameter('o2').value, '2')
        self.assertEqual(ss1._get_parameter('o3').value, 3.0)
        ss2 = study.sub_study('partial').sub_study('ss2')
        self.assertEqual(ss2._get_parameter('o1').value, 1000)
        self.assertEqual(ss2._get_parameter('o2').value, '20')
        self.assertEqual(ss2._get_parameter('o3').value, 30.0)
        self.assertEqual(ss2._get_parameter('product_op').value, 'mul')

    def test_missing_parameter(self):
        # Misses the required 'full_required_op' parameter, which sets
        # the operation of the second node in StudyB's pipeline to
        # 'product'
        missing_parameter_study = self.create_study(
            MultiMultiStudy, 'multi_multi',
            [DatasetMatch('ss1_x', text_format, 'ones'),
             DatasetMatch('ss1_y', text_format, 'ones'),
             DatasetMatch('full_a', text_format, 'ones'),
             DatasetMatch('full_b', text_format, 'ones'),
             DatasetMatch('full_c', text_format, 'ones'),
             DatasetMatch('partial_a', text_format, 'ones'),
             DatasetMatch('partial_b', text_format, 'ones'),
             DatasetMatch('partial_c', text_format, 'ones')],
            parameters=[Parameter('partial_ss2_product_op', 'mul')])
        self.assertRaises(
            RuntimeError,
            missing_parameter_study.data,
            'g')
