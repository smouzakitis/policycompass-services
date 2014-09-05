__author__ = 'fki'

from rest_framework import serializers
from apps.common.serviceadapters import references
from rest_framework.serializers import ValidationError
from .models import RawDataCategory
import datetime
from django.core.exceptions import ObjectDoesNotExist
from .utils import get_rawdata_for_metric


class PolicyDomainsField(serializers.WritableField):

    def field_to_native(self, obj, field_name):
        ids = getattr(obj, self.source).all()
        result = []
        domains = references.PolicyDomain()
        for i in ids:
            result.append(domains.get(i.domain_id))
        return result

    def from_native(self, value):
        if not type(value) is list:
            raise ValidationError("Policy_domains property is not a list")
        return value


class RawDataField(serializers.WritableField):
    def field_to_native(self, obj, field_name):

        # Process Query Paramters
        params = self.context['request'].QUERY_PARAMS
        order = None
        new_sort = []
        if params.get('sort'):
            sort = params.get('sort')
            if sort[:1] == '-':
                order = 'desc'
                sort = sort[1:]
            sort = sort.split(',')

            for s in sort:
                if s == 'from':
                    new_sort.append('from_date')
                elif s == 'to':
                    new_sort.append('to_date')
                else:
                    new_sort.append(s)

        filter = {}
        for p in params:
            if p not in ['sort','format']:
                value_list = params.get(p).split(',')
                if p == 'from':
                    filter['from_date'] = value_list
                elif p == 'to':
                    filter['to_date'] = value_list
                else:
                    filter[p] = value_list

        if params.get('order'):
            order = params.get('order')


        return get_rawdata_for_metric(obj, sort=new_sort, order=order, filter=filter)

    def from_native(self, value):
        if not type(value) is dict:
            raise ValidationError("Wrong datatype")

        if not 'table' in value:
            raise ValidationError("No key table in data")

        if not 'extra_columns' in value:
            raise ValidationError("No key extra_columns in data")

        if not type(value['table']) is list:
            raise ValidationError("Table property is not a list")

        if not type(value['extra_columns']) is list:
            raise ValidationError("Extra Columns property is not a list")

        for e in value['extra_columns']:
            try:
                RawDataCategory.objects.get(title=e)
            except ObjectDoesNotExist:
                raise ValidationError("Invalid Extra Column")

        required_fields = ["to", "from", "value"] + value['extra_columns']
        for r in value['table']:
            if not type(r) is dict:
                raise ValidationError("Table Dict is malformed")

            if not all(k in r for k in required_fields):
                raise ValidationError("Table Dict is malformed, some keys are missing")

            try:
                datetime.datetime.strptime(r['from'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Wrong Date Format")

            try:
                datetime.datetime.strptime(r['to'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Wrong Date Format")

            try:
                float(r['value'])
            except ValueError:
                raise ValidationError("At least one value is not a float")


        return value

    def validate(self, value):
        pass

