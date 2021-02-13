from functools import lru_cache
from .utils import search_paper, \
    search_cited_papers, \
    get_title_from_scholarly_pub, \
    download_arxiv_paper, \
    find_within_reference, \
    get_arxiv_id
import sys


class Search:
    def __init__(
            self,
            paper_title,
            feel_lucky: bool = True):
        """
        Instantiate a related work description search.
        """
        self.query_title = paper_title

    def search(self):
        self.pub = search_paper(self.query_title)
        print(f'Query: {self.query_title}')
        self.paper_title = get_title_from_scholarly_pub(self.pub)
        print(f'Find paper: {self.paper_title}')
        self.cited_papers = search_cited_papers(self.pub)
        print('Go though citedBy papers:')
        for i, paper in enumerate(self.cited_papers):
            paper_title = get_title_from_scholarly_pub(paper)
            print(f'{i}: ', paper_title)
            arxiv_id = get_arxiv_id(paper_title)
            tex_source_path = download_arxiv_paper(arxiv_id)

            mentioned_sentences = find_within_reference(
                tex_source_path,
                self.paper_title,
            )
            if len(mentioned_sentences) == 0:
                print('No mention. : (')
            else:
                for sent in mentioned_sentences:
                    print(sent)
            
            print()


def main():
    paper_title = sys.argv[1]
    Search(paper_title).search()