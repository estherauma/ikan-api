from django import template
from common.utils import format_local_date

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key, None)


@register.filter
def filter_and_get_value(array, args):
    """
    Find object with key_name == key_value, return another property. Similar to array.find() in JS.

    :param array: array of objects
    :param args: comma separated string ("key_name,key_value,return_attr"), first value is the attribute name, second value is the value to match, third value is the attribute to return
    :return: value of the return_property

    Usage:
        {{ list|filter_and_get_value:"key_name,key_value,return_attr" }}
    Example:
        {{ people|filter_and_get_value:"role,editor,name" }}
        {{ people|filter_and_get_value:"role,editor,age" }}
    Description:
        Returns the value of 'return_attr' where 'key_name' == 'key_value'
    """
    try:
        key_name, key_value, return_attr = [part.strip() for part in args.split(',')]
    except ValueError:
        return None

    for obj in array:
        if obj[key_name] == key_value:
            return obj[return_attr]

    return None


@register.filter
def format_date(date):
    """
    Format a date object to a localized string.

    :param date: datetime object
    :return: formatted date string

    Usage:
        {{ date|format_date }}
    Description:
        Formats a datetime object to a localized string based on the current language settings.
    """
    # TODO: add sesseion language after language switching is implemented ie format_local_date(date, selected_language)
    return format_local_date(date)
