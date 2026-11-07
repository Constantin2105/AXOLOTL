"""Tiny HTML tree for tests (stdlib only)."""
import re
import subprocess
from html.parser import HTMLParser

from conftest import ROOT

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find_all(self, tag=None, cls=None, **attrs):
        for n in self.iter():
            if tag and n.tag != tag:
                continue
            if cls and cls not in n.classes:
                continue
            if any(n.attrs.get(k.replace("_", "-")) != v for k, v in attrs.items()):
                continue
            yield n

    def find(self, *a, **kw):
        return next(self.find_all(*a, **kw), None)

    def texts(self):
        """Text nodes below this node, script/style excluded."""
        for c in self.children:
            if isinstance(c, str):
                yield c
            elif c.tag not in ("script", "style"):
                yield from c.texts()

    def text(self):
        return norm(" ".join(self.texts()))


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def norm(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ").replace(" ", " ")).strip()


def parse(html):
    b = _Builder()
    b.feed(html)
    return b.root


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def old(name):
    """The file as it was before the redesign."""
    return subprocess.run(["git", "show", f"7cd33dd:{name}"], cwd=ROOT, capture_output=True,
                          check=True).stdout.decode("utf-8")
