import numpy as np
import pandas
from path import path
import re


filepattern = r'.*\/sub(\d{3})\/model003\/z_maps\/(.*)_fwhm_(\d\.\d{2})-projfrac-(\d\.\d{2})-([r|l]h)\.gii'


def collect_giis(openfmri_dir):
    all_giis = sorted((path(openfmri_dir) / "sub*" / "model003" / "z_maps").glob("*.gii"))

    column_names = ["contrast",
]
