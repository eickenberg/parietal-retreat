from surfer.io import project_volume_data
from path import path
from nibabel import gifti
import nibabel as nb

def project_z_map(in_file, subject, hemi, proj_frac, fsaverage_fwhm=3.):

    out_dir = path(in_file).dirname()
    out_base = path(in_file).basename()
    if out_base[-3:] == ".gz":
        out_base = out_base[:-3]
    if out_base[-4:] == ".nii":
        out_base = out_base[:-4]
    else:
        raise Exception("problem with infile name %s" % infile)

    out_file_name = out_dir / (out_base + "-projfrac-%1.2f-%s.gii"
                               % (proj_frac, hemi))
    print out_file_name
    out_file_fsaverage = out_dir / ("avg_%s-projfrac-%1.2f-%s.gii"
                                    % (out_base, proj_frac, hemi))
    print out_file_fsaverage
    out_data = project_volume_data(in_file, hemi, subject_id=subject,
                              projmeth="frac", projarg=proj_frac,
                                   projsum="point")
    out_data_avg = project_volume_data(in_file, hemi, subject_id=subject,
                                  projmeth="frac", projarg=proj_frac,
                                  target_subject="fsaverage",
                                  smooth_fwhm=fsaverage_fwhm,
                                       projsum="point")

    gii_arr = gifti.GiftiDataArray.from_array(out_data, 0)
    out_gii = gifti.GiftiImage(darrays=[gii_arr])

    gii_arr_avg = gifti.GiftiDataArray.from_array(out_data_avg, 0)
    out_gii_avg = gifti.GiftiImage(darrays=[gii_arr_avg])

    gifti.write(out_gii, out_file_name)
    gifti.write(out_gii_avg, out_file_fsaverage)


if __name__ == "__main__":
    import json
    config = json.load(open("config.json"))
    basedir = config["openfmri_dir"]

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--subject-ids", nargs="+")
    args = parser.parse_args()
    subject_ids = (args.subject_ids is not None and
                   [int(sid) for sid in args.subject_ids]) or range(1, 17)

    hemis = ["lh", "rh"]
    proj_fracs = [0.5, 0.1, 0.9]

    import os
    tmpname = os.tmpnam() + ".nii"

    for subject_id in subject_ids:
        openfmri_subj_name = "sub%03d" % subject_id
        fs_subj_name = "Sub%02d" % subject_id
        files = (path(basedir) / openfmri_subj_name / "model003" /
                         "z_maps").glob("*.nii.gz")
        for fname in files:
            for hemi in hemis:
                for proj_frac in proj_fracs:
                    print fname
                    print hemi
                    print proj_frac
                    # if fname[-3:] == ".gz":
                    #     nb.save(nb.load(fname), tmpname)
                    #     fname2 = tmpname
                    # else:
                    #     fname2 = fname
                    project_z_map(fname, fs_subj_name, hemi, proj_frac)

# os.remove(tmpname)

