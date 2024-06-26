import json
from typing import List

from pydantic import BaseModel, Field


class LCBaseModel(BaseModel):
    class Config:  # noqa
        populate_by_name = True


class QuestionStats(LCBaseModel):
    acceptance_rate: str = Field(..., alias="acRate")
    total_accepted: int = Field(..., alias="totalAcceptedRaw")
    total_submitted: int = Field(..., alias="totalSubmissionRaw")


class CodeSnippet(LCBaseModel):
    lang: str
    lang_slug: str = Field(..., alias="langSlug")
    code: str


class Question(LCBaseModel):
    question_id: int = Field(..., alias="questionId")
    title: str
    difficulty: str
    stats: str
    content: str
    code_snippets: List[CodeSnippet] = Field(..., alias="codeSnippets")

    def get_stats(self) -> QuestionStats:
        return QuestionStats(**json.loads(self.stats))

    def get_python_snippet(self) -> CodeSnippet:
        for s in self.code_snippets:
            if s.lang_slug == "python3":
                # make the code valid
                s.code = s.code + "pass"
                return s
        raise ValueError("No python snippet found in this problem")


class Problem(LCBaseModel):
    question: Question
