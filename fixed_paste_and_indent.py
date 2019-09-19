import sublime
import sublime_plugin

from sublime import Region

REGION_NAME = "fixed_paste_and_indent"
MAXIMUM_CLIPBOARD_SIZE = 10000


# I am saving the state in this class because it is a royal pain in the ass
# to keep typing `global` every time/everywhere I would like to use a global!
class State(object):
    copied_lines = []
    extra_command = ""
    has_new_regions = False
    clear_selections = False


def copy_with_empty_selection(view):
    return view.settings().get( 'copy_with_empty_selection' ) and not view.has_non_empty_selection_region()


# https://github.com/SublimeTextIssues/Core/issues/1635
class FixPasteAndIndendCommandsListener(sublime_plugin.EventListener):

    def on_text_command(self, view, command_name, args):
        # print('view command_name', command_name, args)

        if command_name == 'cut':

            if State.extra_command:
                State.extra_command = ""

            elif copy_with_empty_selection( view ):
                selections = view.sel()
                lines = []

                for selection in selections:
                    full_line = view.full_line( selection )
                    lines.append( full_line )

                State.selections_to_add = lines
                view.run_command( 'fix_paste_and_indend_helpder' )

                # State.extra_command = 'cut'
                # sublime.set_timeout( lambda: view.run_command( 'fix_paste_and_indend_helpder' ), 0 )
                # return ("nope", None)

        elif command_name == 'copy':

            if copy_with_empty_selection( view ) and not State.extra_command:
                selections = view.sel()
                lines = []

                for selection in selections:
                    State.copied_lines.append( selection )

                    full_line = view.full_line( selection )
                    lines.append( full_line )

                State.selections_to_add = lines
                view.run_command( 'fix_paste_and_indend_helpder' )

                # State.extra_command = 'copy'
                # sublime.set_timeout( lambda: view.run_command( 'fix_paste_and_indend_helpder' ), 0 )
                # return ("nope", None)

        elif command_name == 'paste':

            if copy_with_empty_selection( view ) and not State.extra_command:
                clipboard = sublime.get_clipboard( MAXIMUM_CLIPBOARD_SIZE )

                if clipboard and len( clipboard ) < MAXIMUM_CLIPBOARD_SIZE:

                    if clipboard[-1] == '\n':
                        fixed_selections = []

                        # https://github.com/SublimeTextIssues/Core/issues/2963#issuecomment-526913207
                        selections = view.sel()
                        view.add_regions( REGION_NAME, [ selection for selection in selections ] )

                        for selection in selections:
                            full_line = view.line( selection )
                            begin = full_line.begin()
                            fixed_selections.append( Region( begin, begin ) )

                        State.has_new_regions = True
                        State.clear_selections = True

                        State.selections_to_add = fixed_selections
                        view.run_command( 'fix_paste_and_indend_helpder' )

                        # State.extra_command = 'paste'
                        # sublime.set_timeout( lambda: view.run_command( 'fix_paste_and_indend_helpder' ), 0 )
                        # return ("nope", None)

    def on_post_text_command(self, view, command_name, args):
        # print( 'command_name', command_name, args )

        if command_name == 'copy' and State.copied_lines:
            State.extra_command = ""

            selections = view.sel()
            selections.clear()

            selections.add_all( State.copied_lines )
            State.copied_lines.clear()

            # State.clear_selections = True
            # State.selections_to_add = State.copied_lines

            # sublime.set_timeout( lambda: view.run_command( 'fix_paste_and_indend_helpder' ), 0 )
            # view.run_command( 'fix_paste_and_indend_helpder' )

        elif command_name == 'paste' and State.has_new_regions:
            State.extra_command = ""
            State.has_new_regions = False

            fixed_selections = view.get_regions( REGION_NAME )
            selections = view.sel()

            selections.clear()
            selections.add_all( fixed_selections )

            fixed_selections.clear()
            view.erase_regions( REGION_NAME )

            # State.clear_selections = True
            # State.selections_to_add = fixed_selections

            # sublime.set_timeout( lambda: view.run_command( 'fix_paste_and_indend_helpder' ), 0 )
            # view.run_command( 'fix_paste_and_indend_helpder' )


# https://github.com/SublimeTextIssues/Core/issues/2924
class FixPasteAndIndendHelpderCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        selections = view.sel()

        if State.clear_selections:
            State.clear_selections = False
            selections.clear()

        selections.add_all( State.selections_to_add )
        State.selections_to_add.clear()

        # https://github.com/SublimeTextIssues/Core/issues/2400
        # sublime.set_timeout( lambda: view.window().run_command( State.extra_command ), 0 )


class CutWithoutNewlineCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view

        if copy_with_empty_selection( view ):
            selections = view.sel()
            lines = []

            for selection in selections:
                full_line = view.line( selection )
                lines.append( full_line )

            selections.add_all( lines )

        view.run_command( 'cut' )


class CopyWithoutNewlineCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        is_to_copy = copy_with_empty_selection( view )

        if is_to_copy:
            selections = view.sel()
            lines = []

            for selection in selections:
                State.copied_lines.append( selection )

                full_line = view.line( selection )
                lines.append( full_line )

            selections.add_all( lines )

        view.run_command( 'copy' )

        if is_to_copy:
            selections = view.sel()
            selections.clear()

            selections.add_all( State.copied_lines )
            State.copied_lines.clear()


