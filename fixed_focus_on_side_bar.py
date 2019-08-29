import sublime
import sublime_plugin


class State(object):
    preview_on_click = False
    is_running_focus_side_bar = False


class FocusOnSideBarListener(sublime_plugin.EventListener):

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
