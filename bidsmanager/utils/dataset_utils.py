

def anonymize_dataset(dataset, id_length=2):
    # todo: implement shuffling
    for i, subject in enumerate(dataset.get_subjects()):
        subject.set_name("{0:0{1}d}".format(i + 1, id_length))
        for ii, session_name in enumerate(sorted(subject.get_session_names())):
            session = subject.get_session(session_name)
            session.set_name("{0:0{1}d}".format(ii + 1, id_length))

    return dataset
