from lazy_related_work.search import Search

def test_search():
    search = Search('mask rcnn')
    search.search()