#!/usr/bin/python3

import argparse
import flask
import json
import logging


HTML_HEADER = """<!DOCTYPE html>
<html>
<head>
<link rel="icon" href="data:,">
<style>
body {
    font-size: 12pt;
    font-family: sans-serif;
}

.header {
    font-size: 16pt;
    padding: 1ex;
    margin-bottom: 2ex;
    background-color: #ccc;
    font-weight: bold;
}

a.button {
    -webkit-appearance: button;
    -moz-appearance: button;
    appearance: button;
    text-decoration: none;
    color: initial;
    padding: .5ex;
}

th {
   font-size: 18pt;
}

td {
   font-size: 16pt;
   padding: .5ex;
}

table {
    border:none;
    border-collapse: collapse;
}

tr:nth-child(even) {background: #eee}
tr:nth-child(odd) {background: #fff}

</style>
</head>
<body>
<div class=header>
Go/Links Lite
<a class="button" href="/links">List Links</a>
<a class="button" href="/edit/">Create Link</a>
<a class="button" href="/about">About</a>
{{ title }}
</div>
"""

HTML_FOOTER = """
</body>
</html>
"""

HTML_EDIT = """
<form action="/save" method="post">

<p>
Shortened link: go/
<input type="text" id="tag" name="tag" value="{{ tag }}" {% if tag %}readonly{% endif %}>
</p>
<p>
Original link:
<input type="text" id="url" name="url" value="{{ url }}">
</p>
{% if viewcount >= 0 %}
View Count: {{ viewcount }}
{% endif %}

<h2>Confirmation</h2>
<button type="submit" name="action" value="save">Save</button>
<button type="submit" name="action" value="delete">Delete</button>
</form>

"""


HTML_LIST = """
<table>
<thead>
<tr>
<th>url</th>
<th>original</th>
<th>views</th>
<th>&nbsp;</th>
</tr>
</thead>
<tbody>
{% for link in links %}
<tr>
<td><a href="/{{ link.tag }}" target="_blank" >go/{{ link.tag }}</a></td>
<td><a href="/{{ link.tag }}" target="_blank" >{{ link.url }}</a></td>
<td align="right">{{ link.viewcount }}</td>
<td><a href="/edit/{{ link.tag }}"><i class="material-icons">edit</i></a></td>
</tr>
{% endfor %}
</tbody>
</table>
"""

HTML_ABOUT = """
<div class=about>
<pre>
(c) 2019 Robert Muth

Go-Links-Lite is a simple URL shortener modelled after similar internal tools 
used by many "tech companies".

It does not use authentication and all links are shared and editable by 
everybody. The backend consists of a json text file.

It is usually configured to run on port 80 on a machine which is known by the 
name "go", so that http://go/TAG or simply go/TAG can be used to abbreviate a 
link.
</pre>

<a href="https://medium.com/@golinks/the-full-history-of-go-links-and-the-golink-system-cbc6d2c8bb3">
History of Go Links</a>


</div>
"""

app = flask.Flask(__name__)
logger = app.logger
LINK_DB = None


class Link:
    def __init__(self, tag, url, viewcount=0):
        # go/<tag> will redirect to <url>
        self.tag = tag
        self.url = url
        self.viewcount = viewcount

    def to_dict(self):
        return {
            "tag": self.tag,
            "url": self.url,
            "viewcount": self.viewcount,
        }


class LinkDb:
    """Simple db backed by a file with json contents"""

    def __init__(self, filename, dirty_threshold=5):
        self._filename = filename
        self._links = {}
        self._dirty_count = 0
        self._dirty_threshold = dirty_threshold
        try:
            self.Reload()
        except Exception as e:
            logger.error("problem loading db %s", e)

    def IncDirty(self):
        self._dirty_count += 1
        if self._dirty_count > self._dirty_threshold:
            self.Save()

    def Reload(self):
        logger.info("loading db from %s", self._filename)
        with open(self._filename, "r") as f:
            links = json.loads(f.read())
            self._links = {}
            for l in links:
                link = Link(**l)
                # app.logger.debug("dict %s", l)
                # app.logger.debug("obj dict %s", link.__dict__)
                self._links[link.tag] = link
        logger.info("loaded %d records", self.Size())

    def Save(self):
        self._dirty_count = 0
        with open(self._filename, "w") as f:
            f.write(json.dumps([v.to_dict() for v in self._links.values()]))

    def Size(self):
        return len(self._links)

    def GetLink(self, tag):
        link = self._links.get(tag)
        if link:
            link.viewcount += 1
            self.IncDirty()
        else:
            logger.error("link not found for: %s [%s]", tag, self._links)
        return link

    def AddLink(self, tag, url):
        link = Link(tag.strip(), url, 0)
        self._links[link.tag] = link
        return link

    def GetAllLinks(self, filter_tag):
        return self._links.values()

    def Delete(self, tag):
        if tag in self._links:
            app.logger.debug("deleting %s", tag)
            del self._links[tag]
            self.Save()


@app.route('/')
def top():
    return flask.redirect("/links")


@app.route('/about')
def about():
    context = {
        "title": "About",
    }
    return flask.render_template_string(HTML_HEADER + HTML_ABOUT + HTML_FOOTER, **context)


@app.route('/links')
@app.route('/links/<string:tag_filter>')
def links(tag_filter=None):
    global LINK_DB
    context = {
        "title": "List Links",
        "links": LINK_DB.GetAllLinks(tag_filter),
    }
    return flask.render_template_string(HTML_HEADER + HTML_LIST + HTML_FOOTER, **context)


@app.route('/save',  methods=['POST'])
def save(tag=None):
    global LINK_DB
    form = flask.request.form
    app.logger.debug(form)
    if form['action'] == "save":
        link = LINK_DB.AddLink(form["tag"], form["url"])
        LINK_DB.Save()
        return flask.redirect("/edit/" + link.tag)
    elif form['action'] == "delete":
        LINK_DB.Delete(form["tag"])
        return flask.redirect("/links")


@app.route('/edit/')
@app.route('/edit/<string:tag>')
def edit(tag=None):
    context = {
        "viewcount": 0,
    }
    if tag:
        context["title"] = "Edit Link"
        context["tag"] = tag
        link = LINK_DB.GetLink(tag)
        if link:
            context["url"] = link.url
    else:
        context["title"] = "Create Link"
    return flask.render_template_string(HTML_HEADER + HTML_EDIT + HTML_FOOTER, **context)


@app.route('/<string:tag>')
def redir(tag):
    global LINK_DB
    logger.info("link access for %s", tag)
    link = LINK_DB.GetLink(tag)
    if link:
        return flask.redirect(link.url)
    return flask.redirect("/edit/" + tag)


def main():
    global LINK_DB
    parser = argparse.ArgumentParser(description=__name__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port",  type=int, default=80)
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument("--dbfile", default="db.json")
    args = parser.parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(level)
    LINK_DB = LinkDb(args.dbfile)
    app.run(host=args.host, debug=True, port=args.port)


if __name__ == '__main__':
    main()
