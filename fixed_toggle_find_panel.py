import sys

import sublime
import sublime_plugin

g_widget_view = None
g_is_panel_focused = False
g_is_widget_focused = False

g_toggle_comands = (
    'toggle_wrap',
    'toggle_in_selection',
    'toggle_highlight',
    'toggle_show_context',
    'toggle_use_buffer',
    'toggle_case_sensitive',
    'toggle_regex',
    'toggle_whole_word',
    'toggle_preserve_case',
)


def is_panel_focused():
    return g_is_panel_focused


def widget_view():
    return g_widget_view


# https://forum.sublimetext.com/t/why-do-i-call-show-panel-with-output-exec-but-need-to-call-window-find-output-panel-exec-instead-of-window-find-output-panel-output-exec/45739
def get_panel_name(panel_name):
    return panel_name[len("output."):] if panel_name.startswith("output.") else panel_name


def get_panel_view(window, panel_name):
    return window.find_output_panel( panel_name ) or \
            window.find_output_panel( get_panel_name( panel_name ) )


class State(object):
    preview_on_click = False

    is_running_focus_side_bar = False
    is_running_fixed_toggle_find_panel = False


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

    # def on_text_command(self, view, command_name, args):
    #     print('view command_name', command_name, args)

    def on_window_command(self, window, command_name, args):
        # print('window command_name', command_name, args)

        if command_name == 'focus_side_bar':

            if State.is_running_focus_side_bar:
                return

            else:
                State.is_running_focus_side_bar = True
                settings = sublime.load_settings( 'Preferences.sublime-settings' )
                preview_on_click = settings.get( 'preview_on_click' )

                if preview_on_click:
                    State.preview_on_click = preview_on_click
                    settings.set( 'preview_on_click', False )

                window.run_command( 'focus_side_bar' )
                window.run_command( 'move', { "by": "lines", "forward": False } )
                window.run_command( 'move', { "by": "lines", "forward": True } )

                # https://github.com/SublimeTextIssues/Core/issues/1265
                sublime.set_timeout( lambda: window.run_command( 'focus_side_bar_bug_fixer' ), 100 )

    def set_state(self):

        if State.is_running_focus_side_bar:
            State.is_running_focus_side_bar = False
            return True

        else:
            State.is_running_focus_side_bar = True

    # Uncommented this after this bug is fixed
    # https://github.com/SublimeTextIssues/Core/issues/2198
    #
    # def on_window_command(self, window, command_name, args):
    #     print('window command_name', command_name, args)

    # def on_text_command(self, view, command_name, args):
    #     print('view command_name', command_name, args)

    #     if command_name in g_toggle_comands:
    #         if self.set_state():
    #             return

    #         return ('fixed_toggle_find_panel', { "command": command_name })


class FocusSideBarBugFixerCommand(sublime_plugin.WindowCommand):
    """ Confusing "jumps" in Side Bar keyboard navigation
    https://github.com/SublimeTextIssues/Core/issues/1265
    """
    def run(self):
        # print('Running fix...')
        window = self.window
        window.run_command( 'move', { "by": "lines", "forward": False } )
        window.run_command( 'move', { "by": "lines", "forward": True } )
        window.run_command( 'focus_side_bar' )

        if State.preview_on_click:
            settings = sublime.load_settings( 'Preferences.sublime-settings' )
            settings.set( 'preview_on_click', True )

        State.preview_on_click = False
        State.is_running_focus_side_bar = False


# https://github.com/SublimeTextIssues/Core/issues/2914
class FixedToggleFindPanelCommand(sublime_plugin.WindowCommand):

    def run(self, command, args={}, skip=False):
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

        if not skip:
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


if sys.platform.startswith( 'linux' ):
    g_view_selections = {}

    # https://github.com/SublimeTextIssues/Core/issues/1022
    class SelectionData(object):
        def __init__(self):
            self.do_not_save = False
            self.selections = []

    def SelectionState(view=None):
        view = view or sublime.active_window().active_view()
        return g_view_selections.setdefault( view.id(), SelectionData() )

    class SelectionFixListener(sublime_plugin.EventListener):
        last_view = None

        def on_text_command(self, view, command_name, args):
            # print('command_name', command_name, args)

            # https://github.com/SublimeTextIssues/Core/issues/2198
            if command_name == 'show_overlay':
                SelectionState( view ).do_not_save = True

                # print( 'on_text_command do_not_save', SelectionState( view ).do_not_save )
                # show_overlay {"overlay": "goto", "text": ":"}
                # if 'overlay' in args and args['overlay'] == 'goto':
                #     SelectionState( view ).do_not_save = True

        def on_activated(self, view):
            state = SelectionState( view )
            last_view = self.last_view

            if last_view and view.settings().get('is_widget'):
                SelectionState( last_view ).do_not_save = True

            # print( 'on_activated do_not_save', SelectionState( view ).do_not_save )
            if state.do_not_save:
                state.do_not_save = False

            else:
                selections = view.sel()
                selections.clear()
                selections.add_all( state.selections )

        def on_deactivated(self, view):
            self.last_view = view
            state = SelectionState( view )

            selections = view.sel()
            state.selections = [selection for selection in selections]

