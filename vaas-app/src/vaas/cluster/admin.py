from django.db import models
from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from django_ace import AceWidget

from vaas.cluster.models import VarnishServer, VclTemplate, VclTemplateBlock, Dc, LogicalCluster
from vaas.cluster.cluster import VarnishApiProvider
from vaas.manager.signals import switch_state_and_reload

ace_widget = AceWidget(theme='solarized_dark', mode='c_cpp', width='700px', height='400px')


def enable_varnish_servers(modeladmin, request, queryset):
    switch_state_and_reload(queryset, True)
enable_varnish_servers.short_description = "Enable varnish servers"


def disable_varnish_servers(modeladmin, request, queryset):
    switch_state_and_reload(queryset, False)
disable_varnish_servers.short_description = "Disable varnish servers"


class VarnishServerAdmin(admin.ModelAdmin):
    search_fields = ['dc__symbol', 'ip', 'hostname', 'template__name']
    list_filter = ['cluster__name']
    list_display = (
        'hostname',
        'ip',
        'port',
        'dc',
        'cluster',
        'cluster_weight',
        'template',
        'template_version',
        'custom_enabled',
        'is_connected',
        'vcl'
    )
    actions = [enable_varnish_servers, disable_varnish_servers]
    varnish_api_provider = None

    def get_list_display(self, request):
        self.varnish_api_provider = VarnishApiProvider()
        return super(VarnishServerAdmin, self).get_list_display(request)

    def template_version(self, obj):
        return obj.template.get_template_version()

    def custom_enabled(self, obj):
        if obj.enabled:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-success' href='#'>" +
                "<i class='icon-ok-circle'></i></a>" +
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini' href='#'><i class='icon-ban-circle'></i></a>" +
                "</div>"
            )
    custom_enabled.short_description = 'Enabled'

    def is_connected(self, obj):
        try:
            self.varnish_api_provider.get_api(obj)
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-success' href='#'><i class='icon-ok'></i></a>" +
                "</div>"
            )
        except:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-danger' href='#'><i class='icon-off'></i></a>" +
                "</div>"
            )

    def vcl(self, obj):
        return format_html(
            ("<div class='span13 text-center'>" +
             "<button class='btn btn-success' data-remote='/manager/varnish/vcl/%s/' " +
             "data-toggle='modal' data-target='#vclModal'>Show vcl</button>" +
             "</div>") % obj.id
        )


class VclTemplateBlockAdmin(SimpleHistoryAdmin):
    formfield_overrides = {
        models.TextField: {'widget': ace_widget},
    }
    list_display = ['tag', 'template']


class VclTemplateAdmin(SimpleHistoryAdmin):
    formfield_overrides = {
        models.TextField: {'widget': ace_widget},
    }
    list_display = ['name', 'version']
    object_history_template = "custom_simple_history/object_history.html"


class LogicalClusterAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'reload_timestamp',
        'error_timestamp',
        'last_error_info',
        'varnish_servers'
    ]
    exclude = ('last_error_info', 'reload_timestamp', 'error_timestamp')

    def varnish_servers(self, obj):
        return format_html(
            ("<div class='span13 text-center'>" +
             "<a class='btn btn-success' href='/admin/cluster/varnishserver/?cluster__name=%s' "
             ">Show varnish servers (%d)</a>" +
             "</div>") % (obj.name, obj.varnish_count())
        )


admin.site.register(VarnishServer, VarnishServerAdmin)
admin.site.register(VclTemplate, VclTemplateAdmin)
admin.site.register(VclTemplateBlock, VclTemplateBlockAdmin)
admin.site.register(Dc)
admin.site.register(LogicalCluster, LogicalClusterAdmin)
