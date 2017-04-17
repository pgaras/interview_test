# Authored by Peter Garas for Ocom Software

from datetime import datetime
from rest_framework.authentication import BasicAuthentication


def get_project_permissions(user):
    group_permissions = user.get_group_permissions()
    valid_perms = ['api.change_project', 'api.delete_project', 'api.add_project']
    intersect = set(valid_perms).intersection(group_permissions)
    return len(intersect) == 3


def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return False
    else:
        return True


def validate_date_entries(data):
    date_field_keys = ['active_start_date', 'active_end_date']

    for field_key in date_field_keys:
        date_field = data.get(field_key)

        if date_field is not None:
            if not validate_date(date_field):
                return False, {"detail": "Invalid format for {}: must be \"YYYY-mm-dd\"".format(field_key)}

    return True, {}


def get_param_flags(param):
    if param.lower() == 'true':
        inside = True
        outside = False
    elif param.lower() == 'false':
        inside = False
        outside = False
    else:
        inside = False
        outside = True

    return inside, outside


class QuietBasicAuthentication(BasicAuthentication):
    def authenticate_header(self, request):
        return 'xBasic realm="{}"'.format(self.www_authenticate_realm)
