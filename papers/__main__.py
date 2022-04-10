from aku import Aku

from papers.paper import render_html

aku = Aku()

aku.option(render_html)

aku.run()
