import sublime
import sublime_plugin

g_widget_view = None
g_is_panel_focused = False
g_is_widget_focused = False


def is_panel_focused():
    return g_is_widget_focused


class HackListener(sublime_plugin.EventListener):

    def on_new(self, view):
        # print('on_new', view.buffer_id())

        if not view.file_name():
            view.settings().set('is_new_file', True)

    def on_activated(self, view):
        global g_widget_view
        global g_is_panel_focused
        global g_is_widget_focused

        g_widget_view = view
        active_window = sublime.active_window()
        view_has_name = not not view.file_name() or view.settings().get('is_new_file')

        g_is_widget_focused = view.settings().get('is_widget')
        active_panel = active_window.active_panel()
        g_is_panel_focused = active_panel and not view_has_name and not g_is_widget_focused

        # print( "view_has_name:", view_has_name )
        # print( "g_is_widget_focused:", g_is_widget_focused )
        # print( "g_is_panel_focused:", g_is_panel_focused )


# https://github.com/SublimeTextIssues/Core/issues/2914
class FixedToggleFindPanelCommand(sublime_plugin.WindowCommand):

    def run(self, command, args={}):
        window = self.window
        active_group = window.active_group()
        active_panel = window.active_panel()

        focused_widget = g_widget_view
        panel_had_focus = g_is_panel_focused
        widget_had_focus = g_is_widget_focused

        # print('panel_had_focus', panel_had_focus)
        # print('widget_had_focus', widget_had_focus)
        self.window.run_command( "show_panel", { "panel": "find", "reverse": False } )
        self.window.run_command( command, args )

        # print('FixedToggleFindPanel running', command, args)
        sublime.status_message( "Successfully toggled the setting '%s'" % command )

        if active_panel:
            self.window.run_command( "show_panel", { "panel": active_panel } )

            if panel_had_focus:
                panel_view = get_panel_view( window, active_panel )
                self.window.focus_view( panel_view )

            elif widget_had_focus and focused_widget:
                self.window.focus_view( focused_widget )

            else:
                self.window.focus_group( active_group )

        else:
            self.window.run_command( "hide_panel" )

            if widget_had_focus and focused_widget:
                self.window.focus_view( focused_widget )

