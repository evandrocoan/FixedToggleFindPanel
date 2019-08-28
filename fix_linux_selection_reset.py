import sys

import sublime
import sublime_plugin


if sys.platform.startswith( 'linux' ):
    g_view_selections = {}

    # https://github.com/SublimeTextIssues/Core/issues/1022
    class Settings(object):
        def __init__(self):
            self.do_not_save = False
            self.selections = []

    def State(view=None):
        view = view or sublime.active_window().active_view()
        return g_view_selections.setdefault( view.id(), Settings() )

    class SelectionFixListener(sublime_plugin.EventListener):
        last_view = None

        def on_text_command(self, view, command_name, args):
            # print('command_name', command_name, args)

            # https://github.com/SublimeTextIssues/Core/issues/2198
            if command_name == 'show_overlay':
                State( view ).do_not_save = True

                # print( 'on_text_command do_not_save', State( view ).do_not_save )
                # show_overlay {"overlay": "goto", "text": ":"}
                # if 'overlay' in args and args['overlay'] == 'goto':
                #     State( view ).do_not_save = True

        def on_activated(self, view):
            state = State( view )
            last_view = self.last_view

            if last_view and view.settings().get('is_widget'):
                State( last_view ).do_not_save = True

            # print( 'on_activated do_not_save', State( view ).do_not_save )
            if state.do_not_save:
                state.do_not_save = False

            else:
                state_selections = state.selections

                if state_selections:
                    selections = view.sel()
                    selections.add_all( state_selections )

        def on_deactivated(self, view):
            self.last_view = view
            state = State( view )

            selections = view.sel()
            state.selections = [selection for selection in selections]
