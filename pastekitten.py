import sublime, sublime_plugin
import urllib, urllib2, threading, re
import webbrowser


class PastekittenBaseCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    sels = self.view.sel()
    paste = ""
    for sel in sels:
      paste += self.view.substr(sel)
    threads = []

    syntax = self.view.syntax_name(sel.a).split('.')[-1].strip()

    thread = PastekittenApiCall(paste, syntax, 5)
    threads.append(thread)
    thread.start()

    edit = self.view.begin_edit('pastekitten')
    self.handle_threads(edit, threads)

  def handle_threads(self, edit, threads, i=0, dir=1):
    next_threads = []
    for thread in threads:
      if thread.is_alive():
        next_threads.append(thread)
        continue
      if thread.result == False:
        continue
      self.result_handler(edit, thread)
    threads = next_threads

    if len(threads):
      # This animates a little activity indicator in the status area
      before = i % 8
      after = (7) - before
      if not after:
        dir = -1
      if not before:
        dir = 1
      i += dir
      self.view.set_status('pastekitten', 'Pastekitten [%s=%s]' % \
          (' ' * before, ' ' * after))

      sublime.set_timeout(lambda: self.handle_threads(edit, threads,
          i, dir), 100)
      return

    self.view.end_edit(edit)

    self.view.erase_status('pastekitten')
    sublime.status_message('Pastekitten: Purrr purr')

  def result_handler(self, edit, thread):
    self.view.end_edit(edit)
    raise NotImplementedError("Subclasses should implement this!")

    return

class PastekittenApiCall(threading.Thread):
  def __init__(self, paste, syntax, timeout):
      self.paste = paste
      self.syntax = syntax
      self.timeout = timeout
      self.result = None
      threading.Thread.__init__(self)

  def run(self):
      try:
        data = urllib.urlencode({'contents': self.paste, 'syntax': self.syntax })
        request = urllib2.Request('http://pastekitten.com/', data,
            headers={"User-Agent": "Sublime Pastekitten"})
        http_file = urllib2.urlopen(request, timeout=self.timeout)
        self.result = http_file.geturl()
        return

      except (urllib2.HTTPError) as (e):
        err = '%s: HTTP errrror %s contacting API' % (__name__, str(e.code))
      except (urllib2.URLError) as (e):
        err = '%s: URRRL errrrror %s contacting API' % (__name__, str(e.reason))

      sublime.error_message(err)
      self.result = False


class PastekittenToClipboardCommand(PastekittenBaseCommand):
  def result_handler(self, edit, thread):
    result = thread.result
    sublime.set_clipboard(result)
    return

class PastekittenToBrowserCommand(PastekittenBaseCommand):
  def result_handler(self, edit, thread):
    result = thread.result
    webbrowser.open(result)
    return
