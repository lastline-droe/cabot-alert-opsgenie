__author__ = '\n     ~\n    . .\n    /V\\\n   // \\\\\n  /(___)\\\n   ^ ~ ^\nd i b i t s'
# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.template import Context, Template

from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData

from os import environ as env
import requests
import json

opsgenie_template = "Service {{ service.name }} {% if service.overall_status == service.PASSING_STATUS %}is back to normal{% else %}reporting {{ service.overall_status }} status{% endif %}: {{ scheme }}://{{ host }}{% url 'service' pk=service.id %}."


class OpsGenieAlert(AlertPlugin):
    name = 'OpsGenie'
    author = 'dibits'

    def send_alert(self, service, users, duty_officers):
        for user in users:
            alert = True
            priority = 1
            try:
                data = AlertPluginUserData.objects.get(user=user, title=OpsGenieAlertUserData.name)
            except:
                pass

            if service.overall_status == service.WARNING_STATUS:
                if not data.alert_on_warn:
                    alert = False
                    priority = 0
            elif service.overall_status == service.ERROR_STATUS:
                priority = 1
            elif service.overall_status == service.CRITICAL_STATUS:
                priority = 2
            elif service.overall_status == service.PASSING_STATUS:
                priority = 0
                if service.old_overall_status == service.CRITICAL_STATUS:
                    pass
            else:
                alert = False

            if not alert:
                return

            c = Context({
                'service': service,
                'host': settings.WWW_HTTP_HOST,
                'scheme': settings.WWW_SCHEME,
                })

            message = Template(opsgenie_template).render(c)

            self._send_opsgenie_alert(message, user_or_group=data.user_or_group, priority=priority, service=service)

    def _send_opsgenie_alert(self, message, user_or_group, service, priority=0):
        opsgenie_url = 'https://api.opsgenie.com/v1/json/alert'
        headers = {'content-type': 'application/json'}

        payload = {
            'apiKey': env['OPSGENIE_KEY'],
            'alias': service.name,
            }

        if priority > 0:
            payload['recipients'] = user_or_group
            payload['message'] = message
        else:
            payload['notify'] = user_or_group
            payload['note'] = message
            opsgenie_url += '/close'

        requests.post(opsgenie_url, data=json.dumps(payload), headers=headers)

        return


class OpsGenieAlertUserData(AlertPluginUserData):
    name = "OpsGenie Plugin"
    user_or_group = models.CharField(max_length=50, blank=True, verbose_name='OpsGenie User/Group')