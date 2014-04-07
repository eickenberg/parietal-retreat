import json
import os
import glob
from path import path
from pypreprocess.subject_data import SubjectData


config = json.load(open("config.json"))
openfmri_dir = config["openfmri_dir"]

output_dir = path(openfmri_dir).dirname() / "yannick_pypreprocess"


from pypreprocess.openfmri import preproc_dataset


preproc_dataset(openfmri_dir, output_dir, n_jobs=1)

# subjects = [d.basename() for d in path(openfmri_dir).glob("sub???")]
# data_dir = openfmri_dir


# def subject_factory():
#     for subject_id in subjects:
#         # if subject_id in ignore_subjects:
#         #     continue

#         sessions = set()
#         subject_dir = os.path.join(data_dir, subject_id)
#         for session_dir in glob.glob(os.path.join(
#                 subject_dir, 'BOLD', '*')):
#             sessions.add(os.path.split(session_dir)[1])
#             sessions = sorted(sessions)
#             # construct subject data structure
#             subject_data = SubjectData()
#             subject_data.session_id = sessions
#             subject_data.subject_id = subject_id
#             subject_data.func = []

#             # glob for BOLD data
#             has_bad_sessions = False
#             for session_id in subject_data.session_id:
#                 bold_dir = os.path.join(
#                     data_dir, subject_id, 'BOLD', session_id)

#                 # glob BOLD data for this session
#                 func = glob.glob(os.path.join(bold_dir, "bold.nii.gz"))
#                 # check that this session is OK (has BOLD data, etc.)
#                 if not func:
#                     warnings.warn(
#                         'Subject %s is missing data for session %s.' % (
#                             subject_id, session_id))
#                     has_bad_sessions = True
#                     break

#                 subject_data.func.append(func[0])

#             # exclude subject if necessary
#             if has_bad_sessions:
#                 warnings.warn('Excluding subject %s' % subject_id)
#                 continue

#             # anatomical data
#             subject_data.anat = os.path.join(
#                 data_dir, subject_id, 'anatomy', 'highres001_brain.nii.gz')
#             if not os.path.exists(subject_data.anat):
#                 subject_data.anat = os.path.join(
#                     data_dir, subject_id, 'anatomy', 'highres001.nii.gz')

#             # subject output_dir
#             subject_data.output_dir = os.path.join(output_dir, subject_id)
#             yield subject_data


# if __name__ == "__main__":
#     for sd in subject_factory():
#         print sd

