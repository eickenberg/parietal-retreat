import matplotlib
matplotlib.use('Agg')


import re
import numpy as np
from nipy.modalities.fmri.experimental_paradigm import BlockParadigm
from nipy.modalities.fmri.design_matrix import make_dmtx
from path import path
import nibabel as nb
from nipy.modalities.fmri.glm import FMRILinearModel
from pypreprocess.reporting.glm_reporter import generate_subject_stats_report
from pypreprocess.reporting.base_reporter import ProgressReport, pretty_time

import json

config = json.load(open("config.json"))

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


def do_glm_for_subject(subject_id, bold_base_folder, trial_base_folder,
                       output_base_folder):

    subject_dir = path(bold_base_folder) / ("sub%03d" % subject_id)
    output_dir = (path(output_base_folder) / ("sub%03d" % subject_id) /
                  "model002")
    print output_dir
    if not output_dir.exists():
        output_dir.makedirs()


    anat_file = subject_dir / "highres001.nii"
    anat = nb.load(anat_file)
    run_ids = range(1, 10)

    task_bold_files = [subject_dir.glob("task001_run%03d/rbold*.nii"
                                        % rid)[0]
                       for rid in run_ids]
    task_mvt_files = [subject_dir.glob("task001_run%03d/rp_bold*.txt" % 
                                       rid)[0]
                      for rid in run_ids]

    trial_files = [(path(trial_base_folder) / ("Sub%02d" % subject_id) /
                   "BOLD" / "Trials" / ("run_%02d_spmdef.txt" % rid))
                   for rid in range(1, 10)]
    stats_start_time = pretty_time()
    paradigms = []
    design_matrices = []
    n_scans = []
    all_frametimes = []
    list_of_contrast_dicts = []  # one dict per run

    for i, bold_file, mvt_file, trial_file in zip(run_ids, task_bold_files,
                                                  task_mvt_files,
                                                  trial_files):
        print i
        _n_scans = nb.load(bold_file).shape[-1]
        n_scans.append(_n_scans)
        paradigm = make_paradigm(trial_file)
        paradigms.append(paradigm)
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
                "Tx", "Ty", "Tz", "R1", "R2", "R3"])

        design_matrices.append(design_matrix)
        all_frametimes.append(frametimes)

        # specify contrasts
        contrasts = {}
        n_columns = len(design_matrix.names)
        for ii in xrange(paradigm.n_conditions):
            contrasts['%s' % design_matrix.names[2 * ii]] = np.eye(
                n_columns)[2 * ii]

        # more interesting contrasts"""
        contrasts['Famous-Unfamiliar'] = contrasts[
            'Famous'] - contrasts['Unfamiliar']
        contrasts['Unfamiliar-Famous'] = -contrasts['Famous-Unfamiliar']
        contrasts['Famous-Scrambled'] = contrasts[
            'Famous'] - contrasts['Scrambled']
        contrasts['Scrambled-Famous'] = -contrasts['Famous-Scrambled']
        contrasts['Unfamiliar-Scrambled'] = contrasts[
            'Unfamiliar'] - contrasts['Scrambled']
        contrasts['Scrambled-Unfamiliar'] = -contrasts['Unfamiliar-Scrambled']

        list_of_contrast_dicts = [contrasts]


        # important maps
        z_maps = {}
        effects_maps = {}

        fmri_glm = FMRILinearModel(bold_file,
                                   design_matrix.matrix,
                                   mask="compute")
        fmri_glm.fit(do_scaling=True, model="ar1")

        # replicate contrasts across runs
        contrasts = dict((cid, [contrasts[cid]
                                for contrasts in list_of_contrast_dicts])
                         for cid, cval in contrasts.iteritems())

        # compute effects
        for contrast_id, contrast_val in contrasts.iteritems():
            print "\tcontrast id: %s" % contrast_id
            z_map, eff_map, var_map = fmri_glm.contrast(
                contrast_val,
                con_id=contrast_id,
                output_z=True,
                output_stat=False,
                output_effects=True,
                output_variance=True)

            for map_type, out_map in zip(['z', 'effects', 'variance'],
                                         [z_map, eff_map, var_map]):

                map_dir = output_dir / ("task001_run%03d" % i) / ('%s_maps' % map_type)
                if not map_dir.exists():
                    map_dir.makedirs()
                map_path = map_dir / ('%s.nii.gz' % contrast_id)
                print "\t\tWriting %s ..." % map_path
                nb.save(out_map, map_path)

                # collect zmaps for contrasts we're interested in
                if map_type == 'z':
                    z_maps[contrast_id] = map_path

                if map_type == 'effects':
                    effects_maps[contrast_id] = map_path

                if map_type == "variance":
                    effects_maps[contrast_id] = map_path

        stats_report_dir = output_dir / ("task001_run%03d" % (i)) / "report"
        if not stats_report_dir.exists():
            stats_report_dir.makedirs()

        stats_report_filename = stats_report_dir / "report_stats.html"
        # remove repeated contrasts
        contrasts = dict((cid, cval[0]) for cid, cval in contrasts.iteritems())

        slicer = 'z'
        cut_coords = [-20, -10, 0, 10, 20, 30, 40, 50]
        threshold = 3.
        cluster_th = 15


        generate_subject_stats_report(
            stats_report_filename,
            contrasts,
            z_maps,
            fmri_glm.mask,
            anat_affine=anat.get_affine(),
            anat=anat.get_data(),
            threshold=threshold,
            cluster_th=cluster_th,
            slicer=slicer,
            cut_coords=cut_coords,
            design_matrices=design_matrix,
            subject_id="sub%03d" % subject_id,
            start_time=stats_start_time,
            title="GLM for subject %s" % ("sub%03d" % subject_id),

            # additional ``kwargs`` for more informative report
            TR=tr,
            n_scans=_n_scans,
            hfcut=hfcut,
            drift_model=drift_model,
            hrf_model=hrf_model,
            paradigm=paradigm,
            frametimes=frametimes,
            # fwhm=fwhm
            )

    return fmri_glm


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--subject-ids", nargs="+")

    args = parser.parse_args()
    subject_ids = (args.subject_ids is not None and
                   [int(sid) for sid in args.subject_ids]) or range(1, 17)

    bold_base_folder = config["preprocessed"]
    trial_base_folder = config["fmri_raw"]
    output_base_folder = config["openfmri_dir"]

    for sid in subject_ids:
        res = do_glm_for_subject(sid, bold_base_folder, trial_base_folder,
                                 output_base_folder)


