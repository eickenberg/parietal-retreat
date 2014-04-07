import re
import numpy as np
from nipy.modalities.fmri.experimental_paradigm import BlockParadigm
from nipy.modalities.fmri.design_matrix import make_dmtx
from path import path
import nibabel as nb
from nipy.modalities.fmri.glm import FMRILinearModel

preprocessed_dir = config["preprocessed"]


def make_paradigm(filename, **kwargs):
    """
    Constructs design paradigm from run_*_spmdef.txt file

    """

    text = open(filename).read()
    conditions = []
    onsets = []
    durations = []
    for item in re.finditer(
        "(?P<condition>(?:Unfamiliar|Scrambled|Famous))\t+?"
        "(?P<onset>\S+)\t+?(?P<duration>\S+)",
        text):
        conditions.append(item.group("condition"))
        onsets.append(float(item.group("onset")))
        durations.append(float(item.group("duration")))

    return BlockParadigm(con_id=conditions, onset=onsets,
                         duration=durations,
                         amplitude=np.ones(len(conditions)),
                         **kwargs)


def do_glm_for_subject(subject_id, bold_base_folder, trial_base_folder):

    subject_dir = path(bold_base_folder) / ("sub%03d" % subject_id)

    task_bold_files = [subject_dir / ("task001_run%03d/rbold.nii" % rid)
                       for rid in range(1, 10)]
    task_mvt_files = [subject_dir / ("task001_run%03d/rp_bold.txt" % rid)
                      for rid in range(1, 10)]

    trial_files = [(path(trial_base_folder) / ("Sub%02d" % subject_id) /
                   "BOLD" / ("run_%02d_spmdef.txt" % rid))
                   for rid in range(1, 10)]

    paradigms = []
    design_matrices = []
    n_scans = []
    all_frametimes = []
    for bold_file, mvt_file, trial_file in zip(task_bold_files, 
                                               task_mvt_files,
                                               trial_files):

        _n_scans = nb.load(bold_file).shape[-1]
        n_scans.append(_n_scans)
        paradigm = make_paradigm(trial_file)
        movements = np.loadtxt(mvt_file)

        tr = 2.
        drift_model = "Cosine"
        hrf_model = "Canonical With Derivative"
        hfcut = 128.

        frametimes = np.linspace(0, (_n_scans - 1) * tr, _n_scans)

        design_matrix = make_dmtx(
            frametimes,
            paradigm,
            hrf_model=hrf_model,
            drift_model=drift_model,
            hfcut=hfcut,
            add_regs=movements,
            add_reg_names=[
                "Tx, Ty, Tz, R1, R2, R3"])

        design_matrices.append(design_matrix)
        all_frametimes.append(frametimes)

    fmri_glm = FMRILinearModel(task_bold_files,
                               [dm.matrix for dm in design_matrices],
                               mask="compute")
    fmri_glm.fit(do_scaling=True, model="ar1")

    return fmri_glm


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--subject-ids", nargs="+")

    args = parser.parse_args()
    subject_ids = (args.subject_ids is not None and
                   [int(sid) for sid in args.subject_ids]) or range(1, 17)

    import json
    config = json.load(open(config.json))
    bold_base_folder = config["preprocessed"]
    trial_base_folder = config["fmri_raw"]

    for sid in subject_ids:
        res = do_glm_for_subject(sid, bold_base_folder, trial_base_folder)


