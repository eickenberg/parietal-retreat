import json
config = json.load(open("config.json"))

from path import path
import os
import nibabel as nb
import cortex


def realign_surface(subject_id):

    src_subj_name = "sub%03d" % subject_id
    pycortex_subj_name = "Henson2010_Sub%02d" % subject_id

    bold_file = (path(config["preprocessed"]) / src_subj_name /
                 "task001_run001").glob("rbold*.nii")[0]

    mean_bold_file_name = os.tmpnam() + ".nii"

    img = nb.load(bold_file)
    aff = img.get_affine()
    mean_data = img.get_data().mean(-1)

    nb.save(nb.Nifti1Image(mean_data, aff), mean_bold_file_name)

    cortex.align.automatic(pycortex_subj_name, 
                           xfmname="xfm001",
                           reference=mean_bold_file_name)

    os.remove(mean_bold_file_name)


if __name__ == "__main__":
    SUBJECTS_DIR = config["SUBJECTS_DIR"]
    import os
    os.environ["SUBJECTS_DIR"] = SUBJECTS_DIR

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--subject-ids", nargs="+")
    args = parser.parse_args()

    subject_ids = (args.subject_ids is not None and
                   [int(sid) for sid in args.subject_ids]) or range(1, 17)

    for subject_id in subject_ids:
        realign_surface(subject_id)
