import json
import cortex

config = json.load(open("config.json"))


def surface_to_store(subject_id):

    source_subject_name = "Sub%02d" % subject_id
    target_subject_name = "Henson2010_%s" % source_subject_name

    print "%s imported as %s" % (source_subject_name, target_subject_name)

    cortex.freesurfer.import_subj(source_subject_name,
                                  sname=target_subject_name)





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
        surface_to_store(subject_id)
