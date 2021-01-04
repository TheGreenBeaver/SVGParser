def get_info_part(path_string, field_to_search):
    start_ind = path_string.find(f'{field_to_search}="')

    if start_ind == -1:
        return None

    addition = 2 + len(field_to_search)
    end_ind = path_string.find('"', start_ind + addition)
    return path_string[start_ind + addition:end_ind]


def calc_bezier(start_pt, batch, t, order):
    if order == 3:
        p1 = (1 - t) ** 3 * start_pt
        p2 = 3 * (1 - t) ** 2 * t * batch[0]
        p3 = 3 * (1 - t) * t ** 2 * batch[1]
        p4 = t ** 3 * batch[2]

        return p1 + p2 + p3 + p4

    if order == 2:
        p1 = (1 - t) ** 2 * start_pt
        p2 = 2 * (1 - t) * t * batch[0]
        p3 = t ** 2 * batch[1]

        return p1 + p2 + p3


def print_oops(reason, path_id):
    print(f'Sorry! This app can\'t yet process the {reason} (in path {path_id}); the result might not be complete.'
          f' We are open for your suggestions at https://github.com/TheGreenBeaver/SVGParser!')
