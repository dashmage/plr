from string import Template
from textwrap import dedent

from bs4 import BeautifulSoup

from plr.models import Problem


def create_content(p: Problem) -> str:
    q = p.question
    snippet = q.get_python_snippet()
    task = BeautifulSoup(q.content, features="html.parser").get_text()

    template_raw = dedent(
        """
        \"\"\"
        $id. $title
        $diff

        $description
        \"\"\"


        $snippet

        """
    ).lstrip("\n")

    return Template(template_raw).substitute(
        id=q.question_id,
        title=q.title,
        diff=q.difficulty,
        snippet=snippet.code,
        description=task,
    )
