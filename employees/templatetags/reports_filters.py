import json

from django import template

register = template.Library()


def _labels(value):
    return [x.get('label', '') for x in value]


def _values(value):
    return [x.get('value', 0) for x in value]


@register.filter
def map_label(value):
    return json.dumps(_labels(value))


@register.filter
def map_value(value):
    return json.dumps(_values(value))


@register.filter
def map_attr_present(value):
    return json.dumps([x.get('present', 0) for x in value])


@register.filter
def map_attr_absent(value):
    return json.dumps([x.get('absent', 0) for x in value])


@register.filter
def map_attr_half(value):
    return json.dumps([x.get('half_day', 0) for x in value])