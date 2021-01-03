def get_info_part(path_string, field_to_search):
    start_ind = path_string.find(f'{field_to_search}="')

    if start_ind == -1:
        return None

    addition = 2 + len(field_to_search)
    end_ind = path_string.find('"', start_ind + addition)
    return path_string[start_ind + addition:end_ind]
