import mne
from surfer.utils import smoothing_matrix, mesh_edges
import os
from nibabel import freesurfer
from path import path
import numpy as np
import nibabel as nb


def upsample_stc_map(stc_file_prefix, subject_id, smoothing_steps=10,
                     subjects_dir=None):

    if subjects_dir is None:
        subjects_dir = os.environ["SUBJECTS_DIR"]

    stc = mne.read_source_estimate(stc_file_prefix)

    fs_sub_name = "Sub%02d" % subject_id

    lh_vert, lh_triag = freesurfer.load(path(subjects_dir) / fs_sub_name /
                                      "lh.orig")
    rh_vert, rh_triag = freesurfer.load(path(subjects_dir) / fs_sub_name /
                                      "rh.orig")

    lh_adj = mesh_edges(lh_triag)
    rh_adj = mesh_edges(rh_triag)

    lh_smoothing_mat = smoothing_matrix(stc.lh_vertno, lh_adj,
                                        smoothing_steps=smoothing_steps)
    rh_smoothing_mat = smoothing_matrix(stc.rh_vertno, rh_adj,
                                        smoothing_steps=smoothing_steps)

    lh_upsampled = lh_smoothing_mat.dot(stc.lh_data).ravel()
    rh_upsampled = rh_smoothing_mat.dot(stc.rh_data).ravel()

    lh_out_file = stc_file_prefix + "-upsampled-lh.mgz"
    rh_out_file = stc_file_prefix + "-upsampled-rh.mgz"

    freesurfer.save(nb.Nifti1Image(lh_upsampled[:, np.newaxis, np.newaxis],
                    affine=np.eye(4)), lh_out_file)

    freesurfer.save(nb.Nifti1Image(rh_upsampled[:, np.newaxis, np.newaxis],
                    affine=np.eye(4)), rh_out_file)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--subject-ids", nargs="+")

    args = parser.parse_args()

    subject_ids = (args.subject_ids is not None and
                   [int(sid) for sid in args.subject_ids]) or range(1, 17)

    stcs_dir = "/home/me232320/data/parietal_retreat/stcs"
    for subject_id in subject_ids:
        stc_files = (path(stcs_dir) / ("Sub%02d" % subject_id)).glob("*.stc")
        stc_roots = np.unique([stc_file[:-7] for stc_file in stc_files])

        for stc_root in stc_roots:
            print subject_id
            print stc_root
            upsample_stc_map(stc_root, subject_id)

