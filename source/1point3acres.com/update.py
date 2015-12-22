#!/usr/bin/env python2

TAGS = [365, 539]
FILENAME = "README.md"

import re
import httplib
import errno


def parse_file(f):
    header = []
    items = []

    for line in f:
        if line.startswith("- ["):
            break
        header.append(line)
        continue

    item = line
    for line in f:
        if line.startswith("- ["):
            items.append(item)
            item = line
            continue
        if line.strip().startswith("- ["):
            item += line
            continue
        assert False, "bad line '%s'" % line

    return header, {int(re.match(r'^- \[[ x]\][^[]+\[(\d+)\:', item).group(1)):item for item in items}


class Items(object):

    def __init__(self):
        self.files = {}
        self.changed = set()

    def _load_file(self, key):
        data = self.files.get(key, None)
        if data is None:
            try:
                with open("%03d.md" % (key,), 'r') as f:
                    data = parse_file(f)
                self.files[key] = data
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
                data = ([], {})
                
            self.files[key] = data
        return data

    def __setitem__(self, name, value):
        header, items = self._load_file(name/1000)
        if name in items:
            return
        items[name] = value
        self.changed.add(name/1000)

    def __contains__(self, name):
        header, items = self._load_file(name/1000)
        return name in items

    def save(self):
        for p in self.changed:
            header, items = self.files[p]

            l = items.items()
            l.sort()

            result = "".join(header)+"".join(v for _, v in l)
            with open("%03d.md" % (p,), 'w') as f:
                f.write(result)


def fetch(tag, page):
    print "start fetching tag %s page %s" % (tag, page)
    try:
        conn = httplib.HTTPConnection("instant.1point3acres.com")
        conn.set_debuglevel(9)
        conn.request("GET", "/tag/%d/threads?pg=%d" % (tag, page))
        response = conn.getresponse()
        if response.status != 200:
            return
        data = response.read()
        for match in re.finditer(r'<a href="/thread/(\d+)">([^<]+)</a>', data):
            print match.group(1), match.group(2)
            yield int(match.group(1)), "- [ ] [{0}: {1}](http://instant.1point3acres.com/thread/{0})\n".format(match.group(1), match.group(2))
    except httplib.HTTPException:
        return


def update_tag(items, tag):
    page = 1
    no_new_item = 0

    while True:
        count = 0
        for k, v in fetch(tag, page):
            if k in items:
                continue
            items[k] = v
            count += 1

        if count == 0:
            no_new_item += 1

        if no_new_item > 5:
            break

        page += 1


def main():
    items = Items()

    for tag in TAGS:
        update_tag(items, tag)

    items.save()


if __name__ == '__main__':
    main()
