import numpy as np
import pandas
from path import path
import re


filepattern = r'.*\/sub(\d{3})\/model003\/z_maps\/(.*)_fwhm_(\d\.\d{2})-projfrac-(\d\.\d{2})-([r|l]h)\.gii$'


def collect_giis(openfmri_dir):
    all_giis = sorted((path(openfmri_dir) / "sub*" / "model003" / "z_maps").glob("*.gii"))

    column_names = ["subject",
                    "contrast",
                    "fwhm",
                    "projfrac",
                    "hemi"]

    all_descriptors = []
    for fname in all_giis:
        m = re.search(filepattern, fname)
        if m is not None:
            values = dict(zip(column_names,
                              m.groups()))

            values["filename"] = fname
            all_descriptors.append(values)
        else:
            raise Something

    df = pandas.DataFrame(columns=column_names + ["filename"],
                          index_col=None)

    df = df.append(all_descriptors)

    return df

stc_pattern = r'.*\/Sub(\d{2})/mne_dSPM_inverse-(.*)-([r|l]h).stc'


def collect_stcs(openfmri_dir):

    all_stcs = sorted((path(openfmri_dir) / "stc" / "Sub*").glob("*.stc"))

    column_names = ["subject",
                    "contrast",
                    "hemi"]

    all_stcs = []
    for stc in all_stcs:
        m = re.search(stc_pattern,
                      stc)
        if m is not None:
            
