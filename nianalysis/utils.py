import os.path
from nianalysis.exceptions import NiAnalysisError


zip_exts = ('gz', 'zip')

package_dir = os.path.join(os.path.dirname(__file__), '..')


def get_atlas_path(name, dataset='image'):
    """
    Returns the path to the atlas (or atlas mask) in the nianalysis repository

    Parameters
    ----------
    name : str
        Name of the Atlas, can be one of ('mni_nl6')
    atlas_type : str
        Whether to return the brain mask or the full atlas, can be one of
        'image', 'mask'
    """
    if name == 'mni_nl6':
        # MNI ICBM 152 non-linear 6th Generation Symmetric Average Brain
        # Stereotaxic Registration Model (http://nist.mni.mcgill.ca/?p=858)
        base_path = os.path.join(package_dir, 'reference', 'atlases',
                                 'mni_nl6')
        if dataset == 'image':
            path = os.path.join(base_path,
                                'icbm_avg_152_t1_tal_nlin_symmetric_VI.mnc')
        elif dataset == 'mask':
            path = os.path.join(
                base_path, 'icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.mnc')
        else:
            raise NiAnalysisError("Unrecognised dataset '{}'"
                                  .format(dataset))
    else:
        raise NiAnalysisError("Unrecognised atlas name '{}'"
                              .format(name))
    return path


def split_extension(path):
    """
    A extension splitter that checks for compound extensions such as
    'file.nii.gz'

    Parameters
    ----------
    filename : str
        A filename to split into base and extension

    Returns
    -------
    base : str
        The base part of the string, i.e. 'file' of 'file.nii.gz'
    ext : str
        The extension part of the string, i.e. 'nii.gz' of 'file.nii.gz'
    """
    dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    parts = filename.split('.')
    if len(parts) == 1:
        base = filename
        ext = None
    else:
        if parts[-1] in zip_exts:
            num_ext_parts = 2
        else:
            num_ext_parts = 1
        ext = '.' + '.'.join(parts[-num_ext_parts:])
        base = '.'.join(parts[:-num_ext_parts])
    return os.path.join(dirname, base), ext


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()
