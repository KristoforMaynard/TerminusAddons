# in your User settings, it's useful to specify:
# > "origami_auto_close_empty_panes": true,
#
# There are some associated entries in
# > Default (OSX).sublime-keymap
# > Default (Linux).sublime-keymap
# > Default.sublime-commands
#
# cmd+alt+w, next pane?
# cmd+alt+shift+w, prev pane?

import os
import subprocess
import sys
import time

import sublime
import sublime_plugin


is_windows = sys.platform.startswith("win")


interp_lookup = {'python': 'python',
                 'perl': 'perl',
                 'bash': 'bash',
                 'ruby': 'ruby',
                 'lua': 'lua',
                 'julia': 'julia',
                 'make': 'make'
                }
ext_lookup = {'.py': '<python> "{filename}"',
              '.pl': '<perl> "{filename}"',
              '.sh': '<bash> "{filename}"',
              '.rb': '<ruby> "{filename}"',
              '.lua': '<lua> "{filename}"',
              '.jl': '<julia> "{filename}"',
              '.bat': '"{filename}"',
              '.exe': '"{filename}"',
             }


def import_companions():
    try:
        import Terminus
    except ImportError:
        Terminus = None

    try:
        from Origami import origami
    except ImportError:
        origami = None

    return Terminus, origami


class NotATerminal(TypeError):
    pass


def _emit_no_origami_msg():
    sublime.error_message("The Origami plugin must be installed to "
                          "split-open a terminal window")

def argmax(seq):
    return max(enumerate(seq), key=lambda x: x[1])[0]

def argmin(seq):
    return min(enumerate(seq), key=lambda x: x[1])[0]


class SplitOpenTerminus(sublime_plugin.WindowCommand):
    def run(self, direction="down", always_split=False, split_fraction=0.35,
            use_available=False, **kwargs):
        window = self.window

        direction = direction.strip().lower()
        if direction not in ('up', 'down', 'left', 'right'):
            raise ValueError("bad direction: {0}".format(direction))

        if 'working_dir' in kwargs:
            kwargs['cwd'] = kwargs.pop('working_dir')

        if 'config_name' not in kwargs:
            kwargs['config_name'] = 'Default'

        Terminus, origami = import_companions()

        if Terminus is None:
            sublime.error_message("split-open terminal requires the "
                                  "Terminus plugin")
            return

        if origami is None:
            window.run_command("terminus_open", args=kwargs)
            _emit_no_origami_msg()
        else:
            cells = window.get_layout()['cells']
            rows = window.get_layout()['rows']
            cols = window.get_layout()['cols']
            current_cell = cells[window.active_group()]

            # iaxis = {'left': 0, 'right': 0, 'up': 1, 'down': 1}[direction]
            # idir = {'left': 0, 'up': 1, 'right': 2, 'down': 3}[direction]

            adjacent_cells = origami.cells_adjacent_to_cell_in_direction(cells,
                                                                         current_cell,
                                                                         direction)
            lone_in_direction = not bool(adjacent_cells)

            if direction == 'down':
                extreme_group = [tup[3] for tup in cells].index(argmax(rows))
            elif direction == 'up':
                extreme_group = [tup[1] for tup in cells].index(argmin(rows))
            elif direction == 'left':
                extreme_group = [tup[0] for tup in cells].index(argmin(cols))
            elif direction == 'right':
                extreme_group = [tup[2] for tup in cells].index(argmax(cols))

            extreme_group_views = window.views_in_group(extreme_group)
            extreme_group_has_views = bool(extreme_group_views)
            extreme_group_has_terminal = any(view.settings().get('terminus_view', False)
                                             for view in extreme_group_views)
            # print("cells:", cells)
            # print("current_cell:", current_cell)
            # print("rows:", rows)
            # print("cols:", cols)
            # print("Lone in direction?", lone_in_direction)
            # print("Extreme Group", extreme_group)
            # print("extreme_group_has_views", extreme_group_has_views)
            # print("adjacent_cells", adjacent_cells)

            # this logic is becoming silly...
            available_view = None

            if use_available:
                groups_to_check = list(range(window.num_groups()))
                groups_to_check.pop(extreme_group)
                groups_to_check.insert(0, extreme_group)

                for group in groups_to_check:
                    try:
                        active_view = window.active_view_in_group(group)
                        if view_is_available_terminal(active_view):
                            available_view = active_view
                            break
                    except NotATerminal:
                        pass

            if available_view is not None:
                window.focus_view(available_view)
                window.run_command("terminus_keypress",
                                   args={"key": "u", "ctrl": True})

                for hook in kwargs.pop('post_window_hooks', []):
                    print("window running...", hook)
                    window.run_command(*hook)

                for hook in kwargs.pop('post_view_hooks', []):
                    print("view running...", hook)
                    available_view.run_command(*hook)
            else:
                if always_split:
                    do_split, start_from = True, extreme_group
                elif lone_in_direction and not extreme_group_has_views:
                    do_split, start_from = True, extreme_group
                elif extreme_group_has_terminal:
                    do_split, start_from = False, extreme_group
                elif not extreme_group_has_views:
                    do_split, start_from = False, extreme_group
                else:
                    do_split, start_from = True, extreme_group

                window.focus_group(start_from)
                if do_split:
                    window.run_command("create_pane", args={"direction": direction,
                                                            "give_focus": True})
                    window.run_command("zoom_pane", args={"fraction": split_fraction})

                window.run_command("terminus_open", args=kwargs)

def make_cmd(window, filename=None, logout_on_finished=False):
    v = window.extract_variables()
    platform = v['platform'].strip().lower()
    if filename is None:
        filename = v['file']

    if logout_on_finished:
        if is_windows:
            next_cmd = ' & exit'
        else:
            next_cmd = ' && exit'
    else:
        next_cmd = ''

    root, ext = os.path.splitext(os.path.basename(filename))
    ext = ext.strip().lower()

    if ext in ext_lookup:
        cmd = ext_lookup[ext].format(filename=filename)
    elif (root.strip().lower(), ext) == ('makefile', ''):
        cmd = '<make>'
    else:
        # sublime.error_message("Not sure how to run: {0}".format(filename))
        cmd = ''

    if cmd.startswith('<'):
        stop = cmd.find('>')
        try:
            interp = interp_lookup[cmd[1:stop]]
        except KeyError:
            interp = cmd[1:stop]
        cmd = interp + cmd[stop + 1:]

    if is_windows:
        if not cmd:
            raise ValueError("TerminusAddon: I don't know how to start '{0}'"
                             "on Windows".format(filename))
        # if wrap_bash:
        #     print("TerminusAddon: Can't wrap commands in bash on windows!")
    else:
        if not cmd:
            if os.access(filename, os.X_OK):
                cmd = '"{filename}"'.format(filename=filename)
            else:
                raise ValueError("TerminusAddon: I don't know how to start '{0}'"
                                 "on *nix".format(filename))

        # if wrap_bash:
        #     cmd = "bash -lc '{0}'{1}".format(cmd, next_cmd)

    cmd += next_cmd

    return cmd


def _pid_tty_of_view(view):
    Terminus, _ = import_companions()
    term = Terminus.terminus.terminal.Terminal.from_id(view.id())
    if not term:
        term_pid = None
        tty = None
    else:
        term_pid = str(term.process.pid)
        if is_windows:
            tty = None
        else:
            tty = subprocess.check_output(['ps', '-p', term_pid, '-o', 'tt']
                                          ).decode().splitlines()[1].strip()
    return term_pid, tty

def _pids_stats_in_tty(term_pid, tty):
    if is_windows:
        info = subprocess.check_output(['wmic', 'process', 'where',
                                        'ParentProcessId=' + term_pid, 'get',
                                        'Name,ProcessId,Status']
                                        ).decode().splitlines()[1:]
        info = [s.strip() for s in info]
        child_pids = [s.split()[1].strip() for s in info]
        child_stats = [s.split()[2].strip() if len(s.split()) > 2 else ''
                       for s in info]
    else:
        info = subprocess.check_output(['ps', '-t', tty, '-o', 'pid', '-o', 'stat',
                                        '-o', 'command']).decode().splitlines()[1:]
        info = [s.strip() for s in info if not s.strip().startswith(term_pid)]
        child_pids = [s.split()[0].strip() for s in info]
        child_stats = [s.split()[1].strip() for s in info]

    return child_pids, child_stats

def view_is_available_terminal(view):
    term_pid, tty = _pid_tty_of_view(view)
    if term_pid is None or tty is None:
        raise NotATerminal("view is not a terminal")
    child_pids, child_stats = _pids_stats_in_tty(term_pid, tty)

    if is_windows:
        return bool(child_pids)
    else:
        return not any(s.endswith('+') for s in child_stats)


class RunInTerminus(sublime_plugin.WindowCommand):
    def run(self, target_file=None, split_view=False, logout_on_finished=False,
            use_available=True, **kwargs):

        if split_view:
            term_open_cmd = "split_open_terminus"
        else:
            term_open_cmd = "terminus_open"

        cmd = make_cmd(self.window, filename=target_file,
                       logout_on_finished=logout_on_finished)
        kwargs['use_available'] = use_available
        self.window.run_command(term_open_cmd, args=kwargs)
        sublime.set_timeout(lambda:self.window.run_command('terminus_send_string',
                                                           {'string': cmd + '\n'}))
