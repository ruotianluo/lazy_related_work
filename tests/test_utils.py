import pytest
from lazy_related_work.utils import \
    download_arxiv_paper, \
    get_arxiv_id, \
    find_within_reference
import time
from unittest import mock


def test_get_arxiv_id():
    arxiv_id = get_arxiv_id('mask rcnn')
    print(arxiv_id)
    assert arxiv_id == '1703.06870v3'


def test_download_paper(tmpdir):
    with mock.patch('lazy_related_work.utils.paper_download_dir', str(tmpdir)):
        start = time.time()
        print(download_arxiv_paper('1703.06870v3'))
        print(time.time() - start)
        start = time.time()
        print(download_arxiv_paper('1703.06870v3'))
        print(time.time() - start)


# def test_find_within_reference():
#     import pudb;pu.db
#     # find_within_reference('papers/1711.05535v3.UNTITLED', 'Learning two-branch neural networks for image-text matching tasks')
#     find_within_reference('papers/1804.05113v3.UNTITLED', 'Learning two-branch neural networks for image-text matching tasks')