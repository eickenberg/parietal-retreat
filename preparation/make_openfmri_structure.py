"""Converts Henson Data to OpenfMRI structure"""

from path import path
from nilearn.image import resample_img
from nilearn._utils import concat_niimgs
import nibabel as nb
import json
import shutil


def convert(subject_id, henson_base_dir, output_base_dir, run_ids=None):

    if run_ids is None:
        run_ids = range(1, 10)

    henson_subject_dir = path(henson_base_dir) / ("Sub%02d" % subject_id)
    openfmri_subject_dir = path(output_base_dir) / ("sub%03d" % subject_id)

    # Take all fmri volumes and concatenate them into one
    henson_bold_dir = henson_subject_dir / "BOLD"
    openfmri_bold_dir = openfmri_subject_dir / "BOLD"

    for run_id in run_ids:
        print "run id %d" % run_id
        henson_run_dir = henson_bold_dir / ("Run_%02d" % run_id)
        openfmri_run_dir = openfmri_bold_dir / "task001_run001"
        if not openfmri_run_dir.exists():
            openfmri_run_dir.makedirs()

        henson_run_files = sorted(henson_run_dir.glob(
            "fMR09029-0003-00???-000???-01.nii"))

        concatenated = concat_niimgs(henson_run_files)
        nb.save(concatenated, openfmri_run_dir / "bold.nii.gz")
        keep_filenames_file = openfmri_run_dir / "original_files.json"
        json.dump([hrf.basename() for hrf in henson_run_files],
                  open(keep_filenames_file, "w"))

    # Copy anat file
    henson_anat_file = henson_subject_dir / "T1" / "mprage.nii"
    openfmri_anat_file = (openfmri_subject_dir / "anatomy" /
                          "highres001.nii.gz")
    if not openfmri_anat_file.dirname().exists():
        openfmri_anat_file.dirname().makedirs()
    shutil.copy(henson_anat_file, openfmri_anat_file)


if __name__ == "__main__":
    config = json.load(open("config.json"))

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--subject-ids")

    args = parser.parse_args()
    subject_ids = (args is not None and 
                   [int(sid) for sid in args.subject_ids]) or range(1, 17)

    for subject_id in subject_ids:
        print "Subject id %d" % subject_id
        convert(subject_id, config["fmri_raw"], config["openfmri_dir"])
